"""Animated NPE pipeline (same layout as tools/npe_architecture.py), in two passes.

Training: prior -> θ -> simulator -> x -> embedding network (layer by layer) -> h(x) conditions t1, t2, t3;
a cloud of samples travels θ -> t1 -> t2 -> t3 -> u, reshaping (density direction), then the change-of-variables
formula appears.
Inference: x_obs enters the network (pulse through the embedding); Gaussian samples travel back u -> θ
(sampling, inverse direction); the posterior corner fills in. The last frame is held.

Real data: x_obs, real posterior samples, and their images through the trained transforms.
Inputs: $TOY_OUT/npe.pt, posterior.npz. Outputs: figures/videos/npe-pipeline.mp4, figures/npe-pipeline.png.
Run with .render/venv.
"""

import os
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(__file__))
import toy_exo as T
import toy_npe as N

OUT = N.OUT
BLUE, RED, GREY = "#3b78c2", "#c0392b", "#666"
FS, FT = 19, 26
FPS = 24
plt.rcParams.update({"mathtext.fontset": "cm", "font.family": "Roboto", "font.size": FS})

post = np.load(OUT + "posterior.npz")
x_obs, samples = post["x_obs"], post["samples"]
sig = T.SIGMA_NOISE * T.Simulator.scale
I, J = 0, 3

model = N.build()
model.load_state_dict(torch.load(OUT + "npe.pt", weights_only=False)["state"])
model.eval()
with torch.no_grad():
    d = model.flow(model.embed(N.preprocess(torch.tensor(x_obs, dtype=torch.float32))))
    z = torch.tensor(N.to_unit(samples[:2500]), dtype=torch.float32)
    stages = [z.numpy()]
    for t in d.transform.transforms:
        z = t(z)
        stages.append(z.numpy())

fig = plt.figure(figsize=(16, 9.2), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16)
ax.set_ylim(0, 9.2)
ax.axis("off")

GROUPS = {}  # name -> list of (artist, base alpha)


def reg(group, *artists):
    for a in artists:
        if a is None:
            continue
        if isinstance(a, (list, tuple)):
            reg(group, *a)
            continue
        base = a.get_alpha()
        GROUPS.setdefault(group, []).append((a, 1.0 if base is None else base))
    return artists[0] if len(artists) == 1 else artists


def box(g, x, y, w, h, fc="white", ec="black", lw=1.4, r=0.15):
    return reg(g, ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                              fc=fc, ec=ec, lw=lw)))


def arrow(g, x1, y1, x2, y2, lw=1.4, color="black"):
    return reg(g, ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16, lw=lw,
                                               color=color, shrinkA=0, shrinkB=0, zorder=5)))


def line(g, xs, ys, lw=1.4, color="black"):
    return reg(g, ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="butt")[0])


def text(g, *args, **kw):
    kw.setdefault("fontsize", FS)
    return reg(g, ax.text(*args, **kw))


# ---------------------------------------------------------------- simulator and prior
box("prior", 0.3, 2.9, 2.4, 1.9)
text("prior", 1.5, 4.15, "Prior", ha="center", va="center", fontsize=FS + 2)
text("prior", 1.5, 3.5, r"$p(\theta)$", ha="center", va="center", fontsize=FS + 4)
line("theta", [2.7, 3.15], [3.85, 3.85])
text("theta", 3.45, 3.85, r"$\theta$", ha="center", va="center", fontsize=FS + 4)
line("theta", [3.45, 3.45], [4.15, 6.35])
arrow("theta", 3.45, 6.35, 2.75, 6.35)
box("sim", 0.3, 5.9, 2.4, 1.9, fc="black")
text("sim", 1.5, 7.4, "Simulator", color="white", ha="center", va="center", fontsize=FS + 2)
text("sim", 1.5, 6.85, r"$z \sim p(z|\theta)$", color="white", ha="center", va="center", fontsize=FS + 2)
text("sim", 1.5, 6.3, r"$x \sim p(x|z)$", color="white", ha="center", va="center", fontsize=FS + 2)
line("x", [2.7, 3.15], [7.2, 7.2])
text("x", 3.45, 7.2, r"$x$", ha="center", va="center", fontsize=FS + 4)
arrow("x", 3.75, 7.2, 4.25, 7.2)

# ---------------------------------------------------------------- network φ
X0, X1 = 4.3, 10.3
box("phi", X0, 0.95, X1 - X0, 7.35)
text("phi", 4.45, 8.0, r"$\phi$", va="center", fontsize=FS + 4)
text("phi", 6.9, 7.95, "Embedding network", ha="center", va="center", color=BLUE)
layers = [(94, 3), (512, 4), (256, 3), (256, 3), (64, 2)]
lx = np.linspace(5.0, 8.5, len(layers))
cy = 6.75
pos = [(xx, cy + 0.42 * (np.arange(k) - (k - 1) / 2)) for (n, k), xx in zip(layers, lx)]
for c, ((x1, y1s), (x2, y2s)) in enumerate(zip(pos[:-1], pos[1:])):
    for y1 in y1s:
        for y2 in y2s:
            line(f"L{c + 1}", [x1, x2], [y1, y2], lw=0.7, color="#555")
NEURONS = []
for c, ((xx, ys), (n, k)) in enumerate(zip(pos, layers)):
    col = []
    for y in ys:
        circ = ax.add_patch(plt.Circle((xx, y), 0.15, fc="white", ec="#bbb", lw=2, zorder=3))
        reg(f"L{c}", circ)
        col.append(circ)
    NEURONS.append(col)
    text(f"L{c}", xx, 5.6, str(n), ha="center", va="center", color=GREY)
line("h", [8.7, 9.15], [cy, cy], color=BLUE)
text("h", 9.65, cy, r"$h(x)$", ha="center", va="center", color=BLUE, fontsize=FS + 2)
tx = [5.6, 7.3, 9.0]
line("cond", [9.65, 9.65], [cy - 0.35, 5.05], color=BLUE)
line("cond", [tx[0], 9.65], [5.05, 5.05], color=BLUE)
for k, xx in enumerate(tx):
    arrow("cond", xx, 5.05, xx, 4.3, color=BLUE)
    box("tbox", xx - 0.5, 3.45, 1.0, 0.8, r=0.12)
    text("tbox", xx, 3.85, f"$t_{k + 1}$", ha="center", va="center", fontsize=FS + 4)
    if k < 2:
        arrow("tbox", xx + 0.55, 3.85, tx[k + 1] - 0.55, 3.85)
arrow("theta_in", 3.75, 3.85, 5.05, 3.85)

# Insets: normalized sample positions of each stage
ix = [4.95, 6.45, 8.15, 9.7]
sz, Y0 = 1.0, 1.95
NORM = []
for k, zz in enumerate(stages):
    p = zz[:, [I, J]]
    c = np.median(p, 0)
    h = 1.15 * np.max(np.percentile(np.abs(p - c), 99, 0))
    NORM.append((p - c) / h)
keep = np.all(np.concatenate([np.abs(q) < 0.97 for q in NORM], axis=1), axis=1)
NORM = [q[keep] for q in NORM]
INSET_COL = [RED, "#999", "#999", "#555"]
for k, (xc, q) in enumerate(zip(ix, NORM)):
    reg(f"inset{k}", ax.add_patch(plt.Rectangle((xc - sz / 2, Y0), sz, sz, fill=False, lw=1.0, ec="#999")))
    reg(f"inset{k}", ax.scatter(xc + q[:, 0] * sz / 2, Y0 + sz / 2 + q[:, 1] * sz / 2, s=2.0, lw=0,
                                c=INSET_COL[k], alpha=0.5, zorder=4))
text("inset0", ix[0], 1.62, r"$\theta$", ha="center", va="center", fontsize=FS + 2)
text("inset3", ix[3], 1.62, r"$u$", ha="center", va="center", fontsize=FS + 2)
text("flowlabel", 7.3, 1.62, "Normalizing flow", ha="center", va="center")
text("density", 7.3, 1.25, r"$q_\phi(\theta|x) = \mathcal{N}(t_3 \circ t_2 \circ t_1(\theta);\, 0, I)\, |\det J|$",
     ha="center", va="center", color=RED, fontsize=FS + 1)
CLOUD = ax.scatter([], [], s=4.0, lw=0, zorder=6)

# ---------------------------------------------------------------- observed spectrum
sx0, sy0, sw, sh = 10.85, 6.35, 3.9, 1.7
ymin, ymax = -0.8, 9.5
def px(w): return sx0 + (w - 0.95) / 1.5 * sw
def py(v): return sy0 + (v - ymin) / (ymax - ymin) * sh
eb = ax.errorbar(px(T.WL_OUT), py(x_obs), yerr=sig / (ymax - ymin) * sh, fmt="o", ms=2.6, color="black", elinewidth=0.7)
reg("xobs", *[a for a in eb.get_children()])
text("xobs", sx0 + sw + 0.15, sy0 + sh - 0.1, r"$x_{\rm obs}$", va="center", fontsize=FS + 4)
line("xobs", [sx0, sx0 + sw], [sy0 - 0.05, sy0 - 0.05], lw=1.0, color=GREY)
for w in (1.0, 1.5, 2.0):
    line("xobs", [px(w), px(w)], [sy0 - 0.05, sy0 - 0.14], lw=1.0, color=GREY)
    text("xobs", px(w), sy0 - 0.4, f"{w:.1f}", ha="center", va="center", color=GREY)
text("xobs", sx0 + sw / 2, sy0 - 0.85, "wavelength [μm]", ha="center", va="center", color=GREY)
arrow("xobs_in", 10.75, 7.2, 10.35, 7.2)

# ---------------------------------------------------------------- posterior corner
a_, b_ = samples[:, I], samples[:, J]
cx0, cy0, s = 11.4, 1.45, 1.6
lo_a, hi_a = np.percentile(a_, [0.5, 99.5])
lo_b, hi_b = np.percentile(b_, [0.5, 99.5])
pa, pb = 0.15 * (hi_a - lo_a), 0.15 * (hi_b - lo_b)
lo_a, hi_a, lo_b, hi_b = lo_a - pa, hi_a + pa, lo_b - pb, hi_b + pb
for (x0, y0) in [(cx0, cy0 + s), (cx0, cy0), (cx0 + s, cy0)]:
    reg("corner", ax.add_patch(plt.Rectangle((x0, y0), s, s, fill=False, lw=1.2)))
for vals, lo, hi, (x0, y0) in [(a_, lo_a, hi_a, (cx0, cy0 + s)), (b_, lo_b, hi_b, (cx0 + s, cy0))]:
    hg, edges = np.histogram(vals, bins=60, range=(lo, hi), density=True)
    hg = gaussian_filter(hg, 1.5)
    c = (edges[:-1] + edges[1:]) / 2
    reg("corner", ax.plot(x0 + (c - lo) / (hi - lo) * s, y0 + 0.05 + 0.85 * s * hg / hg.max(), color=BLUE, lw=2)[0])
H2, _, _ = np.histogram2d(a_, b_, bins=60, range=[[lo_a, hi_a], [lo_b, hi_b]])
H2 = gaussian_filter(H2, 1.5).T
flat = np.sort(H2.ravel())[::-1]
cum = np.cumsum(flat) / flat.sum()
levels = [flat[np.searchsorted(cum, q)] for q in (0.95, 0.68, 0.3)]
X = cx0 + (np.arange(60) + 0.5) / 60 * s
Y = cy0 + (np.arange(60) + 0.5) / 60 * s
reg("corner", ax.contourf(X, Y, H2, levels=levels + [H2.max() + 1], colors=["#d7e5f5", "#a9c8ea", "#7aa8dc"]))
reg("corner", ax.contour(X, Y, H2, levels=levels, colors=[BLUE], linewidths=1.3))
text("corner", cx0 + s / 2, cy0 - 0.35, r"$T_{\rm int}$", ha="center", va="center", fontsize=FS + 2)
text("corner", cx0 + 1.5 * s, cy0 - 0.35, "C/O", ha="center", va="center")
text("corner", cx0 - 0.3, cy0 + s / 2, "C/O", ha="center", va="center", rotation=90)
arrow("corner_in", 10.35, 3.0, 11.3, 3.0)


def bracket(g, x1, x2, y, up, label):
    dd = 0.22 if up else -0.22
    line(g, [x1, x1, x2, x2], [y - dd, y, y, y - dd], lw=1.4)
    text(g, (x1 + x2) / 2, y + (0.32 if up else -0.36), label, ha="center", va="center", fontsize=FT)


bracket("train", 0.15, 10.45, 8.65, True, "Training")
bracket("infer", 4.15, 15.75, 0.6, False, "Inference")

# ---------------------------------------------------------------- timeline (seconds)
FADE = {  # group: (start, end) of the fade-in
    "train": (0.0, 0.5), "prior": (0.3, 0.8), "theta": (0.8, 1.3), "sim": (1.3, 1.8), "x": (1.8, 2.3),
    "phi": (2.3, 2.8), "L0": (2.8, 3.1), "L1": (3.1, 3.4), "L2": (3.4, 3.7), "L3": (3.7, 4.0), "L4": (4.0, 4.3),
    "h": (4.3, 4.6), "cond": (4.6, 5.0), "tbox": (4.9, 5.4), "theta_in": (5.4, 5.8), "inset0": (5.8, 6.2),
    "flowlabel": (5.8, 6.2),
    "inset1": (7.2, 7.5), "inset2": (8.2, 8.5), "inset3": (9.2, 9.5), "density": (9.6, 10.2),
    "infer": (11.2, 11.7), "xobs": (11.6, 12.2), "xobs_in": (12.2, 12.6),
    "corner_in": (16.6, 17.0), "corner": (16.9, 17.8),
}
FORWARD = [(6.3, 7.3), (7.3, 8.3), (8.3, 9.3)]   # θ -> t1 -> t2 -> u, one segment per transform
PULSE = (12.6, 13.6)                            # x_obs through the embedding
BACKWARD = [(13.8, 14.6), (14.6, 15.4), (15.4, 16.2)]  # u -> t3^-1 -> t2^-1 -> θ
END, HOLD = 18.0, 3.0


def smooth(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def set_alpha(group, a):
    for art, base in GROUPS.get(group, []):
        art.set_alpha(base * a)


def cloud_at(seg_list, tau, forward):
    for k, (t0, t1) in enumerate(seg_list):
        if t0 <= tau < t1:
            u = smooth((tau - t0) / (t1 - t0))
            a, b = (k, k + 1) if forward else (3 - k, 2 - k)
            q = (1 - u) * NORM[a] + u * NORM[b]
            xc = (1 - u) * ix[a] + u * ix[b]
            if forward:
                col = mcolors.to_rgb(RED) if a == 0 and u < 0.5 else mcolors.to_rgb("#555")
            else:
                col = mcolors.to_rgb(BLUE)
            return np.c_[xc + q[:, 0] * sz / 2, Y0 + sz / 2 + q[:, 1] * sz / 2], col
    return None, None


ffmpeg = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1600x920",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "22", "-preset", "slow",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "figures/videos/npe-pipeline.mp4"],
                          stdin=subprocess.PIPE)
n_frames = int((END + HOLD) * FPS)
white = np.array(mcolors.to_rgb("white"))
light = np.array(mcolors.to_rgb("#a9c8ea"))
for f in range(n_frames):
    tau = min(f / FPS, END)
    for g in GROUPS:
        if g in FADE:
            t0, t1 = FADE[g]
            set_alpha(g, smooth((tau - t0) / (t1 - t0)))
        else:
            set_alpha(g, 1.0)
    # Pulse through the embedding (inference): columns light up in turn, then fade
    for c, col in enumerate(NEURONS):
        center = PULSE[0] + (c + 0.5) / len(NEURONS) * (PULSE[1] - PULSE[0])
        w = np.exp(-0.5 * ((tau - center) / 0.12) ** 2)
        for circ in col:
            circ.set_facecolor(tuple((1 - w) * white + w * light))
    # Moving cloud
    xy, col = cloud_at(FORWARD, tau, True)
    if xy is None:
        xy, col = cloud_at(BACKWARD, tau, False)
    if xy is None:
        CLOUD.set_offsets(np.empty((0, 2)))
    else:
        CLOUD.set_offsets(xy)
        CLOUD.set_color(col)
        CLOUD.set_alpha(0.7)
    fig.canvas.draw()
    ffmpeg.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
ffmpeg.stdin.close()
ffmpeg.wait()
fig.savefig("figures/npe-pipeline.png", dpi=100)
