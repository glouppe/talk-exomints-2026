"""Flow matching posterior estimation (FMPE) on the toy simulator, for comparison with NPE (toy_npe.py).

Same training pairs, same parameter scaling (unit box), same embedding network and noise on the fly as NPE.
The flow is continuous: a vector field v(θ_t, t, h(x)) trained by flow matching on straight paths
θ_t = (1 - (1 - σ_min) t) θ_0 + t θ_1, θ_0 ~ N(0, I), with t weighted towards 1 (Dax et al 2023).
Sampling integrates the ODE with RK4; the log-density is exact, by integrating the divergence along the path
(computed exactly, one backward pass per parameter).

    python tools/toy_fmpe.py train     # -> $TOY_OUT/fmpe.pt
    python tools/toy_fmpe.py observe   # samples on x_obs -> $TOY_OUT/fmpe_posterior.npz
    python tools/toy_fmpe.py is        # importance sampling with the FMPE proposal -> $TOY_OUT/fmpe_is.npz

Environment: TOY_OUT, EPOCHS, BATCH, ODE_STEPS, WIDTH, DROPOUT, WEIGHT_DECAY.
The validation loss is monitored and the best checkpoint is kept (the vector field memorizes the training pairs
without regularization: validation loss rose after ~5 epochs with width 512, no dropout).
"""

import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import toy_npe as N

OUT = N.OUT
SIGMA_MIN = 1e-4
ALPHA = 1.0  # time prior p(t) ∝ t^(1 / (1 + ALPHA)), as in Dax et al 2023
ODE_STEPS = int(os.environ.get("ODE_STEPS", 64))
WIDTH = int(os.environ.get("WIDTH", 512))
DROPOUT = float(os.environ.get("DROPOUT", 0.1))
WEIGHT_DECAY = float(os.environ.get("WEIGHT_DECAY", 1e-2))


def build():
    import torch
    import torch.nn as nn

    class Block(nn.Module):
        def __init__(self, d):
            super().__init__()
            self.net = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, d), nn.GELU(), nn.Dropout(DROPOUT), nn.Linear(d, d))

        def forward(self, z):
            return z + self.net(z)

    class FMPE(nn.Module):
        def __init__(self, n_x=94, n_theta=len(N.LO), n_emb=64, width=WIDTH, depth=4, n_freq=8):
            super().__init__()
            self.n_theta = n_theta
            self.embed = nn.Sequential(
                nn.Linear(n_x, 512), nn.ELU(), nn.Linear(512, 256), nn.ELU(),
                nn.Linear(256, 256), nn.ELU(), nn.Linear(256, n_emb))
            self.register_buffer("freq", torch.pi * 2.0 ** torch.arange(n_freq))
            self.inp = nn.Linear(n_theta + 2 * n_freq + n_emb, width)
            self.blocks = nn.Sequential(*[Block(width) for _ in range(depth)])
            self.out = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, n_theta))

        def h(self, x):
            return self.embed(N.preprocess(x))

        def v(self, theta_t, t, h):
            tf = t[:, None] * self.freq
            z = torch.cat([theta_t, torch.sin(tf), torch.cos(tf), h], dim=-1)
            return self.out(self.blocks(self.inp(z)))

        def loss(self, theta1, x):
            n = len(theta1)
            t = torch.rand(n, device=theta1.device) ** (1 / (1 + 1 / (1 + ALPHA)))  # p(t) ∝ t^(1/(1+α))
            theta0 = torch.randn_like(theta1)
            theta_t = (1 - (1 - SIGMA_MIN) * t[:, None]) * theta0 + t[:, None] * theta1
            target = theta1 - (1 - SIGMA_MIN) * theta0
            return ((self.v(theta_t, t, self.h(x)) - target) ** 2).sum(-1).mean()

        def _div(self, theta, t, h):
            """v and its exact divergence (sum of diagonal Jacobian terms, one backward pass per dimension)."""
            with torch.enable_grad():
                theta = theta.detach().requires_grad_(True)
                v = self.v(theta, t, h)
                div = torch.zeros(len(theta), device=theta.device)
                for k in range(self.n_theta):
                    div = div + torch.autograd.grad(v[:, k].sum(), theta, retain_graph=k < self.n_theta - 1)[0][:, k]
            return v.detach(), div.detach()

        def sample_and_log_prob(self, x, n, steps=ODE_STEPS, with_log_prob=True):
            """Integrate dθ/dt = v from t=0 to 1 (RK4). log q(θ_1) = log N(θ_0) - ∫ div v dt."""
            h = self.h(x[None]).expand(n, -1)
            theta = torch.randn(n, self.n_theta, device=x.device)
            logq = -0.5 * (theta ** 2).sum(-1) - 0.5 * self.n_theta * np.log(2 * np.pi)
            dt = 1.0 / steps
            for k in range(steps):
                t0 = torch.full((n,), k * dt, device=x.device)
                if with_log_prob:
                    f = lambda th, tt: self._div(th, tt, h)
                else:
                    f = lambda th, tt: (self.v(th, tt, h), torch.zeros(n, device=x.device))
                k1, d1 = f(theta, t0)
                k2, d2 = f(theta + 0.5 * dt * k1, t0 + 0.5 * dt)
                k3, d3 = f(theta + 0.5 * dt * k2, t0 + 0.5 * dt)
                k4, d4 = f(theta + dt * k3, t0 + dt)
                theta = theta + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
                logq = logq - dt / 6 * (d1 + 2 * d2 + 2 * d3 + d4)
            return theta, logq

    return FMPE()


def load(dev="cpu"):
    import torch
    model = build()
    model.load_state_dict(torch.load(OUT + "fmpe.pt", weights_only=False, map_location=dev)["state"])
    return model.to(dev).eval()


def train(epochs=int(os.environ.get("EPOCHS", 200)), batch=int(os.environ.get("BATCH", 1024)), lr=5e-4):
    import torch
    torch.manual_seed(0)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    theta, flux = N.load_pairs()
    th = torch.tensor(N.to_unit(theta), dtype=torch.float32, device=dev)
    f = torch.tensor(flux, dtype=torch.float32, device=dev)
    del theta, flux
    n = len(th)
    n_val = n // 20  # same split as NPE
    model = build().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    log, best = [], np.inf
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n - n_val, device=dev) + n_val
        losses = []
        for i in range(0, len(perm), batch):
            idx = perm[i:i + batch]
            x = f[idx] + N.SIGMA * torch.randn_like(f[idx])
            loss = model.loss(th[idx], x)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
        sched.step()
        model.eval()
        with torch.no_grad():
            torch.manual_seed(1)
            xv = f[:n_val] + N.SIGMA * torch.randn_like(f[:n_val])
            val = np.mean([model.loss(th[:n_val][j:j + 4096], xv[j:j + 4096]).item() for j in range(0, n_val, 4096)])
        log.append((float(np.mean(losses)), float(val)))
        print(f"epoch {ep:3d}  train {np.mean(losses):.4f}  valid {val:.4f}", flush=True)
        if val < best:  # early stopping: keep the best validation checkpoint (atomic write)
            best = val
            tmp = OUT + "fmpe.pt.tmp"
            torch.save({"state": {k: v.cpu() for k, v in model.state_dict().items()}, "log": log, "epoch": ep}, tmp)
            os.replace(tmp, OUT + "fmpe.pt")


def observe(n=20_000):
    import torch
    torch.manual_seed(0)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    x_obs = np.load(OUT + "posterior.npz")["x_obs"]
    model = load(dev)
    t0 = time.time()
    with torch.no_grad():
        u, _ = model.sample_and_log_prob(torch.tensor(x_obs, dtype=torch.float32, device=dev), n,
                                         with_log_prob=False)
    dt = time.time() - t0
    theta = N.from_unit(u.cpu().numpy())
    inside = np.all((theta >= N.LO) & (theta <= N.UP), axis=1)
    np.savez(OUT + "fmpe_posterior.npz", x_obs=x_obs, samples=theta[inside], seconds=dt)
    print(f"FMPE: {inside.sum()} samples in prior box (of {n}) in {dt:.2f} s on {dev}")


def isample(n=50_000, seed=3, chunk=5_000):
    """Importance sampling with the FMPE proposal: same weights and outputs as toy_npe.isample."""
    import torch
    torch.manual_seed(seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    x_obs = np.load(OUT + "posterior.npz")["x_obs"]
    model = load(dev)
    t0 = time.time()
    us, lqs = [], []
    xt = torch.tensor(x_obs, dtype=torch.float32, device=dev)
    for _ in range(n // chunk):
        u, lq = model.sample_and_log_prob(xt, chunk)
        us.append(u.cpu().double().numpy())
        lqs.append(lq.cpu().double().numpy())
    u, log_q_u = np.concatenate(us), np.concatenate(lqs)
    t_flow = time.time() - t0
    theta = N.from_unit(u)
    inside = np.all((theta >= N.LO) & (theta <= N.UP), axis=1)
    log_q = log_q_u + np.sum(np.log(2 / (N.UP - N.LO)))
    log_prior = -np.sum(np.log(N.UP - N.LO))
    log_lik = np.full(n, -np.inf)
    with Pool(len(os.sched_getaffinity(0)), initializer=N._ns_init, initargs=(x_obs,)) as pool:
        log_lik[inside] = pool.map(N._ns_loglike, list(theta[inside]), chunksize=200)
    log_w = log_lik + log_prior - log_q
    m = log_w.max()
    w = np.exp(log_w - m)
    eff = w.sum() ** 2 / (n * (w * w).sum())
    log_z = m + np.log(w.mean())
    logz_err = np.sqrt(np.var(w) / n) / np.mean(w)
    idx = np.random.default_rng(seed).choice(n, size=20_000, replace=True, p=w / w.sum())
    dt = time.time() - t0
    np.savez(OUT + "fmpe_is.npz", samples=theta[idx], efficiency=eff, logz=log_z, logz_err=logz_err,
             seconds=dt, seconds_flow=t_flow, n=n)
    print(f"FMPE IS: n={n}, efficiency={eff:.3f}, logZ={log_z:.2f} ± {logz_err:.3f}, {dt:.0f} s "
          f"(flow {t_flow:.0f} s)")


if __name__ == "__main__":
    {"train": train, "observe": observe, "is": isample}[sys.argv[1]]()
