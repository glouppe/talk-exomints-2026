"""Figures for the NPE results on the toy simulator.

    python tools/toy_results.py flow       # animation: base samples pushed through the flow layers -> videos/toy-flow.mp4
    python tools/toy_results.py loss       # training curve -> figures/toy-loss.png
    python tools/toy_results.py corner     # NPE vs MCMC on the benchmark -> figures/toy-corner.png
    python tools/toy_results.py ppc        # posterior predictive check -> figures/toy-ppc.png
    python tools/toy_results.py embedding  # where the embedding looks: saliency per parameter -> figures/toy-embedding.png
    python tools/toy_results.py prior_pc   # animation: prior predictive check -> videos/toy-prior-pc.mp4
    python tools/toy_results.py misspec    # misspecified observation: posteriors + PPC -> figures/toy-misspec.png
    python tools/toy_results.py amortize   # animation: new spectra, instant posteriors -> videos/toy-amortize.mp4

Model and samples are read from $TOY_OUT (default .render/data/toy/). Run with .render/venv (torch, zuko, corner).
"""

import os
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(__file__))
import toy_exo as T
import toy_npe as N

OUT = N.OUT
SIGMA = N.SIGMA
NPE_COL, MCMC_COL, NS_COL, TRUE_COL = "#d1495b", "#555555", "#e08a1e", "#1f5fae"
# Font sizes are set per figure so that, once scaled onto the slide, text appears at the same size as in the
# simulator walk-through (20 pt in a 1600 px frame shown at 852 px: ~15 px labels, ~20 px titles).
plt.rcParams.update({"font.size": 18, "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": "Roboto"})


def load_model():
    m = N.build()
    m.load_state_dict(torch.load(OUT + "npe.pt", weights_only=False)["state"])
    m.eval()
    return m


def encode(writer_cmd_out, W, H, FPS):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "22", "-preset", "slow",
                             "-pix_fmt", "yuv420p", "-movflags", "+faststart", writer_cmd_out], stdin=subprocess.PIPE)


# ------------------------------------------------------------------ flow

def flow(i=0, j=3, n=3000, FPS=24):
    """Push base samples through the three transforms, in the (θ_i, θ_j) plane (unit coordinates)."""
    model = load_model()
    x_obs = torch.tensor(np.load(OUT + "posterior.npz")["x_obs"], dtype=torch.float32)
    with torch.no_grad():
        d = model.flow(model.embed(N.preprocess(x_obs)))
        z = d.base.sample((n,))
        stages = [z]
        for t in reversed(d.transform.transforms):  # sampling applies the inverse, last transform first
            z = t.inv(z)
            stages.append(z)
    stages = [s.numpy() for s in stages]
    titles = ["Noise $u$", "after layer 1", "after layer 2", r"Samples of $\theta$ given $x$"]
    W, H, DPI = 1200, 900, 100
    plt.rcParams["font.size"] = 23
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0.16, 0.15, 0.80, 0.74])
    p = encode("figures/videos/toy-flow.mp4", W, H, FPS)
    hold, move = int(0.9 * FPS), int(1.2 * FPS)
    seq = []
    for s in range(len(stages)):
        seq += [(s, s, 0.0)] * hold
        if s < len(stages) - 1:
            seq += [(s, s + 1, (k + 1) / move) for k in range(move)]
    seq += [(len(stages) - 1, len(stages) - 1, 0.0)] * hold
    lab = [T.LABELS[i], T.LABELS[j]]

    def box(z):  # square view around the samples of a stage
        c = np.median(z[:, [i, j]], 0)
        h = 1.25 * np.max(np.percentile(np.abs(z[:, [i, j]] - c), 99, 0))
        return c, h
    boxes = [box(z) for z in stages]
    for a, b, u in seq:
        u = u * u * (3 - 2 * u)
        pts = (1 - u) * stages[a] + u * stages[b]
        ax.cla()
        col = NPE_COL if (b == len(stages) - 1 and u > 0.5) or a == len(stages) - 1 else "#7a8ca8"
        ax.scatter(pts[:, i], pts[:, j], s=6, c=col, alpha=0.45, lw=0)
        c = (1 - u) * boxes[a][0] + u * boxes[b][0]
        h = np.exp((1 - u) * np.log(boxes[a][1]) + u * np.log(boxes[b][1]))  # zoom smoothly, in log scale
        ax.set_xlim(c[0] - h, c[0] + h)
        ax.set_ylim(c[1] - h, c[1] + h)
        ax.set_aspect("equal")
        ax.set_title(titles[b if u > 0.5 else a], fontsize=31, loc="left")
        ax.locator_params(nbins=4)
        ax.set_xlabel(f"{lab[0]} (rescaled)")
        ax.set_ylabel(f"{lab[1]} (rescaled)")
        fig.canvas.draw()
        p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
    fig.savefig("figures/toy-flow.png", dpi=DPI)
    p.stdin.close()
    p.wait()


# ------------------------------------------------------------------ loss

def loss():
    log = np.array(torch.load(OUT + "npe.pt", weights_only=False)["log"])
    plt.rcParams["font.size"] = 17
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=100)
    ax.plot(np.arange(1, len(log) + 1), log[:, 0], color="#888", lw=2.5, label="training")
    ax.plot(np.arange(1, len(log) + 1), log[:, 1], color=NPE_COL, lw=2.5, label="validation")
    ax.set_xlabel("Epoch")
    ax.set_ylabel(r"$-\log q_\phi(\theta | x)$")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("figures/toy-loss.png")


# ------------------------------------------------------------------ corner

def corner_plot():
    import corner
    p = np.load(OUT + "posterior.npz")
    m = np.load(OUT + "mcmc.npz")
    rng = np.random.default_rng(0)
    b = m["samples"][rng.choice(len(m["samples"]), 20000, replace=False)]
    a = p["samples"]
    lo = np.minimum(np.percentile(a, 0.5, 0), np.percentile(b, 0.5, 0))
    hi = np.maximum(np.percentile(a, 99.5, 0), np.percentile(b, 99.5, 0))
    rng_ = [(l - 0.1 * (h - l), h + 0.1 * (h - l)) for l, h in zip(lo, hi)]
    plt.rcParams["font.size"] = 21
    kw = dict(bins=35, smooth=1.0, plot_datapoints=False, plot_density=False, levels=(0.68, 0.95),
              range=rng_, labels=T.LABELS, label_kwargs={"fontsize": 21},
              max_n_ticks=2, labelpad=0.12)
    # Separate hist_kwargs per call: corner writes the colour into the dict it is given.
    fig = corner.corner(b, color=MCMC_COL, fill_contours=False, hist_kwargs={"lw": 2.2, "density": True}, **kw)
    ns_path = OUT + "nested.npz" if os.path.exists(OUT + "nested.npz") else ".render/data/toy/nested.npz"
    ns = np.load(ns_path) if os.path.exists(ns_path) else None
    if ns is not None:
        corner.corner(ns["samples"], color=NS_COL, fig=fig, fill_contours=False,
                      hist_kwargs={"lw": 2.2, "density": True}, **kw)
    corner.corner(a, color=NPE_COL, fig=fig, fill_contours=False, hist_kwargs={"lw": 2.2, "density": True}, **kw)
    n = len(T.NAMES)
    for k in range(n):  # rescale diagonal panels to fit both normalized histograms
        ax = fig.axes[k * n + k]
        ax.relim()
        ax.autoscale(axis="y")
        ax.set_ylim(0, ax.get_ylim()[1] * 1.05)
    corner.overplot_lines(fig, p["theta_star"], color=TRUE_COL, lw=1.5)
    fig.set_size_inches(12, 12)
    for ax in fig.axes:
        ax.tick_params(labelsize=21)
    handles = [plt.Line2D([], [], color=NPE_COL, lw=3, label=f"NPE ({float(p['seconds']):.1f} s)"),
               plt.Line2D([], [], color=MCMC_COL, lw=3, label="MCMC (~9 min)")]
    if ns is not None:
        handles.append(plt.Line2D([], [], color=NS_COL, lw=3, label=f"nested sampling ({float(ns['seconds']) / 60:.0f} min)"))
    handles.append(plt.Line2D([], [], color=TRUE_COL, lw=2, label=r"true $\theta$"))
    fig.legend(handles=handles,
               loc="upper right", bbox_to_anchor=(0.97, 0.97), frameon=False, fontsize=21)
    fig.savefig("figures/toy-corner.png", dpi=100, bbox_inches="tight")


# ------------------------------------------------------------------ ppc

def ppc(n=200):
    p = np.load(OUT + "posterior.npz")
    sim = T.Simulator(noisy=False)
    th = p["samples"][:n]
    f = np.array([sim.clean(t) for t in th])
    plt.rcParams["font.size"] = 17
    fig, ax = plt.subplots(figsize=(14, 6), dpi=100)
    lo, hi = np.percentile(f, [2.5, 97.5], axis=0)
    ax.fill_between(T.WL_OUT, lo, hi, color=NPE_COL, alpha=0.25, lw=0, label=r"$f(\theta)$, $\theta \sim q_\phi(\theta|x)$ (95%)")
    ax.plot(T.WL_OUT, np.median(f, 0), color=NPE_COL, lw=2)
    ax.errorbar(T.WL_OUT, p["x_obs"], yerr=SIGMA, fmt="o", ms=5, color="#222", elinewidth=1, label=r"observed $x$")
    ax.set_xlabel("Wavelength [μm]")
    ax.set_ylabel(r"Flux [$10^{-16}$ W m$^{-2}$ μm$^{-1}$]")
    ax.set_xlim(0.95, 2.45)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig("figures/toy-ppc.png")


# ------------------------------------------------------------------ embedding network

def saliency(n_spectra=150, n_samples=256, seed=5):
    """Where the network looks: |d E[theta_k | x] / d x_j|, in posterior standard deviations per noise sigma,
    averaged over simulated spectra. Saved to OUT/saliency.npy (6, n_bins)."""
    model = load_model()
    sim = T.Simulator(noisy=True, seed=seed)
    X = []
    for t in sim.sample_prior(4 * n_spectra):
        if 0.3 < sim.clean(t).mean() < 8:
            X.append(sim(t))
    torch.manual_seed(0)
    G = []
    for x in X[:n_spectra]:
        xt = torch.tensor(x, dtype=torch.float32, requires_grad=True)
        u = model.flow(model.embed(N.preprocess(xt))).rsample((n_samples,))
        sd, mean = u.std(0).detach(), u.mean(0)
        G.append([(torch.autograd.grad(mean[k], xt, retain_graph=True)[0] * SIGMA / sd[k]).abs().numpy()
                  for k in range(len(T.LOWER))])
    G = np.mean(G, axis=0)
    np.save(OUT + "saliency.npy", G)
    return G


def embedding_arch(sizes=(94, 512, 256, 256, 64), shown=(7, 10, 8, 8, 6)):
    """Figure: the embedding network on the observed spectrum. Input bins, dense layers drawn as columns of units
    with their sizes, and the 64 output features h(x_obs) as a colour strip."""
    model = load_model()
    x = np.load(OUT + "posterior.npz")["x_obs"]
    with torch.no_grad():
        h = model.embed(N.preprocess(torch.tensor(x, dtype=torch.float32))).numpy()
    W, H, DPI = 1600, 640, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    # input spectrum
    a0 = fig.add_axes([0.02, 0.30, 0.22, 0.45])
    a0.plot(T.WL_OUT, x, "o", ms=3, color="#222")
    a0.set_xticks([])
    a0.set_yticks([])
    a0.set_title(r"Spectrum $x$ (94 bins)", fontsize=20)
    # network
    an = fig.add_axes([0.28, 0.08, 0.50, 0.84])
    an.axis("off")
    an.set_xlim(-0.5, len(sizes) - 0.5)
    an.set_ylim(-0.75, 0.5)
    cols = []
    for c, (n_units, n_show) in enumerate(zip(sizes, shown)):
        ys = np.linspace(-0.42, 0.42, n_show) * (0.55 + 0.45 * n_show / max(shown))
        cols.append(ys)
        an.text(c, -0.62, str(n_units), ha="center", va="center", color="#555")
    for c in range(len(cols) - 1):
        for y0 in cols[c]:
            for y1 in cols[c + 1]:
                an.plot([c, c + 1], [y0, y1], color="#cccccc", lw=0.6, zorder=1)
    for c, ys in enumerate(cols):
        an.scatter(np.full(len(ys), c), ys, s=180, color="white", edgecolor="#555", lw=1.5, zorder=2)
    # output features
    a1 = fig.add_axes([0.82, 0.12, 0.05, 0.76])
    a1.imshow(h[:, None], aspect="auto", cmap="RdBu_r", vmin=-np.abs(h).max(), vmax=np.abs(h).max())
    a1.set_xticks([])
    a1.set_yticks([])
    fig.text(0.885, 0.5, r"$h(x)$" + "\n64 features", ha="left", va="center", fontsize=20)
    for x0, x1 in [(0.245, 0.30), (0.765, 0.81)]:
        fig.add_artist(plt.matplotlib.patches.FancyArrowPatch((x0, 0.5), (x1, 0.5), transform=fig.transFigure,
                                                             arrowstyle="-|>", mutation_scale=22, lw=2, color="#555"))
    for sp in a1.spines.values():
        sp.set_visible(False)
    fig.savefig("figures/toy-embedding-arch.png", dpi=DPI)


def embedding_anim(n_spectra=6, sizes=(94, 512, 256, 256, 64), shown=(7, 10, 8, 8, 6), FPS=24, seed=11):
    """Animation: several spectra go through the embedding network in turn. For each, the layers light up one after
    the other with the actual activations of a few units (z-scored per unit across the spectra shown), and the 64
    output features h(x) update. Outputs videos/toy-embedding.mp4 and the poster figures/toy-embedding-arch.png."""
    model = load_model()
    sim = T.Simulator(noisy=True, seed=seed)
    X = [np.load(OUT + "posterior.npz")["x_obs"]]
    for t in sim.sample_prior(20 * n_spectra):
        if len(X) == n_spectra:
            break
        if 0.3 < sim.clean(t).mean() < 8:
            X.append(sim(t))
    X = np.array(X)
    # activations: preprocessed input, then the output of each ELU, then h(x)
    acts = [N.preprocess(torch.tensor(X, dtype=torch.float32))]
    with torch.no_grad():
        z = acts[0]
        for layer in model.embed:
            z = layer(z)
            if isinstance(layer, torch.nn.ELU):
                acts.append(z)
        acts.append(z)
    acts = [a.numpy() for a in acts]
    assert [a.shape[1] for a in acts] == list(sizes)
    # units shown: evenly spaced input bins; for the other layers, the units that vary most across spectra
    idx = [np.linspace(0, sizes[0] - 1, shown[0]).astype(int)]
    idx += [np.sort(np.argsort(a.std(0))[::-1][:k]) for a, k in zip(acts[1:], shown[1:])]
    zs = [(a - a.mean(0)) / (a.std(0) + 1e-6) for a in acts]
    cmap = plt.cm.RdBu_r

    W, H, DPI = 1600, 640, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    a0 = fig.add_axes([0.02, 0.30, 0.22, 0.45])
    an = fig.add_axes([0.28, 0.08, 0.50, 0.84])
    a1 = fig.add_axes([0.82, 0.12, 0.05, 0.76])
    fig.text(0.885, 0.5, r"$h(x)$" + "\n64 features", ha="left", va="center", fontsize=20)
    for x0, x1 in [(0.245, 0.30), (0.765, 0.81)]:
        fig.add_artist(plt.matplotlib.patches.FancyArrowPatch((x0, 0.5), (x1, 0.5), transform=fig.transFigure,
                                                             arrowstyle="-|>", mutation_scale=22, lw=2, color="#555"))
    cols = [np.linspace(-0.42, 0.42, k) * (0.55 + 0.45 * k / max(shown)) for k in shown]

    def draw(i, lit):
        """Spectrum i; layers 0..lit-1 show their activations, the rest are blank. lit = len(sizes) + 1 shows h."""
        a0.cla()
        a0.plot(T.WL_OUT, X[i], "o", ms=3, color="#222")
        a0.set_xticks([])
        a0.set_yticks([])
        a0.set_title(r"Spectrum $x$ (94 bins)", fontsize=20)
        an.cla()
        an.axis("off")
        an.set_xlim(-0.5, len(sizes) - 0.5)
        an.set_ylim(-0.75, 0.5)
        for c in range(len(cols) - 1):
            col = "#999999" if c + 1 < lit else "#dddddd"
            for y0 in cols[c]:
                for y1 in cols[c + 1]:
                    an.plot([c, c + 1], [y0, y1], color=col, lw=0.6, zorder=1)
        for c, ys in enumerate(cols):
            face = cmap(0.5 + 0.25 * np.clip(zs[c][i, idx[c]], -2, 2)) if c < lit else "white"
            an.scatter(np.full(len(ys), c), ys, s=180, c=face if c < lit else "white", edgecolor="#555", lw=1.5,
                       zorder=2)
            an.text(c, -0.62, str(sizes[c]), ha="center", va="center", color="#555")
        a1.cla()
        if lit > len(sizes):
            a1.imshow(zs[-1][i][:, None], aspect="auto", cmap=cmap, vmin=-2, vmax=2)
        else:
            a1.imshow(np.zeros((sizes[-1], 1)), aspect="auto", cmap="Greys", vmin=0, vmax=1)
        a1.set_xticks([])
        a1.set_yticks([])
        for sp in a1.spines.values():
            sp.set_visible(False)

    out = encode("figures/videos/toy-embedding.mp4", W, H, FPS)

    def emit(k):
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba()).tobytes()
        for _ in range(k):
            out.stdin.write(buf)

    for i in range(len(X)):
        draw(i, 0)
        emit(int(0.4 * FPS))
        for lit in range(1, len(sizes) + 2):
            draw(i, lit)
            emit(int(0.18 * FPS))
        emit(int(1.2 * FPS))
        if i == 0:
            fig.savefig("figures/toy-embedding-arch.png", dpi=DPI)
    out.stdin.close()
    out.wait()


def embedding(params=(0, 3, 4, 5)):
    """Figure: an observed spectrum with its molecular bands, and below, for a few parameters, the sensitivity of
    the posterior mean to each wavelength bin (min-max normalized per parameter)."""
    G = np.load(OUT + "saliency.npy") if os.path.exists(OUT + "saliency.npy") else saliency()
    x = np.load(OUT + "posterior.npz")["x_obs"]
    W, H, DPI = 1600, 800, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    n = len(params)
    top = fig.add_axes([0.16, 0.62, 0.81, 0.33])
    rows = [fig.add_axes([0.16, 0.12 + (n - 1 - k) * 0.48 / n, 0.81, 0.48 / n * 0.85], sharex=top) for k in range(n)]
    bands = [(1.39, "H$_2$O"), (1.88, "H$_2$O"), (1.67, "CH$_4$"), (2.32, "CH$_4$ + CO"), (1.58, "CO")]
    for c, lab in bands:
        for ax in [top] + rows:
            ax.axvline(c, color="#cccccc", lw=1.5, zorder=0)
        top.text(c, 1.02, lab, transform=top.get_xaxis_transform(), ha="center", va="bottom", fontsize=17,
                 color="#777")
    top.errorbar(T.WL_OUT, x, yerr=SIGMA, fmt="o", ms=4, color="#222", elinewidth=1)
    top.set_ylabel("Flux")
    top.set_yticks([])
    plt.setp(top.get_xticklabels(), visible=False)
    names = {0: r"$T_{\rm int}$", 1: r"$\log g$", 2: r"[M/H]", 3: "C/O", 4: "cloud top", 5: "radius"}
    for ax, k in zip(rows, params):
        g = (G[k] - G[k].min()) / (G[k].max() - G[k].min())
        ax.fill_between(T.WL_OUT, 0, g, color=NPE_COL, alpha=0.35, lw=0, step="mid")
        ax.plot(T.WL_OUT, g, color=NPE_COL, lw=1.6, drawstyle="steps-mid")
        ax.set_ylim(0, 1.05)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.text(-0.01, 0.35, names[k], transform=ax.transAxes, ha="right", va="center")
        if ax is not rows[-1]:
            plt.setp(ax.get_xticklabels(), visible=False)
    rows[-1].set_xlabel("Wavelength [μm]")
    rows[-1].set_xlim(0.95, 2.45)
    fig.savefig("figures/toy-embedding.png", dpi=DPI)


# ------------------------------------------------------------------ prior predictive check

VEGA_JHK = (3.13e-9, 1.13e-9, 4.28e-10)  # Vega flux density in J, H, K [W m^-2 μm^-1]


def j_minus_k(f):
    """J - K colour (Vega magnitudes, approximate) from binned spectra f (n, n_bins)."""
    J = f[:, (T.WL_OUT >= 1.17) & (T.WL_OUT <= 1.33)].mean(1)
    K = f[:, (T.WL_OUT >= 2.03) & (T.WL_OUT <= 2.37)].mean(1)
    return -2.5 * np.log10(J / K) + 2.5 * np.log10(VEGA_JHK[0] / VEGA_JHK[2])


def prior_pc(n=120, n_all=3000, FPS=24, seed=3):
    """Animation: spectra simulated from the prior pile up, and a summary statistic of each (J - K colour) fills a
    histogram, against the range of known brown dwarfs and directly imaged planets. No observation: the check is
    against domain knowledge."""
    sim = T.Simulator(noisy=False, seed=seed)
    f = np.array([sim.clean(t) for t in sim.sample_prior(n_all)])
    jk = j_minus_k(f)
    print(f"J-K: median {np.median(jk):.2f}, fraction > 3: {np.mean(jk > 3):.2f}, fraction in [-1, 3]: {np.mean((jk > -1) & (jk < 3)):.2f}")
    W, H, DPI = 1600, 800, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0.08, 0.13, 0.52, 0.76])
    ah = fig.add_axes([0.69, 0.13, 0.29, 0.76])
    out = encode("figures/videos/toy-prior-pc.mp4", W, H, FPS)
    PRIOR_COL = "#5b82b5"
    bins = np.linspace(-2, 9, 45)
    KNOWN = (-1.0, 3.0)

    def frame(m, m_hist, last, hold=1):
        ax.cla()
        ah.cla()
        for k in range(m):
            ax.plot(T.WL_OUT, f[k], color=PRIOR_COL, lw=1.2, alpha=0.9 if (k == m - 1 and not last) else 0.3)
        ax.set_xlim(0.95, 2.45)
        ax.set_yscale("log")
        ax.set_ylim(1e-4, 3e2)
        ax.set_xlabel("Wavelength [μm]")
        ax.set_ylabel(r"Flux [$10^{-16}$ W m$^{-2}$ μm$^{-1}$]")
        ax.set_title(r"$f(\theta)$, $\theta \sim p(\theta)$", loc="left", fontsize=27)
        ah.axvspan(*KNOWN, color="#cccccc", alpha=0.5, lw=0)
        ah.text(np.mean(KNOWN), 0.97, "known\nobjects", transform=ah.get_xaxis_transform(), ha="center", va="top",
                color="#555")
        top = 1.0
        if m_hist:
            counts, _, _ = ah.hist(jk[:m_hist], bins=bins, color=PRIOR_COL, alpha=0.85)
            top = max(counts.max(), 3)
            if not last and m_hist <= n:
                ah.axvline(jk[m_hist - 1], color=PRIOR_COL, lw=2, ymax=0.7)
        ah.set_xlim(bins[0], bins[-1])
        ah.set_ylim(0, 1.45 * top)  # headroom for the label
        ah.set_yticks([])
        ah.spines["left"].set_visible(False)
        ah.set_xlabel(r"$J - K$ colour [mag]")
        ah.set_title("Summary statistic", loc="left", fontsize=27)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba()).tobytes()
        for _ in range(hold):
            out.stdin.write(buf)

    frame(0, 0, False, int(0.5 * FPS))
    for m in range(1, n + 1):  # slow at first, then faster
        frame(m, m, False, 4 if m <= 8 else 1)
    for m_hist in np.geomspace(n, n_all, int(1.5 * FPS)).astype(int):  # then many more draws
        frame(n, m_hist, False)
    frame(n, n_all, True, int(6 * FPS))
    fig.savefig("figures/toy-prior-pc.png", dpi=DPI)
    out.stdin.close()
    out.wait()


# ------------------------------------------------------------------ misspecification

def misspec(i=1, j=5, n_ppc=200, d=".render/data/toy-misspec/"):
    """Observation with an absorption band the simulator lacks (1.52 μm, ammonia in cool atmospheres).
    Left: NPE and MCMC posteriors, both confident, both away from θ*. Right: posterior predictive check, whose
    residuals point at the missing band. Run toy_npe.py observe and mcmc with TOY_OUT=d, X_OBS=d/xobs.npz first."""
    from scipy.ndimage import gaussian_filter
    obs = np.load(d + "xobs.npz")
    a = np.load(d + "posterior.npz")["samples"]
    m = np.load(d + "mcmc.npz")["samples"]
    x = obs["x_obs"]
    sim = T.Simulator(noisy=False)
    f = np.array([sim.clean(t) for t in a[:n_ppc]])
    med = np.median(f, 0)
    lo95, hi95 = np.percentile(f, [2.5, 97.5], axis=0)
    W, H, DPI = 1600, 720, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    ap = fig.add_axes([0.07, 0.14, 0.27, 0.74])
    asp = fig.add_axes([0.46, 0.44, 0.52, 0.44])
    ar = fig.add_axes([0.46, 0.14, 0.52, 0.22], sharex=asp)

    # posterior: contours (68, 95%) of NPE and MCMC, and the truth
    ns = np.load(d + "nested.npz")["samples"] if os.path.exists(d + "nested.npz") else None
    pts = np.vstack([a[:, [i, j]], m[:, [i, j]], T.THETA_STAR[[i, j]][None]])
    lo, hi = pts.min(0), pts.max(0)
    pad = 0.12 * (hi - lo)
    lo, hi = lo - pad, hi + pad
    runs = [(m, MCMC_COL, "MCMC")] + ([(ns, NS_COL, "nested sampling")] if ns is not None else []) + [(a, NPE_COL, "NPE")]
    for smp, col, lab in runs:
        Hh, xe, ye = np.histogram2d(smp[:, i], smp[:, j], bins=60, range=[[lo[0], hi[0]], [lo[1], hi[1]]])
        Hh = gaussian_filter(Hh, 1.3).T
        flat = np.sort(Hh.ravel())[::-1]
        cum = np.cumsum(flat) / flat.sum()
        lev = sorted(flat[np.searchsorted(cum, q)] for q in (0.95, 0.68))
        ap.contour((xe[:-1] + xe[1:]) / 2, (ye[:-1] + ye[1:]) / 2, Hh, levels=lev, colors=[col], linewidths=2.2)
        ap.plot([], [], color=col, lw=2.2, label=lab)
    ap.plot(*T.THETA_STAR[[i, j]], "*", ms=24, color=TRUE_COL, mec="white", label=r"$\theta^\star$")
    ap.set_xlim(lo[0], hi[0])
    ap.set_ylim(lo[1], hi[1])
    ap.set_xlabel(T.LABELS[i])
    ap.set_ylabel(T.LABELS[j] + r" [$R_{\rm J}$]")
    ap.legend(frameon=False, loc="upper left", fontsize=17, handlelength=1.4)
    ap.set_title("Posterior", loc="left", fontsize=27)

    # posterior predictive check
    asp.fill_between(T.WL_OUT, lo95, hi95, color=NPE_COL, alpha=0.25, lw=0)
    asp.plot(T.WL_OUT, med, color=NPE_COL, lw=2, label=r"$f(\theta)$, $\theta \sim q_\phi(\theta|x)$")
    asp.errorbar(T.WL_OUT, x, yerr=SIGMA, fmt="o", ms=4, color="#222", elinewidth=1, label=r"observed $x$")
    asp.set_ylabel("Flux")
    asp.legend(frameon=False, loc="upper right")
    asp.set_title("Posterior predictive check", loc="left", fontsize=27)
    plt.setp(asp.get_xticklabels(), visible=False)
    r = (x - med) / SIGMA
    ar.axhspan(-2, 2, color="#e6e6e6", lw=0)
    ar.axhline(0, color="#999", lw=1)
    ar.plot(T.WL_OUT, r, "o", ms=4, color="#222")
    ar.set_xlim(0.95, 2.45)
    ar.set_ylim(-7, 4)
    ar.set_yticks([-6, -3, 0, 3])
    ar.set_ylabel(r"Resid. [$\sigma$]")
    ar.set_xlabel("Wavelength [μm]")
    k = np.argsort(r)[:2]  # the two worst residuals, at the missing band
    cx, cy = T.WL_OUT[k].mean(), r[k].mean()
    from matplotlib.patches import Ellipse
    ar.add_patch(Ellipse((cx, cy), 0.09, 4.2, fill=False, ec=NPE_COL, lw=2.2, clip_on=False))
    print("NPE median", np.median(a, 0).round(2), "MCMC median", np.median(m, 0).round(2))
    print("min residual", r.min().round(1), "at", T.WL_OUT[np.argmin(r)].round(3))
    fig.savefig("figures/toy-misspec.png", dpi=DPI)

    # first build: the new observation alone, against the same planet without the band
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0.07, 0.14, 0.91, 0.74])
    c, w = float(obs["center"]), float(obs["width"])
    ax.axvspan(c - 2 * w, c + 2 * w, color="#e6e6e6", lw=0)
    ax.text(c - 2 * w - 0.015, 7.6, "ammonia band\n(not in the simulator)", ha="right", va="top", color="#555")
    ax.plot(T.WL_OUT, obs["f_clean"], "--", color="#999", lw=2, label="same planet, without the band")
    ax.errorbar(T.WL_OUT, x, yerr=SIGMA, fmt="o", ms=5, color="#222", elinewidth=1, label=r"new observation $x$")
    ax.set_xlim(0.95, 2.45)
    ax.set_ylim(-0.6, 8.4)
    ax.set_xlabel("Wavelength [μm]")
    ax.set_ylabel(r"Flux [$10^{-16}$ W m$^{-2}$ μm$^{-1}$]")
    ax.legend(frameon=False, loc="upper right")
    fig.savefig("figures/toy-misspec-obs.png", dpi=DPI)


# ------------------------------------------------------------------ observed spectrum

def xobs():
    p = np.load(OUT + "posterior.npz")
    plt.rcParams["font.size"] = 17
    fig, ax = plt.subplots(figsize=(14, 6), dpi=100)
    ax.errorbar(T.WL_OUT, p["x_obs"], yerr=SIGMA, fmt="o", ms=5, color="#222", elinewidth=1)
    ax.set_xlabel("Wavelength [μm]")
    ax.set_ylabel(r"Flux [$10^{-16}$ W m$^{-2}$ μm$^{-1}$]")
    ax.set_xlim(0.95, 2.45)
    fig.tight_layout()
    fig.savefig("figures/toy-xobs.png")


# ------------------------------------------------------------------ amortize

def amortize(n_obs=8, i=0, j=3, FPS=24, seed=11):
    model = load_model()
    sim = T.Simulator(noisy=True, seed=seed)
    rng = np.random.default_rng(seed)
    thetas = []
    while len(thetas) < n_obs:
        t = sim.sample_prior(1)[0]
        if 0.3 < sim.clean(t).mean() < 8:
            thetas.append(t)
    W, H, DPI = 1600, 700, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    axs = fig.add_axes([0.08, 0.16, 0.50, 0.72])
    axp = fig.add_axes([0.68, 0.16, 0.29, 0.72])
    p = encode("figures/videos/toy-amortize.mp4", W, H, FPS)
    for k, t in enumerate(thetas):
        x = sim(t)
        with torch.no_grad():
            s = N.from_unit(model.sample(torch.tensor(x, dtype=torch.float32), 4000).numpy())
        for fr in range(int(1.6 * FPS)):
            u = min(1.0, fr / (0.5 * FPS))
            axs.cla()
            axp.cla()
            axs.errorbar(T.WL_OUT, x, yerr=SIGMA, fmt="o", ms=4, color="#222", elinewidth=1)
            axs.set_xlim(0.95, 2.45)
            axs.set_xlabel("Wavelength [μm]")
            axs.set_ylabel("Flux")
            axs.set_title(f"New observation $x$ #{k + 1}", loc="left", fontsize=27)
            m = int(u * len(s))
            axp.scatter(s[:m, i], s[:m, j], s=5, c=NPE_COL, alpha=0.35, lw=0)
            axp.plot([t[i]], [t[j]], "*", ms=22, color=TRUE_COL, mec="white")
            axp.set_xlim(T.LOWER[i], T.UPPER[i])
            axp.set_ylim(T.LOWER[j], T.UPPER[j])
            axp.set_xlabel(T.LABELS[i] + " [K]")
            axp.set_ylabel(T.LABELS[j])
            axp.set_title(r"$q_\phi(\theta | x)$", loc="left", fontsize=27)
            fig.canvas.draw()
            p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
        if k == 0:
            fig.savefig("figures/toy-amortize.png", dpi=DPI)
    p.stdin.close()
    p.wait()


# ------------------------------------------------------------------ gallery

def gallery(n_rows=2, n_cols=5, i=0, j=3, FPS=24, seed=21, mcmc_minutes=9.0):
    """Amortization: new observations, each as a short spectrum with its 2D posterior below, filled one by one."""
    import time as _time
    model = load_model()
    sim = T.Simulator(noisy=True, seed=seed)
    n = n_rows * n_cols
    thetas = []
    while len(thetas) < n:
        t = sim.sample_prior(1)[0]
        if 0.3 < sim.clean(t).mean() < 8:
            thetas.append(t)
    xs = [sim(t) for t in thetas]
    posts, secs = [], []
    for x in xs:
        t0 = _time.time()
        with torch.no_grad():
            u = model.sample(torch.tensor(x, dtype=torch.float32), 3000).numpy()
        secs.append(_time.time() - t0)
        posts.append(N.from_unit(u))
    W, H, DPI = 1600, 1000, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    L, R, B, Tp = 0.085, 0.965, 0.13, 0.985  # left margin for the C/O labels, mirrored on the right
    cw = (R - L) / n_cols
    rh = (Tp - B) / n_rows
    spec_h, post_h, gap = 0.22 * rh, 0.60 * rh, 0.03 * rh
    pairs = []
    for k in range(n):
        r, c = divmod(k, n_cols)
        x0 = L + c * cw + 0.012
        w = cw - 0.03
        top = Tp - r * rh
        axs = fig.add_axes([x0, top - spec_h, w, spec_h])
        axp = fig.add_axes([x0, top - spec_h - gap - post_h, w, post_h])
        for ax in (axs, axp):
            for sp in ("top", "right"):
                ax.spines[sp].set_visible(False)
        axs.set_xlim(0.95, 2.45)
        axs.set_xticks([])
        axs.set_yticks([])
        axp.set_xlim(T.LOWER[i], T.UPPER[i])
        axp.set_ylim(T.LOWER[j], T.UPPER[j])
        axp.set_xticks([800, 1600])
        axp.set_yticks([0.4, 1.0])
        if c > 0:
            axp.set_yticklabels([])
        else:
            axp.set_ylabel("C/O")
        if r < n_rows - 1:
            axp.set_xticklabels([])
        else:
            axp.set_xlabel(r"$T_{\rm int}$ [K]")
        pairs.append((axs, axp))
    clock = fig.text(L + 0.012, 0.035, "", fontsize=24, va="center", ha="left")
    other = fig.text(R - 0.018, 0.035, "", fontsize=24, va="center", ha="right", color="#555")
    p = encode("figures/videos/toy-gallery.mp4", W, H, FPS)
    per = int(0.5 * FPS)
    for k in range(n):
        axs, axp = pairs[k]
        axs.plot(T.WL_OUT, xs[k], color="#222", lw=1.5)
        s_ = posts[k]
        axp.scatter(s_[:, i], s_[:, j], s=4, c=NPE_COL, alpha=0.3, lw=0)
        axp.plot([thetas[k][i]], [thetas[k][j]], "*", ms=18, color=TRUE_COL, mec="white", mew=1)
        clock.set_text(f"NPE: {sum(secs[:k + 1]):.1f} s for {k + 1} spectra")
        other.set_text(f"MCMC or nested sampling: ~{(k + 1) * mcmc_minutes:.0f} min")
        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba()).tobytes()
        for _ in range(per):
            p.stdin.write(frame)
    for _ in range(int(3 * FPS)):
        p.stdin.write(frame)
    fig.savefig("figures/toy-gallery.png", dpi=DPI)
    p.stdin.close()
    p.wait()


# ------------------------------------------------------------------ coverage

def coverage(n_test=1000, n_samples=1000, seed=5):
    """Expected coverage of the highest-density credible regions of q_φ, on test pairs from the simulator."""
    import time as _time
    model = load_model()
    sim = T.Simulator(noisy=True, seed=seed)
    th = sim.sample_prior(n_test)
    xs = np.array([sim(t) for t in th])
    t0 = _time.time()
    ranks = []
    with torch.no_grad():
        for t, x in zip(th, xs):
            c = model.embed(N.preprocess(torch.tensor(x, dtype=torch.float32)))
            d = model.flow(c)
            s_ = d.sample((n_samples,))
            lp_s = d.log_prob(s_)
            lp_t = d.log_prob(torch.tensor(N.to_unit(t), dtype=torch.float32))
            ranks.append((lp_s > lp_t).float().mean().item())  # level of the smallest HPD region containing θ*
    dt = _time.time() - t0
    ranks = np.sort(np.array(ranks))
    levels = np.linspace(0, 1, 101)
    empirical = np.array([(ranks <= a).mean() for a in levels])
    np.savez(OUT + "coverage.npz", levels=levels, empirical=empirical, seconds=dt)
    plt.rcParams["font.size"] = 17
    fig, ax = plt.subplots(figsize=(7.5, 7), dpi=100)
    ax.plot([0, 1], [0, 1], "--", color="#888", lw=2)
    ax.fill_between([0, 1], [0, 1], [1, 1], color="#2a9d8f", alpha=0.07, lw=0)
    ax.fill_between([0, 1], [0, 0], [0, 1], color=NPE_COL, alpha=0.07, lw=0)
    ax.text(0.05, 0.92, "conservative", color="#2a9d8f", fontsize=17)
    ax.text(0.62, 0.06, "overconfident", color=NPE_COL, fontsize=17)
    ax.plot(levels, empirical, color=NPE_COL, lw=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_xlabel("Credibility level")
    ax.set_ylabel("Expected coverage")
    fig.tight_layout()
    fig.savefig("figures/toy-coverage.png")
    print(f"{n_test} posteriors in {dt:.1f} s")


# ------------------------------------------------------------------ coverage animation

def coverage_anim(n_test=1000, n_samples=1000, n_rows=30, j=3, seed=5, FPS=24):
    """Left: 90% credible intervals of C/O for test cases, true value in or out. Right: expected coverage
    computed from the cases seen so far, converging to the diagonal, with the 1/2/3 sigma bands expected for a
    calibrated estimator from that many cases."""
    model = load_model()
    sim = T.Simulator(noisy=True, seed=seed)
    th = sim.sample_prior(n_test)
    ranks, lo, hi = [], [], []
    with torch.no_grad():
        for t in th:
            d = model.flow(model.embed(N.preprocess(torch.tensor(sim(t), dtype=torch.float32))))
            s_ = d.sample((n_samples,))
            ranks.append((d.log_prob(s_) > d.log_prob(torch.tensor(N.to_unit(t), dtype=torch.float32))).float().mean().item())
            cj = N.from_unit(s_.numpy())[:, j]
            lo.append(np.percentile(cj, 5))
            hi.append(np.percentile(cj, 95))
    ranks, lo, hi = np.array(ranks), np.array(lo), np.array(hi)
    inside = (th[:, j] >= lo) & (th[:, j] <= hi)
    levels = np.linspace(0, 1, 101)

    W, H, DPI = 1600, 800, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    axi = fig.add_axes([0.06, 0.14, 0.42, 0.74])
    axc = fig.add_axes([0.6, 0.14, 0.33, 0.74 * 1.0])
    GREEN = "#2a9d8f"
    # Timeline: rows appear one by one, then the count accelerates to n_test
    steps = list(range(1, n_rows + 1)) + list(np.unique(np.geomspace(n_rows, n_test, 70).astype(int)))
    p = encode("figures/videos/toy-coverage.mp4", W, H, FPS)
    for k, n in enumerate(steps):
        axi.cla()
        axc.cla()
        m = min(n, n_rows)
        for r in range(m):
            col = GREEN if inside[r] else NPE_COL
            axi.plot([lo[r], hi[r]], [r, r], color=col, lw=4, solid_capstyle="round", alpha=0.85)
            axi.plot([th[r, j]], [r], "o", color="#222", ms=7, zorder=3)
        axi.set_xlim(T.LOWER[j], T.UPPER[j])
        axi.set_ylim(n_rows - 0.5, -0.8)
        axi.set_yticks([])
        axi.spines["left"].set_visible(False)
        axi.set_xlabel("C/O")
        frac = inside[:n].mean()
        axi.set_title(f"90% credible intervals: true value inside in {inside[:n].sum()} of {n} ({100 * frac:.0f}%)",
                      loc="left", fontsize=20)
        emp = np.array([(ranks[:n] <= a).mean() for a in levels])
        axc.fill_between([0, 1], [0, 1], [1, 1], color=GREEN, alpha=0.08, lw=0)
        axc.fill_between([0, 1], [0, 0], [0, 1], color=NPE_COL, alpha=0.08, lw=0)
        # 1/2/3 sigma bands of a calibrated estimator with n cases (as in Dax et al 2026, Fig. 13): the empirical
        # coverage at level alpha is Binomial(n, alpha) / n, here in its Gaussian approximation
        sd = np.sqrt(levels * (1 - levels) / n)
        for k_sigma, a in [(3, 0.14), (2, 0.18), (1, 0.24)]:
            axc.fill_between(levels, np.clip(levels - k_sigma * sd, 0, 1), np.clip(levels + k_sigma * sd, 0, 1),
                             color="#555555", alpha=a, lw=0)
        axc.plot([0, 1], [0, 1], "--", color="#888", lw=2)
        axc.text(0.04, 0.9, "conservative", color=GREEN)
        axc.text(0.5, 0.06, "overconfident", color=NPE_COL)
        axc.plot(levels, emp, color="#222", lw=3)
        axc.plot([0.9], [inside[:n].mean() if False else emp[90]], "o", color="#222", ms=8)
        axc.set_xlim(0, 1)
        axc.set_ylim(0, 1)
        axc.set_xticks([0, 0.5, 1])
        axc.set_yticks([0, 0.5, 1])
        axc.set_xlabel("Credibility level")
        axc.set_ylabel("Expected coverage")
        axc.set_title(f"Expected coverage, {n} cases", loc="left", fontsize=20)
        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba()).tobytes()
        for _ in range(int(0.35 * FPS) if k < n_rows else 2):
            p.stdin.write(frame)
    for _ in range(int(3 * FPS)):
        p.stdin.write(frame)
    fig.savefig("figures/toy-coverage.png", dpi=DPI)
    p.stdin.close()
    p.wait()


# ------------------------------------------------------------------ importance sampling

def is_corner():
    """NPE, NPE + importance sampling, and MCMC on the benchmark; efficiency and evidence in the legend."""
    import corner
    p = np.load(OUT + "posterior.npz")
    q = np.load(OUT + "is.npz")
    m = np.load(OUT + "mcmc.npz")
    rng = np.random.default_rng(0)
    b = m["samples"][rng.choice(len(m["samples"]), 20000, replace=False)]
    a, c = p["samples"], q["samples"]
    lo = np.minimum(np.percentile(a, 0.5, 0), np.percentile(b, 0.5, 0))
    hi = np.maximum(np.percentile(a, 99.5, 0), np.percentile(b, 99.5, 0))
    rng_ = [(l - 0.1 * (h - l), h + 0.1 * (h - l)) for l, h in zip(lo, hi)]
    plt.rcParams["font.size"] = 21
    kw = dict(bins=35, smooth=1.0, plot_datapoints=False, plot_density=False, levels=(0.68, 0.95),
              range=rng_, labels=T.LABELS, label_kwargs={"fontsize": 21}, max_n_ticks=2, labelpad=0.12,
              fill_contours=False)
    IS_COL = "#1f5fae"
    fig = corner.corner(b, color=MCMC_COL, hist_kwargs={"lw": 2.2, "density": True}, **kw)
    corner.corner(a, color=NPE_COL, fig=fig, hist_kwargs={"lw": 2.2, "density": True}, **kw)
    corner.corner(c, color=IS_COL, fig=fig, hist_kwargs={"lw": 2.2, "density": True}, **kw)
    n = len(T.NAMES)
    for k in range(n):
        ax = fig.axes[k * n + k]
        ax.relim()
        ax.autoscale(axis="y")
        ax.set_ylim(0, ax.get_ylim()[1] * 1.05)
    fig.set_size_inches(12, 12)
    for ax in fig.axes:
        ax.tick_params(labelsize=21)
    ns = OUT + "nested.npz" if os.path.exists(OUT + "nested.npz") else ".render/data/toy/nested.npz"
    z = f"$\\log \\hat{{Z}} = {float(q['logz']):.2f}$"
    if os.path.exists(ns):
        z += f" (nested: {float(np.load(ns)['logz']):.2f})"
    fig.legend(handles=[plt.Line2D([], [], color=NPE_COL, lw=3, label="NPE"),
                        plt.Line2D([], [], color=IS_COL, lw=3, label=f"NPE + importance sampling"),
                        plt.Line2D([], [], color=MCMC_COL, lw=3, label="MCMC"),
                        plt.Line2D([], [], color="none", label=f"efficiency $\\varepsilon = {float(q['efficiency']):.2f}$"),
                        plt.Line2D([], [], color="none", label=z)],
               loc="upper right", bbox_to_anchor=(0.97, 0.97), frameon=False, fontsize=21, handlelength=1.5)
    fig.savefig("figures/toy-is-corner.png", dpi=100, bbox_inches="tight")


# ------------------------------------------------------------------ importance sampling, explained

def is_anim(n=3000, i=0, j=3, FPS=24, seed=4):
    """Three panels: proposal samples from q_phi; the same, sized by importance weight; resampled by weight,
    on top of the MCMC contours. Exact likelihood of the toy."""
    from multiprocessing import Pool
    from scipy.ndimage import gaussian_filter
    torch.manual_seed(seed)
    post = np.load(OUT + "posterior.npz")
    x_obs = post["x_obs"]
    model = load_model()
    with torch.no_grad():
        d = model.flow(model.embed(N.preprocess(torch.tensor(x_obs, dtype=torch.float32))))
        u = d.sample((n,))
        log_q = d.log_prob(u).double().numpy() + np.sum(np.log(2 / (T.UPPER - T.LOWER)))
    th = N.from_unit(u.numpy().astype(np.float64))
    ok = np.all((th >= T.LOWER) & (th <= T.UPPER), axis=1)
    th, log_q = th[ok], log_q[ok]
    with Pool(8, initializer=N._ns_init, initargs=(x_obs,)) as pool:
        ll = np.array(pool.map(N._ns_loglike, list(th), chunksize=100))
    log_w = ll - np.sum(np.log(T.UPPER - T.LOWER)) - log_q
    w = np.exp(log_w - log_w.max())
    eff = w.sum() ** 2 / (len(w) * (w * w).sum())
    rng = np.random.default_rng(seed)
    res = th[rng.choice(len(th), size=len(th), p=w / w.sum())] + rng.normal(0, 1e-3, (len(th), 6)) * (T.UPPER - T.LOWER)
    m = np.load(OUT + "mcmc.npz")["samples"]
    lo = np.percentile(th[:, [i, j]], 0.5, 0)
    hi = np.percentile(th[:, [i, j]], 99.5, 0)
    pad = 0.12 * (hi - lo)
    lo, hi = lo - pad, hi + pad
    H, xe, ye = np.histogram2d(m[:, i], m[:, j], bins=50, range=[[lo[0], hi[0]], [lo[1], hi[1]]])
    H = gaussian_filter(H, 1.3).T
    flat = np.sort(H.ravel())[::-1]
    cum = np.cumsum(flat) / flat.sum()
    lev = sorted(flat[np.searchsorted(cum, q)] for q in (0.95, 0.68))
    X = (xe[:-1] + xe[1:]) / 2
    Y = (ye[:-1] + ye[1:]) / 2

    W, H_, DPI = 1600, 620, 100
    plt.rcParams["font.size"] = 20
    fig = plt.figure(figsize=(W / DPI, H_ / DPI), dpi=DPI, facecolor="white")
    axes = [fig.add_axes([0.06 + k * 0.32, 0.17, 0.26, 0.67]) for k in range(3)]
    titles = [r"1. Sample $\theta_i \sim q_\phi(\theta|x)$", r"2. Weight $w_i$", "3. Resample by weight"]
    IS_COL = "#1f5fae"
    wn = w / w.max()
    p = encode("figures/videos/toy-is.mp4", W, H_, FPS)
    n_in = int(1.2 * FPS)
    stages = [(0, n_in), (1, n_in), (2, n_in)]
    shown = 0
    for stage, nf in stages:
        for f in range(nf):
            uu = (f + 1) / nf
            uu = uu * uu * (3 - 2 * uu)
            for k, ax in enumerate(axes):
                ax.cla()
                ax.set_xlim(lo[0], hi[0])
                ax.set_ylim(lo[1], hi[1])
                ax.set_xlabel(T.LABELS[i] + " [K]")
                if k == 0:
                    ax.set_ylabel("C/O")
                else:
                    ax.set_yticklabels([])
                ax.locator_params(nbins=3)
                ax.set_title(titles[k], loc="left", fontsize=21, color="#222" if k <= stage else "#ccc")
                if k > stage or (k == stage and False):
                    continue
                a = uu if k == stage else 1.0
                if k == 0:
                    ax.scatter(th[:, i], th[:, j], s=4, c=NPE_COL, alpha=0.35 * a, lw=0)
                elif k == 1:
                    ax.scatter(th[:, i], th[:, j], s=2 + 60 * wn ** 1.0, c=NPE_COL, alpha=0.35 * a, lw=0)
                else:
                    ax.contour(X, Y, H, levels=lev, colors=[MCMC_COL], linewidths=2, alpha=a)
                    ax.scatter(res[:, i], res[:, j], s=4, c=IS_COL, alpha=0.35 * a, lw=0)
            fig.canvas.draw()
            p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
    axes[2].text(0.97, 0.05, f"efficiency $\\varepsilon = {eff:.2f}$", transform=axes[2].transAxes, ha="right",
                 fontsize=19, color="#222")
    axes[2].plot([], [], color=MCMC_COL, lw=2, label="MCMC")
    axes[2].legend(frameon=False, fontsize=18, loc="upper left")
    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba()).tobytes()
    for _ in range(int(3 * FPS)):
        p.stdin.write(frame)
    fig.savefig("figures/toy-is.png", dpi=DPI)
    p.stdin.close()
    p.wait()
    print(f"efficiency {eff:.3f}")


if __name__ == "__main__":
    {"flow": flow, "loss": loss, "corner": corner_plot, "ppc": ppc, "amortize": amortize, "xobs": xobs, "prior_pc": prior_pc, "embedding": embedding, "embedding_arch": embedding_arch, "embedding_anim": embedding_anim, "saliency": saliency, "misspec": misspec, "gallery": gallery, "coverage": coverage, "coverage_anim": coverage_anim, "is_corner": is_corner, "is_anim": is_anim}[sys.argv[1]]()
