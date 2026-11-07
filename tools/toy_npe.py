"""Neural posterior estimation on the toy simulator, end to end.

    python tools/toy_npe.py simulate [N]   # (θ, f(θ)) pairs from the prior -> .render/data/toy/pairs.npz
    python tools/toy_npe.py train          # NSF + MLP embedding, noise added on the fly -> .render/data/toy/npe.pt
    python tools/toy_npe.py observe        # benchmark x_obs, NPE samples -> .render/data/toy/posterior.npz
    python tools/toy_npe.py mcmc           # reference posterior with the exact Gaussian likelihood -> .render/data/toy/mcmc.npz
    python tools/toy_npe.py is             # importance sampling with the NPE proposal: posterior, efficiency, log Z
    python tools/toy_npe.py nested         # nested sampling (dynesty): posterior and log Z

Environment: TOY_OUT (output folder), TOY_MODEL (cloudy | clear), X_OBS (npz with x_obs, for observe).

Run with the venv in .render/venv (torch CPU, zuko). Simulation uses all cores.
"""

import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import toy_exo as T

OUT = os.environ.get("TOY_OUT", ".render/data/toy/")
SIGMA = T.SIGMA_NOISE * T.Simulator.scale

# Model: "cloudy" (default, 6 parameters) or "clear" (no cloud deck: log P_cloud fixed at the bottom, 5 parameters)
MODEL = os.environ.get("TOY_MODEL", "cloudy")
KEEP = [0, 1, 2, 3, 4, 5] if MODEL == "cloudy" else [0, 1, 2, 3, 5]
CLEAR_LOG_PC = 2.0
LO, UP = T.LOWER[KEEP], T.UPPER[KEEP]


def full(theta):
    """Model parameters -> the 6 simulator parameters."""
    theta = np.asarray(theta, dtype=float)
    if MODEL == "cloudy":
        return theta
    return np.insert(theta, 4, CLEAR_LOG_PC, axis=-1)


def _simulate_chunk(args):
    seed, n = args
    sim = T.Simulator(noisy=False, seed=seed)
    th = LO + (UP - LO) * sim.rng.random((n, len(LO)))
    f = np.array([sim.clean(full(t)) for t in th])
    return th, f


def simulate(n=100_000, chunk=2_000):
    os.makedirs(OUT, exist_ok=True)
    jobs = [(1000 + i, chunk) for i in range(n // chunk)]
    t0 = time.time()
    with Pool(len(os.sched_getaffinity(0))) as pool:  # the CPUs actually allocated (Slurm), not the node's
        res = pool.map(_simulate_chunk, jobs)
    th = np.concatenate([r[0] for r in res]).astype(np.float32)
    f = np.concatenate([r[1] for r in res]).astype(np.float32)
    ok = np.all(np.isfinite(f), axis=1)
    np.savez(OUT + "pairs.npz", theta=th[ok], f=f[ok])
    print(f"{ok.sum()} pairs in {time.time() - t0:.0f} s")


# ---------------------------------------------------------------- NPE

def preprocess(x):
    """Spectra span orders of magnitude: asinh in units of the noise level."""
    import torch
    return torch.asinh(x / SIGMA)


def build():
    import torch.nn as nn
    import zuko

    class NPE(nn.Module):
        def __init__(self, n_x=len(T.WL_OUT), n_theta=len(LO), n_emb=64):
            super().__init__()
            self.embed = nn.Sequential(
                nn.Linear(n_x, 512), nn.ELU(), nn.Linear(512, 256), nn.ELU(),
                nn.Linear(256, 256), nn.ELU(), nn.Linear(256, n_emb))
            hidden = [int(h) for h in os.environ.get("FLOW_HIDDEN", "256,256").split(",")]
            self.flow = zuko.flows.NSF(n_theta, n_emb, transforms=3, hidden_features=hidden)

        def forward(self, theta, x):
            return -self.flow(self.embed(preprocess(x))).log_prob(theta).mean()

        def sample(self, x, n):
            return self.flow(self.embed(preprocess(x))).sample((n,))

    return NPE()


def to_unit(theta):
    return 2 * (theta - LO) / (UP - LO) - 1


def from_unit(u):
    return LO + (u + 1) / 2 * (UP - LO)


def train(epochs=int(os.environ.get("EPOCHS", 60)), batch=int(os.environ.get("BATCH", 512)), lr=1e-3):
    import torch
    torch.manual_seed(0)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    d = np.load(OUT + "pairs.npz")
    th = torch.tensor(to_unit(d["theta"]), dtype=torch.float32, device=dev)
    f = torch.tensor(d["f"], dtype=torch.float32, device=dev)
    n = len(th)
    n_val = n // 20
    model = build().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    log = []
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n - n_val, device=dev) + n_val
        losses = []
        for i in range(0, len(perm), batch):
            idx = perm[i:i + batch]
            x = f[idx] + SIGMA * torch.randn_like(f[idx])  # noise on the fly
            loss = model(th[idx], x)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
        sched.step()
        model.eval()
        with torch.no_grad():
            g = torch.Generator(device=dev).manual_seed(1)
            xv = f[:n_val] + SIGMA * torch.randn(f[:n_val].shape, generator=g, device=dev)
            val = model(th[:n_val], xv).item()
        log.append((float(np.mean(losses)), float(val)))
        print(f"epoch {ep:3d}  train {np.mean(losses):.3f}  valid {val:.3f}", flush=True)
        if ep % 10 == 9 or ep == epochs - 1:  # checkpoint (atomic)
            tmp = OUT + "npe.pt.tmp"
            torch.save({"state": {k: v.cpu() for k, v in model.state_dict().items()}, "log": log}, tmp)
            os.replace(tmp, OUT + "npe.pt")


def observe(n=20_000, seed=7):
    import torch
    sim = T.Simulator(noisy=True, seed=seed)
    x_obs = np.load(os.environ["X_OBS"])["x_obs"] if "X_OBS" in os.environ else sim(T.THETA_STAR)
    model = build()
    model.load_state_dict(torch.load(OUT + "npe.pt", weights_only=False)["state"])
    model.eval()
    t0 = time.time()
    with torch.no_grad():
        u = model.sample(torch.tensor(x_obs, dtype=torch.float32), n).numpy()
    dt = time.time() - t0
    theta = from_unit(u)
    inside = np.all((theta >= LO) & (theta <= UP), axis=1)
    np.savez(OUT + "posterior.npz", x_obs=x_obs, theta_star=T.THETA_STAR, samples=theta[inside], seconds=dt)
    print(f"{inside.sum()} samples in {dt:.2f} s")


# ---------------------------------------------------------------- MCMC reference

def log_post(theta, x_obs, sim):
    if np.any(theta < LO) or np.any(theta > UP):
        return -np.inf
    r = (x_obs - sim.clean(full(theta))) / SIGMA
    return -0.5 * np.sum(r * r)


def _chain(args):
    seed, x_obs, n_steps, start = args
    rng = np.random.default_rng(seed)
    sim = T.Simulator(noisy=False)
    th = start.copy()
    lp = log_post(th, x_obs, sim)
    scale = 0.02 * (UP - LO)
    cov = np.diag(scale ** 2)
    out, acc = [], 0
    for k in range(n_steps):
        if k >= 2000 and k % 500 == 0:  # adapt the proposal from the chain so far
            cov = np.cov(np.array(out[1000:]).T) * 2.38 ** 2 / len(LO) + 1e-10 * np.eye(len(LO))
        prop = rng.multivariate_normal(th, cov)
        lq = log_post(prop, x_obs, sim)
        if np.log(rng.random()) < lq - lp:
            th, lp = prop, lq
            acc += 1
        out.append(th.copy())
    return np.array(out), acc / n_steps


def mcmc(n_chains=8, n_steps=20_000, burn=5_000):
    d = np.load(OUT + "posterior.npz")
    x_obs = d["x_obs"]
    starts = d["samples"][:n_chains]  # start from NPE draws, then forget them
    t0 = time.time()
    with Pool(n_chains) as pool:
        res = pool.map(_chain, [(i, x_obs, n_steps, starts[i]) for i in range(n_chains)])
    chains = np.stack([r[0] for r in res])
    print("acceptance", [round(r[1], 2) for r in res], f"{time.time() - t0:.0f} s")
    np.savez(OUT + "mcmc.npz", samples=chains[:, burn:].reshape(-1, len(LO)), chains=chains)


# ---------------------------------------------------------------- importance sampling

def isample(n=50_000, seed=3):
    """Reweight NPE samples with the exact (toy) likelihood: corrected posterior, efficiency, evidence.

    The likelihood is unnormalized (-0.5 r^2), as in the nested sampling run, so log Z values are comparable."""
    import torch
    torch.manual_seed(seed)
    x_obs = np.load(OUT + "posterior.npz")["x_obs"]
    model = build()
    model.load_state_dict(torch.load(OUT + "npe.pt", weights_only=False)["state"])
    model.eval()
    t0 = time.time()
    with torch.no_grad():
        d = model.flow(model.embed(preprocess(torch.tensor(x_obs, dtype=torch.float32))))
        u = d.sample((n,))
        log_q_u = d.log_prob(u).double().numpy()
    u = u.numpy().astype(np.float64)
    theta = from_unit(u)
    inside = np.all((theta >= LO) & (theta <= UP), axis=1)
    log_q = log_q_u + np.sum(np.log(2 / (UP - LO)))  # density of θ, not of the rescaled u
    log_prior = -np.sum(np.log(UP - LO))
    sim = T.Simulator(noisy=False)
    log_lik = np.full(n, -np.inf)
    with Pool(len(os.sched_getaffinity(0)), initializer=_ns_init, initargs=(x_obs,)) as pool:
        ll = pool.map(_ns_loglike, list(theta[inside]), chunksize=200)
    log_lik[inside] = ll
    log_w = log_lik + log_prior - log_q
    m = log_w.max()
    w = np.exp(log_w - m)
    eff = w.sum() ** 2 / (n * (w * w).sum())
    log_z = m + np.log(w.mean())
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=20_000, replace=True, p=w / w.sum())
    dt = time.time() - t0
    # Standard error of log Z from the weights (delta method)
    logz_err = np.sqrt(np.var(w) / n) / np.mean(w)
    np.savez(OUT + "is.npz", samples=theta[idx], efficiency=eff, logz=log_z, logz_err=logz_err, seconds=dt, n=n)
    print(f"IS: n={n}, efficiency={eff:.3f}, logZ={log_z:.2f} ± {logz_err:.3f}, {dt:.0f} s")


# ---------------------------------------------------------------- nested sampling reference

_NS_SIM = None
_NS_X = None


def _ns_init(x_obs):
    global _NS_SIM, _NS_X
    _NS_SIM, _NS_X = T.Simulator(noisy=False), x_obs


def _ns_loglike(theta):
    r = (_NS_X - _NS_SIM.clean(full(theta))) / SIGMA
    return -0.5 * float(np.sum(r * r))


def _ns_prior(u):
    return LO + u * (UP - LO)


def nested(nlive=500, n_cores=int(os.environ.get("NS_CORES", len(os.sched_getaffinity(0))))):
    import dynesty
    from dynesty import utils as dyfunc
    x_obs = np.load(os.environ["X_OBS"] if "X_OBS" in os.environ else OUT + "posterior.npz")["x_obs"]
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    with Pool(n_cores, initializer=_ns_init, initargs=(x_obs,)) as pool:
        sampler = dynesty.NestedSampler(_ns_loglike, _ns_prior, len(LO), nlive=nlive, pool=pool, queue_size=n_cores,
                                        rstate=np.random.default_rng(0))
        sampler.run_nested(dlogz=0.1, print_progress=False)
    res = sampler.results
    dt = time.time() - t0
    samples = res.samples_equal()
    np.savez(OUT + "nested.npz", samples=samples, seconds=dt, logz=res.logz[-1], ncall=int(np.sum(res.ncall)))
    print(f"nested sampling: {dt:.0f} s on {n_cores} cores, {int(np.sum(res.ncall))} likelihood calls, "
          f"logZ = {res.logz[-1]:.2f} ± {res.logzerr[-1]:.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "simulate":
        simulate(int(sys.argv[2]) if len(sys.argv) > 2 else 100_000)
    elif cmd == "train":
        train()
    elif cmd == "observe":
        observe()
    elif cmd == "mcmc":
        mcmc()
    elif cmd == "nested":
        nested()
    elif cmd == "is":
        isample()
