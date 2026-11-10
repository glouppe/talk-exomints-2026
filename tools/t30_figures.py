"""Slide figures for the 30-parameter toy benchmark (backup slides), from the runs of toy_tsnpe.py on alan.

    python tools/t30_figures.py   # -> figures/t30-corner.png, t30-corner-full.png, t30-chi2.png

Reads .render/data/t30/ (fetched from /scratch/.../exomints/t30/): nested-s1-n2000/nested.npz (reference),
amortised/posterior-0.npz (amortised NPE, 1M simulations), tsnpe2-s2/is-4.npz (TSNPE seed 2, 5 rounds of 200k, reweighted by
importance sampling), xobs.npz. Same sets as plot_t30.py's "npe-tsnpe-ns" figures, drawn at slide size.
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import toy_exo30 as T

D = ".render/data/t30/"
SIGMA = T.SIGMA_NOISE * T.Simulator.scale
NS_COL, NPE_COL, TS_COL = "#e08a1e", "#d1495b", "#2a9d8f"  # all three as lines: no method is the reference
TSNPE_RUN = "tsnpe2-s2"  # best of the four TSNPE runs (seed 2): IS ESS 3638 of 50k at round 4
LABELS = {"R_p": r"$R_P$", "T_0": r"$T_0$", "r_3": r"$r_3$", "log_H2O": r"$\log X_{\rm H_2O}$",
          "log_CH4": r"$\log X_{\rm CH_4}$", "log_CO": r"$\log X_{\rm CO}$", "log_FeH": r"$\log X_{\rm FeH}$",
          "log_TiO": r"$\log X_{\rm TiO}$", "log_VO": r"$\log X_{\rm VO}$"}
SHOW = ["R_p", "T_0", "log_H2O", "log_CO", "log_FeH", "log_VO"]


def sets():
    ns = np.load(D + "nested-s1-n2000/nested.npz")
    return [("nested sampling", ns["samples"], NS_COL),
            ("NPE, amortized", np.load(D + "amortised/posterior-0.npz")["samples"], NPE_COL),
            ("TSNPE + importance sampling", np.load(D + TSNPE_RUN + "/is-4.npz")["samples"], TS_COL)]


def corner_fig():
    import corner
    idx = [T.NAMES.index(n) for n in SHOW]
    data = sets()
    rng_ = [(T.LOWER[i], T.UPPER[i]) for i in idx]
    # zoom on the constrained parameters, keep the full prior range for the trace species
    for k, i in enumerate(idx):
        if T.NAMES[i] in ("R_p", "T_0", "log_H2O", "log_CH4", "log_CO"):
            lo = min(np.percentile(s[:, i], 0.5) for _, s, _ in data)
            hi = max(np.percentile(s[:, i], 99.5) for _, s, _ in data)
            pad = 0.1 * (hi - lo)
            rng_[k] = (lo - pad, hi + pad)
    plt.rcParams.update({"font.size": 21, "font.family": "Roboto"})
    kw = dict(bins=30, smooth=1.2, plot_datapoints=False, plot_density=False, levels=(0.68, 0.95), range=rng_,
              labels=[LABELS[n] for n in SHOW], label_kwargs={"fontsize": 21}, max_n_ticks=2, labelpad=0.12)
    (l0, s0, c0) = data[0]
    fig = corner.corner(s0[:, idx], color=c0, fill_contours=True, contour_kwargs={"linewidths": 0},
                        hist_kwargs={"lw": 0, "density": True, "histtype": "stepfilled", "alpha": 0.45}, **kw)
    for lab, s, c in data[1:]:
        corner.corner(s[:, idx], color=c, fig=fig, fill_contours=False, no_fill_contours=True,
                      contour_kwargs={"linewidths": 2.0}, hist_kwargs={"lw": 2.2, "density": True}, **kw)
    n = len(idx)
    for k in range(n):
        ax = fig.axes[k * n + k]
        ax.relim()
        ax.autoscale(axis="y")
        ax.set_ylim(0, ax.get_ylim()[1] * 1.05)
    corner.overplot_lines(fig, T.THETA_STAR[idx], color="#222", lw=1.2)
    fig.set_size_inches(11, 11)
    for ax in fig.axes:
        ax.tick_params(labelsize=17)
    handles = [plt.matplotlib.patches.Patch(color=NS_COL, alpha=0.6, label="nested sampling"),
               plt.Line2D([], [], color=NPE_COL, lw=3, label="NPE, amortized"),
               plt.Line2D([], [], color=TS_COL, lw=3, label="TSNPE + importance sampling"),
               plt.Line2D([], [], color="#222", lw=1.5, label=r"true $\theta$")]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.97, 0.97), frameon=False, fontsize=22)
    fig.savefig("figures/t30-corner.png", dpi=100, bbox_inches="tight")
    plt.close(fig)


def corner_full():
    """All 30 parameters. Axes zoomed where the reference posterior is narrow, prior range elsewhere."""
    import corner
    data = sets()
    ref = data[0][1]
    rng_ = []
    for i in range(len(T.NAMES)):
        lo, hi = np.percentile(ref[:, i], [0.5, 99.5])
        if hi - lo < 0.5 * (T.UPPER[i] - T.LOWER[i]):
            lo = min(np.percentile(s[:, i], 0.5) for _, s, _ in data)
            hi = max(np.percentile(s[:, i], 99.5) for _, s, _ in data)
            pad = 0.1 * (hi - lo)
            rng_.append((max(lo - pad, T.LOWER[i]), min(hi + pad, T.UPPER[i])))
        else:
            rng_.append((T.LOWER[i], T.UPPER[i]))
    import re
    sub = lambda t: re.sub(r"(\d)", r"$_{\1}$", t)  # digits as subscripts, with mathtext (Roboto has no glyphs)
    short = {"log_g": "log g", "R_p": "$R_p$", "T_0": "$T_0$", "log_Pc": "log $P_c$", "log_tau_c": r"log $\tau_c$",
             "alpha_c": r"$\alpha_c$"}
    labels = [short.get(n, f"$r_{n[2:]}$" if n.startswith("r_") else sub(n[4:]) if n.startswith("log_") else n)
              for n in T.NAMES]  # r_3 -> r_3, log_H2O -> H_2O
    plt.rcParams.update({"font.size": 14, "font.family": "Roboto"})
    kw = dict(bins=25, smooth=1.2, plot_datapoints=False, plot_density=False, levels=(0.68, 0.95), range=rng_,
              labels=labels, label_kwargs={"fontsize": 17}, max_n_ticks=0, labelpad=0.2)
    fig = None
    for lab, s, c in data:
        fig = corner.corner(s, color=c, fig=fig, fill_contours=False, no_fill_contours=True,
                            contour_kwargs={"linewidths": 0.9}, hist_kwargs={"lw": 1.2, "density": True}, **kw)
    n = len(T.NAMES)
    for k in range(n):
        ax = fig.axes[k * n + k]
        ax.relim()
        ax.autoscale(axis="y")
        ax.set_ylim(0, ax.get_ylim()[1] * 1.05)
    corner.overplot_lines(fig, T.THETA_STAR, color="#777", lw=0.4)
    fig.set_size_inches(22, 22)
    handles = [plt.Line2D([], [], color=NS_COL, lw=4, label="nested sampling"),
               plt.Line2D([], [], color=NPE_COL, lw=4, label="NPE, amortized"),
               plt.Line2D([], [], color=TS_COL, lw=4, label="TSNPE + importance sampling"),
               plt.Line2D([], [], color="#222", lw=2, label=r"true $\theta$")]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.95, 0.95), frameon=False, fontsize=40)
    fig.savefig("figures/t30-corner-full.png", dpi=60, bbox_inches="tight")
    plt.close(fig)


def marginals_fig(ncol=6):
    """Gallery of the 30 one-dimensional marginals, each over its full prior range."""
    import re
    data = sets()
    sub = lambda t: re.sub(r"(\d)", r"$_{\1}$", t)
    short = {"log_g": "log g", "R_p": "$R_p$", "T_0": "$T_0$", "log_Pc": "log $P_c$", "log_tau_c": r"log $\tau_c$",
             "alpha_c": r"$\alpha_c$"}
    names = [short.get(n, f"$r_{n[2:]}$" if n.startswith("r_") else sub(n[4:]) if n.startswith("log_") else n)
             for n in T.NAMES]
    n = len(T.NAMES)
    nrow = int(np.ceil(n / ncol))
    plt.rcParams.update({"font.size": 16, "font.family": "Roboto"})
    fig, axes = plt.subplots(nrow, ncol, figsize=(16, 2.25 * nrow), dpi=100)
    for i, ax in enumerate(axes.ravel()):
        if i >= n:
            ax.axis("off")
            continue
        bins = np.linspace(T.LOWER[i], T.UPPER[i], 41)
        for lab, s, c in data:
            ax.hist(s[:, i], bins, density=True, histtype="step", color=c, lw=1.8)
        ax.axvline(T.THETA_STAR[i], color="#222", lw=1.2)
        ax.set_xlim(T.LOWER[i], T.UPPER[i])
        ax.set_yticks([])
        ax.set_xticks([])
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.set_title(names[i], fontsize=18, pad=4)
    handles = [plt.Line2D([], [], color=NS_COL, lw=3, label="nested sampling"),
               plt.Line2D([], [], color=NPE_COL, lw=3, label="NPE, amortized"),
               plt.Line2D([], [], color=TS_COL, lw=3, label="TSNPE + importance sampling"),
               plt.Line2D([], [], color="#222", lw=1.5, label=r"true $\theta$")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=17, bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig("figures/t30-marginals.png", dpi=100, bbox_inches="tight")
    plt.close(fig)


def chi2_fig(n=400):
    """χ² of the observation against posterior predictive draws, one histogram per method."""
    x = np.load(D + "xobs.npz")["x_obs"]
    sim = T.Simulator(noisy=False)
    rng = np.random.default_rng(0)
    plt.rcParams.update({"font.size": 20, "font.family": "Roboto", "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=100)
    bins = np.linspace(100, 400, 61)
    legend = {"nested sampling": "nested sampling, 13.8M likelihood calls",
              "NPE, amortized": "NPE, amortized, 1M simulations\n(importance sampling: ESS 6)",
              "TSNPE + importance sampling": "TSNPE, 1M simulations\n(importance sampling: ESS 3638)"}
    for lab, s, c in sets():
        lab = legend[lab]
        th = s[rng.choice(len(s), n, replace=False)]
        chi = np.array([np.sum(((x - sim.clean(t)) / SIGMA) ** 2) for t in th])
        print(f"{lab}: median chi2 {np.median(chi):.0f}")
        if c == NS_COL:
            ax.hist(chi, bins, color=c, alpha=0.55, density=True, label=lab)
        else:
            ax.hist(chi, bins, histtype="step", lw=2.5, color=c, density=True, label=lab)
    chi_true = np.sum(((x - sim.clean(T.THETA_STAR)) / SIGMA) ** 2)
    ax.axvline(chi_true, color="#222", lw=1.5, ls="--")
    ax.text(chi_true + 4, 0.98, r"true $\theta$", transform=ax.get_xaxis_transform(), va="top", fontsize=18)
    ax.set_xlabel(r"$\chi^2$ of the observation, 176 bins")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.legend(frameon=False, fontsize=17, loc="upper right", labelspacing=0.8)
    fig.tight_layout()
    fig.savefig("figures/t30-chi2.png", dpi=100)
    plt.close(fig)


def ppc_fig(n=300):
    """Posterior predictive check (spectrum, residuals per method) and χ² of the observation, one figure."""
    x = np.load(D + "xobs.npz")["x_obs"]
    sim = T.Simulator(noisy=False)
    rng = np.random.default_rng(0)
    data = sets()
    preds = [np.array([sim.clean(t) for t in s[rng.choice(len(s), n, replace=False)]]) for _, s, _ in data]
    legend = ["nested sampling\n13.8M likelihood calls", "NPE, amortized\n1M simulations, ESS 6",
              "TSNPE\n1M simulations, ESS 3638"]
    plt.rcParams.update({"font.size": 18, "font.family": "Roboto", "axes.spines.top": False,
                         "axes.spines.right": False})
    fig = plt.figure(figsize=(16, 8.5), dpi=100)
    gs = fig.add_gridspec(4, 2, width_ratios=[2.6, 1], height_ratios=[2.2, 1, 1, 1], hspace=0.12, wspace=0.12)
    ax = fig.add_subplot(gs[0, 0])
    wl = T.WL_OUT
    for (lab, _, c), f in zip(data, preds):
        rep = f + SIGMA * rng.standard_normal(f.shape)
        lo, hi = np.quantile(rep, [0.025, 0.975], axis=0)
        ax.fill_between(wl, lo, hi, color=c, alpha=0.15, lw=0)
        ax.plot(wl, np.median(f, 0), color=c, lw=1.6)
    ax.errorbar(wl, x, yerr=SIGMA, fmt="o", ms=3, color="#222", elinewidth=0.8, zorder=5)
    ax.set_ylabel("Flux")
    ax.set_yticks([])
    ax.set_title("Posterior predictive check", loc="left", fontsize=22)
    plt.setp(ax.get_xticklabels(), visible=False)
    for k, ((lab, _, c), f) in enumerate(zip(data, preds)):
        axr = fig.add_subplot(gs[1 + k, 0], sharex=ax)
        r = (x[None, :] - f) / SIGMA
        lo, med, hi = np.quantile(r, [0.16, 0.5, 0.84], axis=0)
        axr.axhspan(-2, 2, color="#eeeeee", lw=0)
        axr.fill_between(wl, lo, hi, color=c, alpha=0.4, lw=0)
        axr.plot(wl, med, color=c, lw=1.0)
        axr.axhline(0, color="#999", lw=0.8)
        axr.set_ylim(-4.5, 4.5)
        axr.set_yticks([-3, 0, 3])
        axr.set_ylabel("Resid. [σ]" if k == 1 else "", fontsize=16)
        if k < 2:
            plt.setp(axr.get_xticklabels(), visible=False)
    axr.set_xlabel("Wavelength [μm]")
    axc = fig.add_subplot(gs[:, 1])
    bins = np.linspace(100, 400, 61)
    for (lab, _, c), f, leg in zip(data, preds, legend):
        chi = np.sum(((x - f) / SIGMA) ** 2, 1)
        axc.hist(chi, bins, histtype="step", lw=2.5, color=c, density=True, label=leg, orientation="horizontal")
    chi_true = np.sum(((x - sim.clean(T.THETA_STAR)) / SIGMA) ** 2)
    axc.axhline(chi_true, color="#222", lw=1.5, ls="--")
    axc.text(0.98, chi_true + 4, r"true $\theta$", transform=axc.get_yaxis_transform(), ha="right", fontsize=16)
    axc.set_ylabel(r"$\chi^2$ of the observation (176 bins)")
    axc.yaxis.set_label_position("right")
    axc.yaxis.tick_right()
    axc.spines["right"].set_visible(True)
    axc.spines["left"].set_visible(False)
    axc.set_xticks([])
    axc.set_title("Fit quality", loc="left", fontsize=22)
    axc.legend(frameon=False, fontsize=15, loc="upper right", labelspacing=1.0)
    fig.savefig("figures/t30-ppc.png", dpi=100, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    corner_fig()
    corner_full()
    marginals_fig()
    chi2_fig()
    ppc_fig()
