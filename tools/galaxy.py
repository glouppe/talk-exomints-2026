"""A galaxy of Bayesian inference algorithms, with simulation-based inference on its arms.

Six spiral arms, one per family: three classical (MCMC & co., nested sampling, ABC) and three of
simulation-based inference (posterior, likelihood and ratio estimation), longer and denser. Dust drifts along the
arms; named algorithms twinkle as labelled stars.

Builds:
    1: the galaxy (loops),
    2: same, then everything dims except NPE, which grows and glows (plays once, holds).

Outputs: figures/videos/galaxy-{1,2}.mp4, figures/galaxy-{1,2}.jpg (posters).
Usage: python tools/galaxy.py [--quick]
"""

import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.transforms
import numpy as np

plt.rcParams["font.family"] = "Roboto"
FAMILY_FONT = {"family": "Lato", "weight": "normal", "style": "italic"}

W, H, DPI = 1920, 1440, 100
FPS = 24
BG = "#03050b"

# Families: (name, colour, arm length in turns, algorithms along the arm from the core outwards)
FAMILIES = [
    ("MCMC & co.", "#9ec5ff", 0.70, ["Metropolis–Hastings", "Gibbs", "HMC", "NUTS", "slice sampling",
                                     "parallel tempering", "emcee", "SMC", "importance sampling", "variational inference"]),
    ("Neural posterior\nestimation", "#ff8fc7", 1.0, ["SNPE-A", "SNPE-B", "APT", "NPE", "TSNPE", "RNPE", "BNPE",
                                                     "GNPE", "DINGO", "DINGO-IS", "FMPE", "BayesFlow", "JANA",
                                                     "SA-ABI", "self-consistency loss", "GATSBI", "CMPE", "NPSE",
                                                     "Simformer"]),
    ("Nested sampling", "#b9d7ff", 0.62, ["nested sampling", "MultiNest", "PolyChord", "dynesty", "UltraNest", "nautilus"]),
    ("Neural likelihood\nestimation", "#ffa8d8", 0.80, ["NLE", "SNLE", "MNLE", "SNVI", "SNPLA", "SCANDAL",
                                                       "emulator + MCMC"]),
    ("ABC", "#d6e6ff", 0.70, ["rejection ABC", "regression ABC", "ABC-MCMC", "ABC-SMC", "semi-automatic ABC",
                              "K2-ABC", "BOLFI", "synthetic likelihood"]),
    ("Neural ratio\nestimation", "#ff9ccf", 1.0, ["CARL", "ROLR", "RASCAL", "CASCAL", "SALLY", "ALICES", "LFIRE",
                                                 "NRE", "NRE-B", "NRE-C", "BNRE", "AMNRE", "MNRE", "TMNRE", "ANRE"]),
]
HIGHLIGHT = ("NPE", "FMPE")
# Hand nudges (in data units) for the few labels that would otherwise collide
NUDGE = {}

R0, R1, WIND = 0.10, 2.0, np.deg2rad(235)
INCL, ROT = 0.68, np.deg2rad(-14)  # disk seen at ~50° (cos i = 0.62), major axis rotated by -18°


def project(xy):
    """Face-on disk coordinates -> tilted view: squash along y, then rotate."""
    x, y = xy[..., 0], INCL * xy[..., 1]
    c, s_ = np.cos(ROT), np.sin(ROT)
    return np.stack([c * x - s_ * y, s_ * x + c * y], -1)  # radius grows linearly along an arm; winding of a full-length arm


def arm_xy(k, t, length):
    """Point at fraction t ∈ [0, 1] along arm k; `length` ∈ (0, 1.25] scales how far the arm reaches."""
    u = t * length
    r = R0 + (R1 - R0) * u
    a = k * 2 * np.pi / len(FAMILIES) + WIND * u
    return np.stack([r * np.cos(a), r * np.sin(a)], -1)  # face-on; tilted by project()


def dust(rng, n_per_turn=9000):
    pts = []
    for k, (_, col, turns, _) in enumerate(FAMILIES):
        n = int(n_per_turn * turns)
        t0 = rng.random(n)
        width = 0.025 + 0.035 * t0
        off = rng.standard_normal((n, 2)) * width[:, None]
        pts.append((k, t0, off, col, turns))
    return pts


def label_positions():
    out = []
    for k, (fam, col, turns, algos) in enumerate(FAMILIES):
        n = len(algos)
        for i, name in enumerate(algos):
            t = 0.20 + 0.79 * (i + 0.5) / n
            p = project(arm_xy(k, np.array(t), turns))
            out.append((name, p, col, k))
        p_tip = arm_xy(k, np.array(1.0), turns)
        p_end = project(p_tip * (1 + 0.24 / np.linalg.norm(p_tip)))  # beyond the tip, radially
        out.append((fam, p_end, col, -1 - k))  # family name at the end of the arm
    return out


def place_labels(fig, ax, labels):
    """Greedy placement: for each label, the first candidate position whose box overlaps no placed box."""
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    placed, out = [], {}
    # Star points are obstacles too
    for name, pos, col, k in labels:
        if k >= 0:
            x, y = ax.transData.transform(pos)
            placed.append(matplotlib.transforms.Bbox([[x - 5, y - 5], [x + 5, y + 5]]))
    order = sorted(range(len(labels)), key=lambda i: (labels[i][3] >= 0, np.linalg.norm(labels[i][1])))
    for i in order:
        name, pos, col, k = labels[i]
        family = k < 0
        txt = name.replace("\n", " ") if (family and len(name) < 16) else name
        kw = dict(fontsize=22, linespacing=1.0, **FAMILY_FONT) if family else dict(fontsize=14, fontweight="light")
        o = pos / np.linalg.norm(pos)
        perp = np.array([-o[1], o[0]])
        cands = [(pos, "center", "center")] if family else []
        for d in ([0.0, 0.08, 0.16, -0.08, 0.24] if family else [0.045, 0.08, 0.12]):
            for v in ([o] if family else [o, o + 0.8 * perp, o - 0.8 * perp, -o]):
                v = v / np.linalg.norm(v)
                q = pos + d * v
                cands.append((q, "center", "center") if family else
                             (q, "left" if v[0] >= 0 else "right", "bottom" if v[1] >= 0 else "top"))
        best = None
        for q, ha, va in cands:
            t = ax.text(q[0], q[1], txt, ha=ha, va=va, **kw)
            bb = t.get_window_extent(ren).expanded(1.08, 1.15)
            t.remove()
            if all(not bb.overlaps(b) for b in placed):
                best = (q, ha, va, bb)
                break
        if best is None:
            q, ha, va = cands[0]
            t = ax.text(q[0], q[1], txt, ha=ha, va=va, **kw)
            best = (q, ha, va, t.get_window_extent(ren))
            t.remove()
        placed.append(best[3])
        out[i] = best[:3]
    return out


def render(build, out_mp4, out_poster, seconds):
    rng = np.random.default_rng(0)
    dust_arms = dust(rng)
    labels = label_positions()
    # Bulge: a dense cloud of warm stars, denser towards the centre
    rad = np.abs(rng.standard_normal(14000)) * 0.13 * (1 + 0.6 * rng.random(14000))
    ang = rng.random(14000) * 2 * np.pi
    core = project(np.stack([rad * np.cos(ang), rad * np.sin(ang)], -1))
    core_col = np.where(rng.random(14000) < 0.7, "#ffe9c4", "#fff8ee")
    # Soft radial glow (RGBA image), no hard edges
    gx = np.linspace(-0.7, 0.7, 401)
    GX, GY = np.meshgrid(gx, gx)
    c, s_ = np.cos(ROT), np.sin(ROT)
    FX, FY = c * GX + s_ * GY, (-s_ * GX + c * GY) / INCL  # inverse of project()
    rr = np.hypot(FX, FY)
    glow = np.zeros(rr.shape + (4,))
    glow[..., :3] = matplotlib.colors.to_rgb("#ffe6bf")
    glow[..., 3] = 0.55 * np.exp(-(rr / 0.07) ** 2) + 0.28 * np.exp(-(rr / 0.18) ** 2) + 0.10 * np.exp(-(rr / 0.40) ** 2)

    allxy = np.concatenate([project(arm_xy(k, t0, turns) + off) for k, t0, off, _, turns in dust_arms]
                           + [np.array([lab[1] for lab in labels])])
    lo, hi = np.percentile(allxy, 0.2, axis=0), np.percentile(allxy, 99.8, axis=0)
    lo, hi = np.minimum(lo, allxy[-len(labels):].min(0)), np.maximum(hi, allxy[-len(labels):].max(0))
    cx, cy = (lo + hi) / 2
    half_w = max((hi[0] - lo[0]) / 2 + 0.45, (hi[1] - lo[1]) / 2 * 4 / 3 + 0.35)  # room for label text
    half_w *= 0.92  # fill the frame; the tip of the lower arm may sit under the caption box
    half_h = half_w * 3 / 4

    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
    lim = 1.78
    n_frames = int(seconds * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "22", "-preset", "slow", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    phases = rng.random(len(labels)) * 2 * np.pi
    ax.set_xlim(cx - half_w, cx + half_w)
    ax.set_ylim(cy - half_h, cy + half_h)
    ax.axis("off")
    placement = place_labels(fig, ax, labels)
    for f in range(n_frames):
        tau = f / FPS
        ax.cla()
        ax.set_facecolor(BG)
        ax.set_xlim(cx - half_w, cx + half_w)
        ax.set_ylim(cy - half_h, cy + half_h)
        ax.axis("off")
        # Highlight progress (build 2): 0 for 1 s, then ease in over 2 s
        hl = 0.0 if build == 1 else float(np.clip((tau - 1.0) / 2.0, 0, 1))
        hl = hl * hl * (3 - 2 * hl)
        dim = 1 - 0.75 * hl

        # Core glow
        g = glow.copy()
        g[..., 3] *= dim
        ax.imshow(g, extent=[-0.7, 0.7, -0.7, 0.7], origin="lower", interpolation="bilinear", zorder=0)
        ax.scatter(core[:, 0], core[:, 1], s=1.4, c=core_col, alpha=0.35 * dim, lw=0)

        # Dust drifting outward along the arms (periodic, faded near the ends so the loop is seamless)
        for k, t0, off, col, turns in dust_arms:
            t = (t0 + 0.02 * tau) % 1.0
            xy = project(arm_xy(k, t, turns) + off)
            fade = np.sin(np.pi * t) ** 0.7
            ax.scatter(xy[:, 0], xy[:, 1], s=1.6 * (0.4 + fade), c=col, alpha=0.32 * dim, lw=0)

        # Labelled stars
        for idx, ((name, pos, col, k), ph) in enumerate(zip(labels, phases)):
            is_family = k < 0
            lp, ha, va = placement[idx]
            if is_family:
                ax.text(lp[0], lp[1], name.replace("\n", " ") if len(name) < 16 else name, color=col,
                        fontsize=22, alpha=0.9 * dim, ha=ha, va=va, linespacing=1.0, **FAMILY_FONT)
                continue
            tw = 0.75 + 0.25 * np.sin(2 * np.pi * 0.35 * tau + ph)
            star = name in HIGHLIGHT
            a = (0.95 * tw) * (1.0 if star else dim)
            size = 26 * tw * (1 + (2.8 if star else 0) * hl)
            if star and hl > 0:
                for rad, al in [(0.16, 0.10), (0.10, 0.18), (0.06, 0.30)]:
                    ax.add_patch(plt.Circle(pos, rad * (0.5 + hl), color=col, alpha=al * hl, lw=0))
            ax.scatter([pos[0]], [pos[1]], s=size, c="white", alpha=a, lw=0)
            ax.scatter([pos[0]], [pos[1]], s=size * 4, c=col, alpha=0.25 * a, lw=0)
            fs = 14 * (1 + (1.9 if star else 0) * hl)
            ax.text(lp[0], lp[1], name, color="white", fontsize=fs, alpha=1.0 if star else min(1, a + 0.05),
                    ha=ha, va=va,
                    fontweight="medium" if star and hl > 0.3 else "light")
        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba())
        p.stdin.write(frame.tobytes())
        if f == (0 if build == 1 else n_frames - 1):
            plt.imsave(out_poster, frame[..., :3])
    p.stdin.close()
    p.wait()
    plt.close(fig)


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    if quick:
        render(2, ".render/data/galaxy-quick.mp4", ".render/shots/galaxy-quick.jpg", 4)
    else:
        render(1, "figures/videos/galaxy-1.mp4", "figures/galaxy-1.jpg", 12)
        render(2, "figures/videos/galaxy-2.mp4", "figures/galaxy-2.jpg", 5)
