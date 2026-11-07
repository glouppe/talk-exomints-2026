"""Animated walk through the toy simulator: θ -> z -> f(θ) -> x.

The parameters morph smoothly between a few prior draws. Four builds are rendered on the same timeline,
revealing one stage at a time:
    1: θ only, 2: θ and z, 3: θ, z and f(θ), 4: θ, z, f(θ) and x.

Outputs: figures/videos/toy-walk-{1,2,3,4}.mp4 and figures/toy-walk-{1,2,3,4}.png (posters).

Usage: python tools/toy_walkthrough.py [--quick]
"""

import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, "tools")
import toy_exo as T

FPS = 24
HOLD, MORPH = 1.0, 0.9  # seconds
W, H, DPI = 1600, 800, 100
COL = {"theta": "#1f5fae", "T": "#d1495b", "H2O": "#1f77b4", "CH4": "#2a9d8f", "CO": "#e9a23b",
       "f": "#222222", "x": "#d1495b", "cloud": "#b8bec9"}

plt.rcParams.update({"font.size": 20, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.labelcolor": "#333", "xtick.color": "#555", "ytick.color": "#555"})


def draws(n, seed=3):
    """Prior draws with a visible spectrum (for the animation only)."""
    sim = T.Simulator(noisy=False, seed=seed)
    out = [T.THETA_STAR]
    while len(out) < n:
        th = sim.sample_prior(1)[0]
        m = sim.clean(th).mean()
        if 0.3 < m < 8:
            out.append(th)
    return np.array(out)


def timeline(thetas):
    """Per-frame θ: hold each draw, then morph (smoothstep) to the next; loops back to the first."""
    frames = []
    n_hold, n_morph = int(HOLD * FPS), int(MORPH * FPS)
    for i in range(len(thetas)):
        a, b = thetas[i], thetas[(i + 1) % len(thetas)]
        frames += [a] * n_hold
        for k in range(n_morph):
            u = (k + 1) / (n_morph + 1)
            u = u * u * (3 - 2 * u)
            frames.append(a + u * (b - a))
    return np.array(frames)


def setup(stage):
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
    ax_th = fig.add_axes([0.02, 0.14, 0.18, 0.72])
    ax_T = fig.add_axes([0.315, 0.14, 0.13, 0.72])
    ax_X = fig.add_axes([0.47, 0.14, 0.11, 0.72], sharey=ax_T)
    ax_f = fig.add_axes([0.715, 0.14, 0.265, 0.72])
    titles = [(0.02, r"Parameters $\theta$", 1), (0.27, r"Latent state $z$", 2), (0.665, r"Spectrum", 3)]
    for x0, t, s in titles:
        fig.text(x0, 0.92, t, fontsize=27, color="#222" if stage >= s else "#ccc", ha="left", va="bottom")
    # Arrows between columns
    for x0, s in [(0.225, 2), (0.612, 3)]:
        fig.text(x0, 0.5, "→", fontsize=48, color="#222" if stage >= s else "#ddd", ha="center", va="center")
    return fig, ax_th, ax_T, ax_X, ax_f


def draw(fig, axes, theta, stage, sim, rng, ymax):
    ax_th, ax_T, ax_X, ax_f = axes
    for ax in (ax_th, ax_T, ax_X, ax_f):
        ax.cla()
    # θ: one slider per parameter
    u = (theta - T.LOWER) / (T.UPPER - T.LOWER)
    names = [l + (f" [{un}]" if un else "") for l, un in zip(T.LABELS, T.UNITS)]
    for i in range(6):
        y = 5 - i
        ax_th.plot([0, 1], [y, y], color="#ddd", lw=6, solid_capstyle="round")
        ax_th.plot([0, u[i]], [y, y], color=COL["theta"], lw=6, solid_capstyle="round")
        ax_th.plot([u[i]], [y], "o", color=COL["theta"], ms=13)
        ax_th.text(0, y + 0.38, names[i], fontsize=19, color="#333")
        val = f"{theta[i]:.0f}" if i == 0 else f"{theta[i]:.2f}"
        ax_th.text(1, y + 0.38, val, fontsize=19, color="#333", ha="right")
    ax_th.set_xlim(-0.05, 1.05)
    ax_th.set_ylim(-0.6, 6.0)
    ax_th.axis("off")

    z = T.latent(theta)
    if stage >= 2:
        ax_T.axhspan(z["P_cloud"], T.P.max(), color=COL["cloud"], alpha=0.5, lw=0)
        ax_T.text(2950, min(z["P_cloud"] * 1.6, 60), "cloud", color="#777", fontsize=17, ha="right", va="top")
        ax_T.plot(z["T"], T.P, color=COL["T"], lw=3)
        for s in ["H2O", "CH4", "CO"]:
            ax_X.plot(z["X"][s], T.P, color=COL[s], lw=3, label=s.replace("2", "₂").replace("4", "₄"))
        ax_X.legend(frameon=False, fontsize=17, loc="lower left", handlelength=1.2)
    ax_T.set_yscale("log")
    ax_T.set_ylim(T.P.max(), T.P.min())
    ax_T.set_xlim(500, 3000)
    ax_T.set_xticks([1000, 2000, 3000])
    ax_T.set_xticklabels(["1000", "2000", "3000"], fontsize=16)
    ax_T.set_xlabel("Temperature [K]")
    ax_T.set_ylabel("Pressure [bar]")
    ax_X.set_xscale("log")
    ax_X.set_xlim(1e-7, 3e-2)
    ax_X.set_xticks([1e-6, 1e-3])
    ax_X.set_xlabel("Abundance")
    plt.setp(ax_X.get_yticklabels(), visible=False)
    for ax in (ax_T, ax_X):
        if stage < 2:
            for s in ax.spines.values():
                s.set_color("#e5e5e5")
            ax.tick_params(colors="#ddd")
            ax.xaxis.label.set_color("#ccc")
            ax.yaxis.label.set_color("#ccc")

    if stage >= 3:
        f = sim.clean(theta)
        ax_f.plot(T.WL_OUT, f, color=COL["f"], lw=2.5, label=r"$f(\theta)$")
        if stage >= 4:
            x = f + T.SIGMA_NOISE * T.Simulator.scale * rng.standard_normal(f.shape)
            ax_f.errorbar(T.WL_OUT, x, yerr=T.SIGMA_NOISE * T.Simulator.scale, fmt="o", ms=4, color=COL["x"],
                          elinewidth=1, alpha=0.8, label=r"$x$ (with noise)")
        ax_f.legend(frameon=False, fontsize=18, loc="upper right")
    ax_f.set_xlim(0.95, 2.45)
    ax_f.set_xticks([1.0, 1.5, 2.0])
    ax_f.set_ylim(-0.1 * ymax, ymax)
    ax_f.set_xlabel("Wavelength [μm]")
    ax_f.set_ylabel(r"Flux [$10^{-16}$ W m$^{-2}$ μm$^{-1}$]")
    ax_f.yaxis.set_label_coords(-0.14, 0.5)  # fixed, whatever the tick labels
    if stage < 3:
        for s in ax_f.spines.values():
            s.set_color("#e5e5e5")
        ax_f.tick_params(colors="#ddd")
        ax_f.xaxis.label.set_color("#ccc")
        ax_f.yaxis.label.set_color("#ccc")


def render(stage, thetas, out_mp4, out_png):
    sim = T.Simulator(noisy=False)
    rng = np.random.default_rng(0)
    # Smooth autoscale of the flux axis
    peaks = np.array([sim.clean(t).max() for t in thetas])
    smooth = peaks[0]
    fig, *axes = setup(stage)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, th in enumerate(thetas):
        target = 1.25 * peaks[k] if stage >= 3 else 6.0
        smooth = target if k == 0 else smooth + 0.15 * (target - smooth)
        draw(fig, axes, th, stage, sim, rng, max(smooth, 0.5))
        fig.canvas.draw()
        p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
        if k == 0:
            fig.savefig(out_png, dpi=DPI, facecolor="white")
    p.stdin.close()
    p.wait()
    plt.close(fig)


def render_ppc(out_mp4, out_png, n_draws=24, hold=0.35, morph=0.45):
    """Posterior predictive check: the walk-through driven by posterior draws, over the observed spectrum.

    Each draw's spectrum is shown in red; past draws stay as faint traces, building the predictive band."""
    import os
    d = np.load(os.environ.get("TOY_OUT", ".render/data/toy/") + "posterior.npz")
    x_obs, post = d["x_obs"], d["samples"]
    draws_ = post[np.random.default_rng(1).choice(len(post), n_draws, replace=False)]
    n_hold, n_morph = int(hold * FPS), int(morph * FPS)
    frames, keys = [], []
    for i in range(n_draws):
        a, b = draws_[i], draws_[(i + 1) % n_draws]
        frames += [a] * n_hold
        keys += [True] + [False] * (n_hold - 1)
        for k in range(n_morph):
            u = (k + 1) / (n_morph + 1)
            u = u * u * (3 - 2 * u)
            frames.append(a + u * (b - a))
            keys.append(False)
    sim = T.Simulator(noisy=False)
    rng = np.random.default_rng(0)
    sig = T.SIGMA_NOISE * T.Simulator.scale
    ymax = 1.25 * x_obs.max()
    fig, *axes = setup(3)
    ax_f = axes[3]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    trail = []
    for th, key in zip(frames, keys):
        if key:
            trail.append(sim.clean(th))
        draw(fig, axes, th, 3, sim, rng, ymax)
        ax_f.get_legend().remove()
        for f in trail[-40:]:
            ax_f.plot(T.WL_OUT, f, color=COL["x"], lw=1.2, alpha=0.18)
        ax_f.lines[0].set_color(COL["x"])
        ax_f.errorbar(T.WL_OUT, x_obs, yerr=sig, fmt="o", ms=4, color="#222", elinewidth=1, zorder=5)
        ax_f.legend(handles=[plt.Line2D([], [], color=COL["x"], lw=2.5, label=r"$f(\theta)$, $\theta \sim q_\phi(\theta | x_{\rm obs})$"),
                             plt.Line2D([], [], color="#222", marker="o", lw=0, label=r"$x_{\rm obs}$")],
                    frameon=False, fontsize=18, loc="upper right")
        fig.canvas.draw()
        p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
    fig.savefig(out_png, dpi=DPI, facecolor="white")  # last frame: the full band
    p.stdin.close()
    p.wait()
    plt.close(fig)


if __name__ == "__main__":
    if "--ppc" in sys.argv:
        render_ppc("figures/videos/toy-ppc.mp4", "figures/toy-ppc.png")
        sys.exit()
    quick = "--quick" in sys.argv
    thetas = timeline(draws(3 if quick else 8))
    stages = [4] if quick else [1, 2, 3, 4]
    for s in stages:
        out = ".render/data/toy-walk-quick" if quick else f"figures/videos/toy-walk-{s}"
        png = ".render/shots/toy-walk-quick.png" if quick else f"figures/toy-walk-{s}.png"
        render(s, thetas, out + ".mp4", png)
