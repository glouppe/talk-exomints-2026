"""Slide figures for the 30-parameter toy benchmark (backup slides), from the runs of toy_tsnpe.py on alan.

    python tools/t30_figures.py   # -> figures/t30-corner.png, figures/t30-chi2.png

Reads .render/data/t30/ (fetched from /scratch/.../exomints/t30/): nested-s1-n2000/nested.npz (reference),
amortised/posterior-0.npz (amortised NPE, 1M simulations), tsnpe/is-4.npz (TSNPE, 5 rounds of 200k, reweighted by
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
NS_COL, NPE_COL, TS_COL = "#9a9a9a", "#d1495b", "#2a9d8f"
LABELS = {"R_p": r"$R_P$", "T_0": r"$T_0$", "r_3": r"$r_3$", "log_H2O": r"$\log X_{\rm H_2O}$",
          "log_CH4": r"$\log X_{\rm CH_4}$", "log_CO": r"$\log X_{\rm CO}$", "log_FeH": r"$\log X_{\rm FeH}$",
          "log_TiO": r"$\log X_{\rm TiO}$", "log_VO": r"$\log X_{\rm VO}$"}
SHOW = ["R_p", "T_0", "log_H2O", "log_CO", "log_FeH", "log_VO"]


def sets():
    ns = np.load(D + "nested-s1-n2000/nested.npz")
    return [("nested sampling", ns["samples"], NS_COL),
            ("NPE, amortized", np.load(D + "amortised/posterior-0.npz")["samples"], NPE_COL),
            ("TSNPE + importance sampling", np.load(D + "tsnpe/is-4.npz")["samples"], TS_COL)]


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


def chi2_fig(n=400):
    """χ² of the observation against posterior predictive draws, one histogram per method."""
    x = np.load(D + "xobs.npz")["x_obs"]
    sim = T.Simulator(noisy=False)
    rng = np.random.default_rng(0)
    plt.rcParams.update({"font.size": 20, "font.family": "Roboto", "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(8, 5.2), dpi=100)
    bins = np.linspace(100, 400, 61)
    for lab, s, c in sets():
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
    ax.legend(frameon=False, fontsize=17, loc="upper right")
    fig.tight_layout()
    fig.savefig("figures/t30-chi2.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    corner_fig()
    chi2_fig()
