"""Truncated sequential NPE (TSNPE, Deistler et al. 2022) on the 30-parameter toy simulator (toy_exo30.py).

Round R: train the NPE on the pooled pairs of rounds 0..R (warm start from round R-1), then truncate the prior to
the 1 - ε highest-probability region of q(θ | x_obs) and draw the parameters of round R+1 from it. With ROUNDS=1 and
the whole budget in round 0, the same code is amortised NPE, the baseline.

    python tools/toy_tsnpe.py simulate R   # CPU: θ of round R (prior if R = 0, else theta-R.npz) -> pairs-R.npz;
                                           #      also the importance-sampling diagnostics of round R-1
    python tools/toy_tsnpe.py round R      # GPU: train npe-R.pt, draws for IS, proposal theta-(R+1).npz
    python tools/toy_tsnpe.py nested       # CPU: dynesty reference posterior with the exact likelihood
    python tools/toy_tsnpe.py report       # figures and table over the runs given in RUNS

Truncated proposal: p̃(θ) ∝ p(θ) 1[q(θ | x_obs) > τ], τ the ε-quantile of log q over samples of q. Sampled by SIR
(K candidates from q per draw, weights 1[θ in prior box, log q > τ] / q; the uniform prior cancels). The prior
volume kept, E_q[p 1[HPR] / q], is logged: rejection sampling from the prior would accept that fraction.

Environment: TOY_OUT, N0 (round-0 budget), N (per later round), ROUNDS, EPS (1e-4), K (SIR candidates, 256),
EPOCHS (max per round), PATIENCE, FLOW_TRANSFORMS (8), FLOW_PASSES (2: coupling), FLOW_HIDDEN, BATCH, SEED.
"""

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import toy_exo30 as T

OUT = os.environ.get("TOY_OUT", "/scratch/users/" + os.environ.get("USER", "") + "/exomints/t30/run/")
SIGMA = T.SIGMA_NOISE * T.Simulator.scale
LO, UP = T.LOWER, T.UPPER
D = len(LO)
SEED = int(os.environ.get("SEED", 0))
N0 = int(os.environ.get("N0", 200_000))
N = int(os.environ.get("N", 200_000))
ROUNDS = int(os.environ.get("ROUNDS", 5))
EPS = float(os.environ.get("EPS", 1e-4))
K = int(os.environ.get("K", 256))
N_IS = 50_000
LOG_UNIT_PRIOR = -D * np.log(2.0)  # uniform density on [-1, 1]^D


def to_unit(theta):
    return 2 * (theta - LO) / (UP - LO) - 1


def from_unit(u):
    return LO + (u + 1) / 2 * (UP - LO)


def x_obs():
    """The benchmark observation, made once (seed 7) and shared by every run."""
    path = os.path.join(os.path.dirname(OUT.rstrip("/")), "xobs.npz")
    if not os.path.exists(path):
        x = T.Simulator(noisy=True, seed=7)(T.THETA_STAR)
        tmp = path + f".{os.getpid()}.tmp.npz"  # unique: two runs may start at once (same content, seed 7)
        np.savez(tmp, x_obs=x, theta_star=T.THETA_STAR)
        os.replace(tmp, path)
    return np.load(path)["x_obs"]


def save_npz(path, **kw):
    tmp = path + ".tmp.npz"
    np.savez(tmp, **kw)
    with open(tmp, "rb") as fh:
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def log_summary(R, **kw):
    path = OUT + "summary.json"
    s = json.load(open(path)) if os.path.exists(path) else {}
    s.setdefault(str(R), {}).update(kw)
    tmp = path + ".tmp"
    json.dump(s, open(tmp, "w"), indent=1)
    os.replace(tmp, path)


# ---------------------------------------------------------------- simulation and likelihood (CPU)

_SIM, _X = None, None


def _init(x=None):
    global _SIM, _X
    _SIM, _X = T.Simulator(noisy=False), x


def _clean(theta):
    return _SIM.clean(theta)


def _loglike(theta):
    r = (_X - _SIM.clean(theta)) / SIGMA
    return -0.5 * float(np.sum(r * r))


def ncpu():
    return len(os.sched_getaffinity(0))


def simulate(R):
    os.makedirs(OUT, exist_ok=True)
    xo = x_obs()
    if R > 0 and os.path.exists(OUT + f"isdraws-{R - 1}.npz"):
        importance(R - 1, xo)
    if R >= ROUNDS:
        return
    if R == 0:
        rng = np.random.default_rng(1000 + SEED)
        theta = LO + (UP - LO) * rng.random((N0, D))
    else:
        theta = np.load(OUT + f"theta-{R}.npz")["theta"]
    t0 = time.time()
    with Pool(ncpu(), initializer=_init) as pool:
        f = np.array(pool.map(_clean, list(theta), chunksize=500))
    ok = np.all(np.isfinite(f), axis=1)
    save_npz(OUT + f"pairs-{R}.npz", theta=theta[ok].astype(np.float32), f=f[ok].astype(np.float32))
    print(f"round {R}: {ok.sum()} pairs in {time.time() - t0:.0f} s on {ncpu()} CPUs", flush=True)
    log_summary(R, n_sims=int(ok.sum()))


def importance(R, xo):
    """IS of q_R(θ | x_obs) against the exact posterior: efficiency, log Z, reweighted samples."""
    d = np.load(OUT + f"isdraws-{R}.npz")
    theta, log_q = d["theta"], d["log_q"]  # log_q: density of θ (not of u)
    inside = np.all((theta >= LO) & (theta <= UP), axis=1)
    t0 = time.time()
    log_lik = np.full(len(theta), -np.inf)
    with Pool(ncpu(), initializer=_init, initargs=(xo,)) as pool:
        log_lik[inside] = pool.map(_loglike, list(theta[inside]), chunksize=200)
    log_prior = -np.sum(np.log(UP - LO))
    log_w = log_lik + log_prior - log_q
    m = log_w.max()
    w = np.exp(log_w - m)
    eff = w.sum() ** 2 / (len(w) * (w * w).sum())
    log_z = m + np.log(w.mean())
    idx = np.random.default_rng(R).choice(len(w), size=20_000, p=w / w.sum())
    save_npz(OUT + f"is-{R}.npz", samples=theta[idx], efficiency=eff, logz=log_z, log_w=log_w)
    print(f"IS round {R}: efficiency {eff:.4f}, ESS {eff * len(w):.0f}, log Z {log_z:.2f}, "
          f"inside prior {inside.mean():.3f}, {time.time() - t0:.0f} s", flush=True)
    log_summary(R, is_efficiency=float(eff), is_ess=float(eff * len(w)), logz=float(log_z),
                q_inside_prior=float(inside.mean()))


# ---------------------------------------------------------------- the estimator (GPU)

def preprocess(x):
    import torch
    return torch.asinh(x / SIGMA)


def build():
    import torch.nn as nn
    import zuko

    class NPE(nn.Module):
        def __init__(self, n_x=len(T.WL_OUT), n_emb=128):
            super().__init__()
            self.embed = nn.Sequential(
                nn.Linear(n_x, 512), nn.ELU(), nn.Linear(512, 512), nn.ELU(),
                nn.Linear(512, 256), nn.ELU(), nn.Linear(256, n_emb))
            hidden = [int(h) for h in os.environ.get("FLOW_HIDDEN", "512,512").split(",")]
            # Coupling (passes=2): sampling is one pass per transform, against D for a fully autoregressive
            # flow, which made the SIR proposal take hours (~2000 draws/s on a 1080 Ti).
            self.flow = zuko.flows.NSF(D, n_emb, transforms=int(os.environ.get("FLOW_TRANSFORMS", 8)),
                                       passes=int(os.environ.get("FLOW_PASSES", 2)), hidden_features=hidden)

        def forward(self, theta, x):
            return -self.flow(self.embed(preprocess(x))).log_prob(theta).mean()

        def posterior(self, x):
            return self.flow(self.embed(preprocess(x)))

    return NPE()


def load_rounds(R, dev):
    """Pooled pairs of rounds 0..R; the first 5% of each round is held out for validation."""
    import torch
    tr, va = [], []
    for r in range(R + 1):
        d = np.load(OUT + f"pairs-{r}.npz")
        th, f = to_unit(d["theta"]).astype(np.float32), d["f"]
        n_val = len(th) // 20
        va.append((th[:n_val], f[:n_val]))
        tr.append((th[n_val:], f[n_val:]))
    cat = lambda parts, i: torch.tensor(np.concatenate([p[i] for p in parts]), device=dev)
    return cat(tr, 0), cat(tr, 1), cat(va, 0), cat(va, 1)


def train(R, dev):
    import torch
    torch.manual_seed(SEED + R)
    model = build().to(dev)
    if os.environ.get("REUSE") == "1" and os.path.exists(OUT + f"npe-{R}.pt"):  # resume after a timed-out SIR
        model.load_state_dict(torch.load(OUT + f"npe-{R}.pt", weights_only=False)["state"])
        print(f"round {R}: reusing npe-{R}.pt", flush=True)
        return model
    th, f, th_v, f_v = load_rounds(R, dev)
    if R > 0:
        model.load_state_dict(torch.load(OUT + f"npe-{R - 1}.pt", weights_only=False)["state"])
    lr = 1e-3 if R == 0 else 5e-4
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=4)
    batch = int(os.environ.get("BATCH", 1024))
    epochs, patience = int(os.environ.get("EPOCHS", 150)), int(os.environ.get("PATIENCE", 12))
    g = torch.Generator(device=dev).manual_seed(1)
    xv = f_v + SIGMA * torch.randn(f_v.shape, generator=g, device=dev)
    best, best_state, wait, log = np.inf, None, 0, []
    t0 = time.time()
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(len(th), device=dev)
        losses = []
        for i in range(0, len(perm), batch):
            idx = perm[i:i + batch]
            loss = model(th[idx], f[idx] + SIGMA * torch.randn_like(f[idx]))
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            losses.append(loss.item())
        model.eval()
        with torch.no_grad():
            val = float(np.mean([model(th_v[i:i + 8192], xv[i:i + 8192]).item() for i in range(0, len(th_v), 8192)]))
        sched.step(val)
        log.append((float(np.mean(losses)), val))
        print(f"round {R} epoch {ep:3d}  train {np.mean(losses):.3f}  valid {val:.3f}  "
              f"lr {opt.param_groups[0]['lr']:.1e}  {time.time() - t0:.0f} s", flush=True)
        if val < best - 1e-3:
            best, wait = val, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    tmp = OUT + f"npe-{R}.pt.tmp"
    torch.save({"state": best_state, "log": log}, tmp)
    os.replace(tmp, OUT + f"npe-{R}.pt")
    model.load_state_dict(best_state)
    log_summary(R, valid=best, epochs=len(log), train_seconds=time.time() - t0, n_train=len(th))
    return model


def sample_logq(post, n, chunk=int(os.environ.get("SAMPLE_CHUNK", 8192))):
    """Samples of q in unit coordinates, with their log densities."""
    import torch
    us, lq = [], []
    with torch.no_grad():
        for i in range(0, n, chunk):
            u, l = post.rsample_and_log_prob((min(chunk, n - i),))
            us.append(u)
            lq.append(l)
    return torch.cat(us), torch.cat(lq)


def round_(R):
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    xo = x_obs()
    model = train(R, dev)
    post = model.posterior(torch.tensor(xo, dtype=torch.float32, device=dev))
    # Draws for importance sampling against the exact likelihood (done by the next CPU job)
    t0 = time.time()
    u, lq = sample_logq(post, N_IS)
    print(f"round {R}: {N_IS} draws from q in {time.time() - t0:.0f} s", flush=True)
    log_jac = np.sum(np.log(2 / (UP - LO)))
    save_npz(OUT + f"isdraws-{R}.npz", theta=from_unit(u.double().cpu().numpy()),
             log_q=lq.double().cpu().numpy() + log_jac)
    # Posterior samples (inside the prior box) for the plots
    inside = torch.all(u.abs() <= 1, dim=1)
    save_npz(OUT + f"posterior-{R}.npz", samples=from_unit(u[inside].double().cpu().numpy()))
    if R + 1 >= ROUNDS:
        return
    # HPR threshold from samples of q
    t0 = time.time()
    _, lq_ref = sample_logq(post, max(200_000, int(20 / EPS)))
    tau = float(np.quantile(lq_ref.double().cpu().numpy(), EPS))
    # SIR from the truncated prior: K candidates per draw
    out, ess, logv = [], [], []
    per = min(max(1, 4_000_000 // K), N)
    with torch.no_grad():
        while sum(len(o) for o in out) < N:
            u, lq = sample_logq(post, per * K)
            keep = torch.all(u.abs() <= 1, dim=1) & (lq > tau)
            logw = torch.where(keep, -lq, torch.full_like(lq, -torch.inf)).view(per, K)
            # prior volume kept: log E_q[p 1[HPR] / q]
            logv.append((torch.logsumexp((logw + LOG_UNIT_PRIOR).flatten(), 0) - np.log(per * K)).item())
            ok = torch.isfinite(logw).any(dim=1)
            wn = torch.softmax(logw[ok], dim=1)
            ess.append((1 / (wn ** 2).sum(1)).mean().item())
            j = torch.multinomial(wn, 1).squeeze(1)
            out.append(u.view(per, K, D)[ok][torch.arange(len(j), device=dev), j])
            print(f"  SIR: {sum(len(o) for o in out)} draws, {time.time() - t0:.0f} s", flush=True)
    theta = from_unit(torch.cat(out)[:N].double().cpu().numpy())
    save_npz(OUT + f"theta-{R + 1}.npz", theta=theta)
    log10_vol = float(np.mean(logv) / np.log(10))
    print(f"round {R}: proposal for round {R + 1}, tau {tau:.2f}, log10 prior volume kept {log10_vol:.2f}, "
          f"SIR ESS per draw {np.mean(ess):.1f} of {K}, unique {len(np.unique(theta, axis=0))}, "
          f"{time.time() - t0:.0f} s", flush=True)
    log_summary(R, tau=tau, log10_volume=log10_vol, sir_ess=float(np.mean(ess)))


# ---------------------------------------------------------------- reference

def _prior_transform(c):
    return LO + c * (UP - LO)


def nested(nlive=int(os.environ.get("NLIVE", 1000))):
    import dynesty
    os.makedirs(OUT, exist_ok=True)
    xo = x_obs()
    ck = OUT + "dynesty.save"
    t0 = time.time()
    with Pool(ncpu(), initializer=_init, initargs=(xo,)) as pool:
        if os.path.exists(ck):
            sampler = dynesty.NestedSampler.restore(ck, pool=pool)
            sampler.run_nested(resume=True, checkpoint_file=ck, checkpoint_every=600, print_progress=False)
        else:
            sampler = dynesty.NestedSampler(_loglike, _prior_transform, D, nlive=nlive, sample="rslice",
                                            pool=pool, queue_size=ncpu(), rstate=np.random.default_rng(SEED))
            sampler.run_nested(dlogz=0.5, checkpoint_file=ck, checkpoint_every=600, print_progress=False)
    res = sampler.results
    save_npz(OUT + "nested.npz", samples=res.samples_equal(), logz=res.logz[-1], logzerr=res.logzerr[-1],
             ncall=int(np.sum(res.ncall)), seconds=time.time() - t0)
    print(f"nested: log Z {res.logz[-1]:.2f} ± {res.logzerr[-1]:.2f}, {int(np.sum(res.ncall))} calls, "
          f"{time.time() - t0:.0f} s", flush=True)


# ---------------------------------------------------------------- report

def _load_samples(run, R=None):
    """Last-round q samples and IS-reweighted samples of a run (R = last round with both)."""
    base = os.path.join(os.path.dirname(OUT.rstrip("/")), run) + "/"
    s = json.load(open(base + "summary.json"))
    rounds = sorted(int(r) for r in s if os.path.exists(base + f"posterior-{r}.npz"))
    R = rounds[-1] if R is None else R
    q = np.load(base + f"posterior-{R}.npz")["samples"]
    is_ = np.load(base + f"is-{R}.npz")["samples"] if os.path.exists(base + f"is-{R}.npz") else None
    return s, q, is_


def report():
    """RUNS="tsnpe amortised": table per round, and the 30 marginals against the nested-sampling reference."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    top = os.path.dirname(OUT.rstrip("/")) + "/"
    runs = os.environ.get("RUNS", "tsnpe amortised").split()
    ref = np.load(top + "nested/nested.npz")["samples"] if os.path.exists(top + "nested/nested.npz") else None
    sd_prior = (UP - LO) / np.sqrt(12)
    for run in runs:
        s, _, _ = _load_samples(run)
        print(f"\n{run}")
        print("round  sims(total)  valid    epochs  IS eff   IS ESS   log Z     log10 vol kept")
        tot = 0
        for r in sorted(s, key=int):
            v = s[r]
            tot += v.get("n_sims", 0)
            print(f"{r:>5}  {tot:>11}  {v.get('valid', np.nan):7.2f}  {v.get('epochs', 0):>6}  "
                  f"{v.get('is_efficiency', np.nan):7.4f}  {v.get('is_ess', np.nan):7.0f}  "
                  f"{v.get('logz', np.nan):8.2f}  {v.get('log10_volume', np.nan):8.2f}")
    if ref is not None:
        print("\nagainst the nested-sampling reference, per parameter, in reference std units:")
        print("run          |mean err| med / max    std ratio med [min, max]")
        for run in runs:
            for kind, smp in zip(["q", "q+IS"], _load_samples(run)[1:]):
                if smp is None:
                    continue
                err = np.abs(smp.mean(0) - ref.mean(0)) / ref.std(0)
                rat = smp.std(0) / ref.std(0)
                print(f"{run + ' ' + kind:<12} {np.median(err):6.3f} / {err.max():5.2f}       "
                      f"{np.median(rat):5.2f} [{rat.min():.2f}, {rat.max():.2f}]")
    fig, axes = plt.subplots(5, 6, figsize=(18, 13), facecolor="white")
    colors = {"tsnpe": "#d1495b", "amortised": "#1f5fae"}
    for i, ax in enumerate(axes.flat):
        bins = np.linspace(LO[i], UP[i], 60)
        if ref is not None:
            ax.hist(ref[:, i], bins, density=True, color="0.75", label="nested sampling (exact likelihood)")
        for run in runs:
            _, q, is_ = _load_samples(run)
            c = colors.get(run, None)
            ax.hist(q[:, i], bins, density=True, histtype="step", color=c, lw=1.2, label=f"{run}: q")
            if is_ is not None:
                ax.hist(is_[:, i], bins, density=True, histtype="step", color=c, lw=1.0, ls=":",
                        label=f"{run}: q + importance sampling")
        ax.axvline(T.THETA_STAR[i], color="k", lw=0.8, label="truth")
        ax.set_title(T.NAMES[i], fontsize=10)
        ax.set_yticks([])
    axes.flat[0].legend(fontsize=7, loc="upper left", bbox_to_anchor=(0, -0.25 - 0 * 1))
    h, l = axes.flat[0].get_legend_handles_labels()
    axes.flat[0].get_legend().remove()
    fig.legend(h, l, loc="lower center", ncol=len(l), fontsize=9)
    fig.suptitle("30-parameter toy: 1D marginals of the benchmark posterior", fontsize=13)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(top + "report.png", dpi=80)
    print("\n" + top + "report.png")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "simulate":
        simulate(int(sys.argv[2]))
    elif cmd == "round":
        round_(int(sys.argv[2]))
    elif cmd == "nested":
        nested()
    elif cmd == "report":
        report()
