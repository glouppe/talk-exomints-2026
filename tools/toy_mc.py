"""Model comparison on the toy problem: cloudy (6 parameters) vs clear (5 parameters).

    python tools/toy_mc.py classify   # classifier p(M|x) on simulations of both models -> .render/data/toy-mc/classifier.pt
    python tools/toy_mc.py evidence   # IS evidence for each (model, observation) with the NPE of each model
    python tools/toy_mc.py figures    # figures/mc-ppc.png, figures/mc-bayes.png

Layout of .render/data/toy-mc/:
    xobs-{cloudy,clear}.npz                 observations (theta_star, x_obs)
    pairs-{cloudy,clear}.npz, npe-{cloudy,clear}.pt   training pairs and NPE per model
    {model}-{obs}/                          posterior.npz, is.npz (local); nested.npz (from alan)
Run with .render/venv.
"""

import os
import shutil
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import toy_exo as T

D = ".render/data/toy-mc/"
SIGMA = T.SIGMA_NOISE * T.Simulator.scale
MODELS, OBS = ["cloudy", "clear"], ["cloudy", "clear"]
COL = {"cloudy": "#d1495b", "clear": "#1f5fae"}
VENV = ".render/venv/bin/python"


def run_npe(model, obs, cmd):
    out = f"{D}{model}-{obs}/"
    os.makedirs(out, exist_ok=True)
    if not os.path.exists(out + "npe.pt"):
        shutil.copy(f"{D}npe-{model}.pt", out + "npe.pt")
    env = dict(os.environ, TOY_OUT=out, TOY_MODEL=model, X_OBS=f"{D}xobs-{obs}.npz")
    subprocess.run([VENV, "tools/toy_npe.py", cmd], env=env, check=True)


def evidence():
    for m in MODELS:
        for o in OBS:
            run_npe(m, o, "observe")
            run_npe(m, o, "is")


# ---------------------------------------------------------------- classifier

def classify(n_per_model=400_000, epochs=30, batch=1024):
    import torch
    import torch.nn as nn
    torch.manual_seed(0)
    xs, ys = [], []
    for k, m in enumerate(MODELS):
        f = np.load(f"{D}pairs-{m}.npz")["f"][:n_per_model]
        xs.append(f)
        ys.append(np.full(len(f), k))
    f = torch.tensor(np.concatenate(xs), dtype=torch.float32)
    y = torch.tensor(np.concatenate(ys), dtype=torch.float32)
    n = len(y)
    perm = torch.randperm(n)
    f, y = f[perm], y[perm]
    n_val = n // 20
    net = nn.Sequential(nn.Linear(len(T.WL_OUT), 512), nn.ELU(), nn.Linear(512, 256), nn.ELU(),
                        nn.Linear(256, 256), nn.ELU(), nn.Linear(256, 1))
    pre = lambda x: torch.asinh(x / SIGMA)
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    bce = nn.BCEWithLogitsLoss()
    for ep in range(epochs):
        net.train()
        idx = torch.randperm(n - n_val) + n_val
        for i in range(0, len(idx), batch):
            b = idx[i:i + batch]
            x = f[b] + SIGMA * torch.randn_like(f[b])
            loss = bce(net(pre(x)).squeeze(-1), y[b])
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()
        net.eval()
        with torch.no_grad():
            g = torch.Generator().manual_seed(1)
            xv = f[:n_val] + SIGMA * torch.randn(f[:n_val].shape, generator=g)
            lv = net(pre(xv)).squeeze(-1)
            acc = ((lv > 0).float() == y[:n_val]).float().mean().item()
            print(f"epoch {ep:2d}  valid loss {bce(lv, y[:n_val]).item():.4f}  accuracy {acc:.3f}", flush=True)
    torch.save(net.state_dict(), D + "classifier.pt")
    with torch.no_grad():
        for o in OBS:
            x = torch.tensor(np.load(f"{D}xobs-{o}.npz")["x_obs"], dtype=torch.float32)
            logit = net(pre(x)).item()  # log p(clear|x) / p(cloudy|x), equal prior odds
            print(f"obs {o}: log B(cloudy:clear) from classifier = {-logit:.2f}")
            np.save(f"{D}classifier-logB-{o}.npy", -logit)


# ---------------------------------------------------------------- figures

def figures():
    plt.rcParams.update({"font.size": 20, "axes.spines.top": False, "axes.spines.right": False,
                         "font.family": "Roboto"})
    sim = T.Simulator(noisy=False)
    # Posterior predictive of each model, for each observation, with normalized residuals below
    fig = plt.figure(figsize=(16, 7.5), dpi=100)
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.08, wspace=0.12)
    for c, o in enumerate(OBS):
        ax = fig.add_subplot(gs[0, c])
        axr = fig.add_subplot(gs[1, c], sharex=ax)
        x = np.load(f"{D}xobs-{o}.npz")["x_obs"]
        for m in MODELS:
            smp = np.load(f"{D}{m}-{o}/is.npz")["samples"][:200]
            full = smp if m == "cloudy" else np.insert(smp, 4, 2.0, axis=-1)
            f = np.array([sim.clean(t) for t in full])
            lo, hi = np.percentile(f, [2.5, 97.5], axis=0)
            med = np.median(f, axis=0)
            ax.fill_between(T.WL_OUT, lo, hi, color=COL[m], alpha=0.35, lw=0, label=f"{m} model")
            r = (x - med) / SIGMA
            axr.plot(T.WL_OUT, r, "o-", ms=4, lw=1.2, color=COL[m], alpha=0.85)
        ax.errorbar(T.WL_OUT, x, yerr=SIGMA, fmt="o", ms=4, color="#222", elinewidth=1, label="observation")
        ax.set_title(f"A {o} planet", loc="left", fontsize=26)
        ax.set_xlim(0.95, 2.45)
        plt.setp(ax.get_xticklabels(), visible=False)
        axr.axhline(0, color="#999", lw=1)
        axr.set_ylim(-4.5, 4.5)
        axr.set_xlabel("Wavelength [μm]")
        if c == 0:
            ax.set_ylabel("Flux")
            axr.set_ylabel("Residual [σ]")
            ax.legend(frameon=False, fontsize=18, loc="upper right")
        else:
            plt.setp(ax.get_yticklabels(), visible=False)
            plt.setp(axr.get_yticklabels(), visible=False)
    fig.savefig("figures/mc-ppc.png", bbox_inches="tight")

    # log Bayes factors: IS, nested, classifier
    # Shown ~375 px wide: 22 pt -> ~15 px on screen
    plt.rcParams["font.size"] = 22
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    methods = [("importance sampling", "is", "#d1495b"), ("nested sampling", "nested", "#555"),
               ("classifier", "clf", "#2a9d8f")]
    for j, o in enumerate(OBS):
        for k, (label, key, c) in enumerate(methods):
            if key == "clf":
                p = f"{D}classifier-logB-{o}.npy"
                if not os.path.exists(p):
                    continue
                v, e = float(np.load(p)), 0.0
            else:
                fs = [f"{D}{m}-{o}/{key}.npz" for m in MODELS]
                if not all(os.path.exists(f) for f in fs):
                    continue
                a, b = np.load(fs[0]), np.load(fs[1])
                ek = "logz_err" if key == "is" else "logzerr"
                v = float(a["logz"] - b["logz"])
                e = float(np.hypot(a[ek], b[ek])) if ek in a and ek in b else 0.0
            y = j + (k - 1) * 0.22
            ax.errorbar([v], [y], xerr=[e], fmt="o", ms=14, color=c, elinewidth=2, capsize=4,
                        label=label if j == 0 else None)
    ax.axvline(0, color="#999", lw=1.5, ls="--")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["cloudy\nplanet", "clear\nplanet"])
    ax.set_ylim(1.45, -0.45)
    ax.set_xlabel(r"$\log B$")
    ax.legend(frameon=False, fontsize=20, loc="lower right", handletextpad=0.2, borderaxespad=0.1)
    fig.tight_layout()
    fig.savefig("figures/mc-bayes.png", bbox_inches="tight")


# ---------------------------------------------------------------- amortized model comparison over a survey

def load_classifier():
    import torch
    import torch.nn as nn
    net = nn.Sequential(nn.Linear(len(T.WL_OUT), 512), nn.ELU(), nn.Linear(512, 256), nn.ELU(),
                        nn.Linear(256, 256), nn.ELU(), nn.Linear(256, 1))
    net.load_state_dict(torch.load(D + "classifier.pt"))
    net.eval()
    return net


def survey(n=1500, seed=13):
    """p(cloudy | x) for many simulated cloudy planets, against their cloud-top pressure."""
    import time
    import torch
    net = load_classifier()
    sim = T.Simulator(noisy=True, seed=seed)
    th = sim.sample_prior(n)
    x = np.array([sim(t) for t in th])
    t0 = time.time()
    with torch.no_grad():
        logit = net(torch.asinh(torch.tensor(x, dtype=torch.float32) / SIGMA)).squeeze(-1).numpy()
    dt = time.time() - t0
    p_cloudy = 1 / (1 + np.exp(logit))
    np.savez(D + "survey.npz", theta=th, p_cloudy=p_cloudy, seconds=dt)
    print(f"{n} spectra classified in {dt:.2f} s")
    plt.rcParams.update({"font.size": 20, "axes.spines.top": False, "axes.spines.right": False,
                         "font.family": "Roboto"})
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=100)
    ax.scatter(th[:, 4], p_cloudy, s=14, c=COL["cloudy"], alpha=0.35, lw=0)
    # running median
    bins = np.linspace(T.LOWER[4], T.UPPER[4], 16)
    c = (bins[:-1] + bins[1:]) / 2
    med = [np.median(p_cloudy[(th[:, 4] >= a) & (th[:, 4] < b)]) for a, b in zip(bins[:-1], bins[1:])]
    ax.plot(c, med, color="#222", lw=3)
    ax.axhline(0.5, color="#999", lw=1.5, ls="--")
    ax.set_xlabel(r"Cloud-top pressure $\log P_{\rm cloud}$ [bar]  (higher: deeper clouds)")
    ax.set_ylabel(r"$p({\rm cloudy} \,|\, x)$")
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlim(T.LOWER[4], T.UPPER[4])
    fig.tight_layout()
    fig.savefig("figures/mc-survey.png")


if __name__ == "__main__":
    {"classify": classify, "evidence": evidence, "figures": figures, "survey": survey}[sys.argv[1]]()
