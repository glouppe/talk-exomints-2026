"""Corner plot and posterior predictive check for the 30-parameter toy benchmark (toy_exo30.py).

    python tools/plot_t30.py      # -> $T30/corner-full.png, corner-zoom.png, ppc.png

Sets compared (each included if its file exists): nested sampling runs (exact likelihood), and for each run in
RUNS its last-round flow q and q reweighted by importance sampling with the exact likelihood.
Environment: T30 (default /scratch/users/$USER/exomints/t30), RUNS ("tsnpe tsnpe2 amortised amortised2").
"""

import glob
import json
import os
import sys
from multiprocessing import Pool

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(__file__))
import toy_exo30 as T

B = os.environ.get("T30", f"/scratch/users/{os.environ['USER']}/exomints/t30") + "/"
RUNS = os.environ.get("RUNS", "tsnpe tsnpe2 amortised amortised2").split()
ONLY_IS = os.environ.get("ONLY_IS") == "1"  # show q + IS alone where it exists
TAG = os.environ.get("TAG", "")  # output suffix
SIGMA = T.SIGMA_NOISE * T.Simulator.scale
LO, UP = T.LOWER, T.UPPER
COLORS = {"tsnpe": "#d1495b", "tsnpe2": "#e07b39", "amortised": "#1f5fae", "amortised2": "#2a9d8f",
          "tsnpe2-s1": "#8e5ea2", "tsnpe2-s2": "#3a9a5b"}


def load_sets():
    """[(label, samples, style)]: nested runs first (filled grey), then each run's q (solid) and q+IS (dashed)."""
    sets = []
    for i, p in enumerate(sorted(glob.glob(B + os.environ.get("NESTED", "nested*") + "/nested.npz"))):
        name = os.path.basename(os.path.dirname(p))
        d = np.load(p)
        sets.append((f"{name}: nested sampling, log Z {float(d['logz']):.2f}", d["samples"],
                     dict(color=["0.55", "0.3"][i % 2], filled=i == 0, ls="-")))
    for run in RUNS:
        sp = B + run + "/summary.json"
        if not os.path.exists(sp):
            continue
        s = json.load(open(sp))
        rounds = sorted(int(r) for r in s if os.path.exists(B + f"{run}/posterior-{r}.npz"))
        if not rounds:
            continue
        R = rounds[-1]
        c = COLORS.get(run, "C0")
        tag = f"{run} round {R}" if len(s) > 1 or R > 0 else run
        sims = sum(v.get("n_sims", 0) for r, v in s.items() if int(r) <= R)
        has_is = os.path.exists(B + f"{run}/is-{R}.npz") and s[str(R)].get("is_ess", 0) >= 50  # fewer: a few points
        if not (ONLY_IS and has_is):
            sets.append((f"{tag}: q ({sims // 1000}k sims)", np.load(B + f"{run}/posterior-{R}.npz")["samples"],
                         dict(color=c, filled=False, ls="-")))
        if has_is:
            ess = s[str(R)].get("is_ess", np.nan)
            sets.append((f"{tag}: q + importance sampling (ESS {ess:.0f})", np.load(B + f"{run}/is-{R}.npz")["samples"],
                         dict(color=c, filled=False, ls="--")))
    return sets


def levels(h, qs=(0.95, 0.68)):
    """Density thresholds enclosing the given masses."""
    v = np.sort(h.ravel())[::-1]
    c = np.cumsum(v) / v.sum()
    return [v[min(np.searchsorted(c, q), len(v) - 1)] for q in qs]


def corner(sets, idx, path, size):
    n = len(idx)
    fig, axes = plt.subplots(n, n, figsize=(size * n, size * n), facecolor="white")
    nb = 40
    for a, i in enumerate(idx):
        for b, j in enumerate(idx):
            ax = axes[a, b]
            if b > a:
                ax.axis("off")
                continue
            if a == b:
                bins = np.linspace(LO[i], UP[i], nb + 1)
                for lab, smp, st in sets:
                    h, _ = np.histogram(smp[:, i], bins, density=True)
                    h = gaussian_filter(h, 1.0)
                    x = 0.5 * (bins[1:] + bins[:-1])
                    if st["filled"]:
                        ax.fill_between(x, h, color=st["color"], alpha=0.5, lw=0)
                    else:
                        ax.plot(x, h, color=st["color"], ls=st["ls"], lw=1.1)
                ax.axvline(T.THETA_STAR[i], color="k", lw=0.8)
                ax.set_yticks([])
                ax.set_xlim(LO[i], UP[i])
            else:
                for lab, smp, st in sets:
                    h, xe, ye = np.histogram2d(smp[:, j], smp[:, i], nb, [[LO[j], UP[j]], [LO[i], UP[i]]])
                    h = gaussian_filter(h, 1.2)
                    lv = levels(h)
                    xc, yc = 0.5 * (xe[1:] + xe[:-1]), 0.5 * (ye[1:] + ye[:-1])
                    if st["filled"]:
                        ax.contourf(xc, yc, h.T, [lv[0], lv[1], h.max() + 1], colors=[st["color"]],
                                    alpha=0.35)
                        ax.contourf(xc, yc, h.T, [lv[1], h.max() + 1], colors=[st["color"]], alpha=0.45)
                    else:
                        ax.contour(xc, yc, h.T, lv, colors=st["color"], linestyles=st["ls"], linewidths=0.9)
                ax.plot(T.THETA_STAR[j], T.THETA_STAR[i], "k+", ms=6)
                ax.set_xlim(LO[j], UP[j])
                ax.set_ylim(LO[i], UP[i])
            fs = 7 if n > 15 else 9
            if a == n - 1:
                ax.set_xlabel(T.NAMES[j], fontsize=fs)
                ax.tick_params(axis="x", labelsize=fs - 2, rotation=45)
            else:
                ax.set_xticklabels([])
            if b == 0 and a > 0:
                ax.set_ylabel(T.NAMES[i], fontsize=fs)
                ax.tick_params(axis="y", labelsize=fs - 2)
            else:
                ax.set_yticklabels([])
    handles = []
    for lab, _, st in sets:
        if st["filled"]:
            handles.append(matplotlib.patches.Patch(color=st["color"], alpha=0.5, label=lab))
        else:
            handles.append(matplotlib.lines.Line2D([], [], color=st["color"], ls=st["ls"], label=lab))
    handles.append(matplotlib.lines.Line2D([], [], color="k", marker="+", ls="-", lw=0.8, label="truth"))
    fig.legend(handles=handles, loc="upper right", fontsize=11 if n > 15 else 10, frameon=False,
               bbox_to_anchor=(0.98, 0.98))
    fig.suptitle("30-parameter toy benchmark: posterior (contours: 68% and 95%)", fontsize=14 if n > 15 else 12,
                 x=0.55, y=0.995)
    fig.subplots_adjust(hspace=0.06, wspace=0.06, left=0.05, bottom=0.05, right=0.99, top=0.97)
    fig.savefig(path, dpi=60 if n > 15 else 90)
    plt.close(fig)
    print(path, flush=True)


_SIM = None


def _init():
    global _SIM
    _SIM = T.Simulator(noisy=False)


def _clean(th):
    return _SIM.clean(th)


def ppc(sets, x_obs, path, n=400):
    rng = np.random.default_rng(0)
    preds = []
    with Pool(len(os.sched_getaffinity(0)), initializer=_init) as pool:
        for lab, smp, st in sets:
            th = smp[rng.choice(len(smp), n, replace=False)]
            preds.append(np.array(pool.map(_clean, list(th), chunksize=10)))
    wl = T.WL_OUT
    fig = plt.figure(figsize=(15, 4.2 + 2.2 * len(sets)), facecolor="white")
    gs = fig.add_gridspec(1 + len(sets), 2, width_ratios=[3.2, 1], height_ratios=[2.6] + [1] * len(sets),
                          hspace=0.12, wspace=0.18)
    ax = fig.add_subplot(gs[0, 0])
    ax.errorbar(wl, x_obs, SIGMA, fmt=".", ms=3, color="k", elinewidth=0.6, label="x_obs (±1σ noise)", zorder=5)
    for (lab, _, st), f in zip(sets, preds):
        rep = f + SIGMA * rng.standard_normal(f.shape)
        lo, hi = np.quantile(rep, [0.025, 0.975], axis=0)
        ax.fill_between(wl, lo, hi, color=st["color"], alpha=0.18 if st["filled"] else 0.0, lw=0)
        ax.plot(wl, np.median(f, 0), color=st["color"], ls=st["ls"], lw=1.0, label=f"{lab}: median model")
        if not st["filled"]:
            ax.plot(wl, lo, color=st["color"], ls=":", lw=0.6)
            ax.plot(wl, hi, color=st["color"], ls=":", lw=0.6)
    ax.set_ylabel("flux [1e-16 W m$^{-2}$ μm$^{-1}$]")
    ax.set_title("posterior predictive: median model; band / dotted lines = 95% of replicated data (model + noise)",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="upper right")
    plt.setp(ax.get_xticklabels(), visible=False)
    # residuals per set: (x_obs - model) / σ for each predictive draw, 68% band and median
    for k, ((lab, _, st), f) in enumerate(zip(sets, preds)):
        axr = fig.add_subplot(gs[1 + k, 0], sharex=ax)
        r = (x_obs[None, :] - f) / SIGMA
        lo, med, hi = np.quantile(r, [0.16, 0.5, 0.84], axis=0)
        axr.fill_between(wl, lo, hi, color=st["color"], alpha=0.3, lw=0)
        axr.plot(wl, med, color=st["color"], lw=0.8)
        axr.axhline(0, color="k", lw=0.6)
        for y in (-2, 2):
            axr.axhline(y, color="k", lw=0.4, ls=":")
        axr.set_ylim(-4.5, 4.5)
        axr.set_ylabel("(x_obs − f) / σ", fontsize=8)
        axr.text(0.005, 0.97, lab, transform=axr.transAxes, fontsize=7.5, va="top", color=st["color"])
        if k < len(sets) - 1:
            plt.setp(axr.get_xticklabels(), visible=False)
    axr.set_xlabel("wavelength [μm]")
    # χ² of the observation against each predictive model, and the posterior predictive p-value
    axc = fig.add_subplot(gs[:, 1])
    chis = [np.sum(((x_obs - f) / SIGMA) ** 2, 1) for f in preds]
    lo_c, hi_c = min(np.quantile(c, 0.005) for c in chis), max(np.quantile(c, 0.995) for c in chis)
    bins = np.linspace(min(lo_c, 100), max(hi_c, len(wl) + 20), 60)
    for (lab, _, st), f in zip(sets, preds):
        chi_obs = np.sum(((x_obs - f) / SIGMA) ** 2, 1)
        rep = f + SIGMA * rng.standard_normal(f.shape)
        chi_rep = np.sum(((rep - f) / SIGMA) ** 2, 1)
        p = np.mean(chi_rep >= chi_obs)
        axc.hist(chi_obs, bins, histtype="stepfilled" if st["filled"] else "step", color=st["color"],
                 alpha=0.5 if st["filled"] else 1, ls=st["ls"], label=f"{lab.split(':')[0]}{':' + lab.split(':')[1][:24]}"
                 f"\nmedian χ² {np.median(chi_obs):.0f}, p = {p:.2f}")
    axc.axvline(len(wl), color="k", lw=0.8, ls=":", label=f"number of bins ({len(wl)})")
    chi_true = np.sum(((x_obs - T.Simulator(noisy=False).clean(T.THETA_STAR)) / SIGMA) ** 2)
    axc.axvline(chi_true, color="k", lw=1.0, label=f"χ² at the truth ({chi_true:.0f}): the noise draw")
    axc.set_xlabel("χ² of x_obs against posterior draws")
    axc.set_yticks([])
    axc.set_title("fit quality; p = posterior predictive p-value", fontsize=10)
    axc.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.08))
    fig.savefig(path, dpi=90, bbox_inches="tight")
    plt.close(fig)
    print(path, flush=True)


if __name__ == "__main__":
    sets = load_sets()
    for lab, smp, _ in sets:
        print(f"{len(smp):>7}  {lab}")
    x_obs = np.load(B + "xobs.npz")["x_obs"]
    corner(sets, list(range(30)), B + f"corner-full{TAG}.png", 0.9)
    # zoom: the 12 parameters the reference constrains most (smallest posterior / prior std)
    ref = sets[0][1]
    shrink = ref.std(0) / ((UP - LO) / np.sqrt(12))
    zoom = sorted(np.argsort(shrink)[:12])
    print("zoom:", [T.NAMES[i] for i in zoom])
    corner(sets, zoom, B + f"corner-zoom{TAG}.png", 1.6)
    ppc(sets, x_obs, B + f"ppc{TAG}.png")
