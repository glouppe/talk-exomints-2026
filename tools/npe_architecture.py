"""NPE pipeline figure for the toy problem, in the spirit of Fig. 1 of Vasist et al (2023).

Training (top bracket): prior p(θ) and simulator p(x|θ) produce pairs (θ, x) that train the network φ:
an embedding MLP (94-512-256-256-64) reading x, and a flow t_3 ∘ t_2 ∘ t_1 conditioned on its output h(x).
Under the flow, posterior samples for x_obs are pushed through t_1, t_2, t_3 (real samples, real trained layers),
in the (T_int, C/O) plane: the posterior becomes u ~ N(0, I), a change of variables with tractable density
q_φ(θ|x) = N(t_3 ∘ t_2 ∘ t_1(θ); 0, I) |det J|.
Inference (bottom bracket): x_obs through the same network gives the posterior, as a small corner plot.

Font sizes: the SVG is 16 in wide and shown ~897 px wide on the slide, so 19 pt text appears ~15 px, the size
used in the simulator walk-through.

Inputs: $TOY_OUT/npe.pt and posterior.npz. Output: figures/npe-architecture.svg (+ .render/shots preview).
Run with .render/venv (torch, zuko, scipy).
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
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
FS, FT = 19, 26  # text, titles
plt.rcParams.update({"mathtext.fontset": "cm", "font.family": "Roboto", "font.size": FS})

post = np.load(OUT + "posterior.npz")
x_obs, samples = post["x_obs"], post["samples"]
sig = T.SIGMA_NOISE * T.Simulator.scale
I, J = 0, 3  # T_int, C/O

# Posterior samples pushed through the trained transforms (density direction θ -> u)
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


def box(x, y, w, h, fc="white", ec="black", lw=1.4, r=0.15):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))


def arrow(x1, y1, x2, y2, lw=1.4, color="black"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16, lw=lw, color=color,
                                 shrinkA=0, shrinkB=0, zorder=5))


def line(xs, ys, lw=1.4, color="black"):
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="butt")


# ---------------------------------------------------------------- simulator and prior
box(0.3, 5.9, 2.4, 1.9, fc="black")
ax.text(1.5, 7.4, "Simulator", color="white", ha="center", va="center", fontsize=FS + 2)
ax.text(1.5, 6.85, r"$z \sim p(z|\theta)$", color="white", ha="center", va="center", fontsize=FS + 2)
ax.text(1.5, 6.3, r"$x \sim p(x|z)$", color="white", ha="center", va="center", fontsize=FS + 2)
box(0.3, 2.9, 2.4, 1.9)
ax.text(1.5, 4.15, "Prior", ha="center", va="center", fontsize=FS + 2)
ax.text(1.5, 3.5, r"$p(\theta)$", ha="center", va="center", fontsize=FS + 4)
line([2.7, 3.15], [3.85, 3.85])
ax.text(3.45, 3.85, r"$\theta$", ha="center", va="center", fontsize=FS + 4)
arrow(3.75, 3.85, 5.05, 3.85)  # θ into the flow (t_1)
line([3.45, 3.45], [4.15, 6.35])
arrow(3.45, 6.35, 2.75, 6.35)  # θ into the simulator
line([2.7, 3.15], [7.2, 7.2])
ax.text(3.45, 7.2, r"$x$", ha="center", va="center", fontsize=FS + 4)
arrow(3.75, 7.2, 4.25, 7.2)

# ---------------------------------------------------------------- network φ
X0, X1 = 4.3, 10.3
box(X0, 0.95, X1 - X0, 7.35)
ax.text(4.45, 8.0, r"$\phi$", va="center", fontsize=FS + 4)
ax.text(6.9, 7.95, "Embedding network", ha="center", va="center", color=BLUE, fontsize=FS)
layers = [(94, 3), (512, 4), (256, 3), (256, 3), (64, 2)]
lx = np.linspace(5.0, 8.5, len(layers))
cy = 6.75
pos = []
for (n, k), xx in zip(layers, lx):
    pos.append((xx, cy + 0.42 * (np.arange(k) - (k - 1) / 2)))
for (x1, y1s), (x2, y2s) in zip(pos[:-1], pos[1:]):
    for y1 in y1s:
        for y2 in y2s:
            line([x1, x2], [y1, y2], lw=0.7, color="#555")
for (xx, ys), (n, k) in zip(pos, layers):
    for y in ys:
        ax.add_patch(plt.Circle((xx, y), 0.15, fc="white", ec="#bbb", lw=2, zorder=3))
    ax.text(xx, 5.6, str(n), ha="center", va="center", color=GREY, fontsize=FS)
line([8.7, 9.15], [cy, cy], color=BLUE)
ax.text(9.65, cy, r"$h(x)$", ha="center", va="center", color=BLUE, fontsize=FS + 2)
# Conditioning h(x) -> t_k
tx = [5.6, 7.3, 9.0]
line([9.65, 9.65], [cy - 0.35, 5.05], color=BLUE)
line([tx[0], 9.65], [5.05, 5.05], color=BLUE)
for k, xx in enumerate(tx):
    arrow(xx, 5.05, xx, 4.3, color=BLUE)
    box(xx - 0.5, 3.45, 1.0, 0.8, r=0.12)
    ax.text(xx, 3.85, f"$t_{k + 1}$", ha="center", va="center", fontsize=FS + 4)
    if k < 2:
        arrow(xx + 0.55, 3.85, tx[k + 1] - 0.55, 3.85)

# Samples through the flow: θ, after t1, after t2, after t3 = u
ix = [4.95, 6.45, 8.15, 9.7]
sz = 1.0
for k, (xc, zz) in enumerate(zip(ix, stages)):
    p = zz[:, [I, J]]
    c = np.median(p, 0)
    h = 1.15 * np.max(np.percentile(np.abs(p - c), 99, 0))
    q = (p - c) / h
    q = q[np.all(np.abs(q) < 0.97, axis=1)]  # keep the points inside the frame
    x0, y0 = xc - sz / 2, 1.95
    ax.add_patch(plt.Rectangle((x0, y0), sz, sz, fill=False, lw=1.0, ec="#999"))
    ax.scatter(xc + q[:, 0] * sz / 2, y0 + sz / 2 + q[:, 1] * sz / 2, s=2.0, lw=0,
               c=RED if k == 0 else ("#555" if k == 3 else "#999"), alpha=0.5, zorder=4)
ax.text(ix[0], 1.62, r"$\theta$", ha="center", va="center", fontsize=FS + 2)
ax.text(ix[3], 1.62, r"$u$", ha="center", va="center", fontsize=FS + 2)
ax.text(7.3, 1.62, "Normalizing flow", ha="center", va="center", fontsize=FS)
ax.text(7.3, 1.25, r"$q_\phi(\theta|x) = \mathcal{N}(t_3 \circ t_2 \circ t_1(\theta);\, 0, I)\, |\det J|$",
        ha="center", va="center", color=RED, fontsize=FS + 1)

# ---------------------------------------------------------------- observed spectrum (inference input)
sx0, sy0, sw, sh = 10.85, 6.35, 3.9, 1.7
ymin, ymax = -0.8, 9.5
def px(w): return sx0 + (w - 0.95) / 1.5 * sw
def py(v): return sy0 + (v - ymin) / (ymax - ymin) * sh
ax.errorbar(px(T.WL_OUT), py(x_obs), yerr=sig / (ymax - ymin) * sh, fmt="o", ms=2.6, color="black", elinewidth=0.7)
ax.text(sx0 + sw + 0.15, sy0 + sh - 0.1, r"$x_{\rm obs}$", va="center", fontsize=FS + 4)
line([sx0, sx0 + sw], [sy0 - 0.05, sy0 - 0.05], lw=1.0, color=GREY)
for w in (1.0, 1.5, 2.0):
    line([px(w), px(w)], [sy0 - 0.05, sy0 - 0.14], lw=1.0, color=GREY)
    ax.text(px(w), sy0 - 0.4, f"{w:.1f}", ha="center", va="center", color=GREY, fontsize=FS)
ax.text(sx0 + sw / 2, sy0 - 0.85, "wavelength [μm]", ha="center", va="center", color=GREY, fontsize=FS)
arrow(10.75, 7.2, 10.35, 7.2)

# ---------------------------------------------------------------- posterior corner (inference output)
a, b = samples[:, I], samples[:, J]
cx0, cy0, s = 11.4, 1.45, 1.6
lo_a, hi_a = np.percentile(a, [0.5, 99.5])
lo_b, hi_b = np.percentile(b, [0.5, 99.5])
pa, pb = 0.15 * (hi_a - lo_a), 0.15 * (hi_b - lo_b)
lo_a, hi_a, lo_b, hi_b = lo_a - pa, hi_a + pa, lo_b - pb, hi_b + pb
for (x0, y0) in [(cx0, cy0 + s), (cx0, cy0), (cx0 + s, cy0)]:
    ax.add_patch(plt.Rectangle((x0, y0), s, s, fill=False, lw=1.2))
for vals, lo, hi, (x0, y0) in [(a, lo_a, hi_a, (cx0, cy0 + s)), (b, lo_b, hi_b, (cx0 + s, cy0))]:
    hg, edges = np.histogram(vals, bins=60, range=(lo, hi), density=True)
    hg = gaussian_filter(hg, 1.5)
    c = (edges[:-1] + edges[1:]) / 2
    ax.plot(x0 + (c - lo) / (hi - lo) * s, y0 + 0.05 + 0.85 * s * hg / hg.max(), color=BLUE, lw=2)
H2, _, _ = np.histogram2d(a, b, bins=60, range=[[lo_a, hi_a], [lo_b, hi_b]])
H2 = gaussian_filter(H2, 1.5).T
flat = np.sort(H2.ravel())[::-1]
cum = np.cumsum(flat) / flat.sum()
levels = [flat[np.searchsorted(cum, q)] for q in (0.95, 0.68, 0.3)]
X = cx0 + (np.arange(60) + 0.5) / 60 * s
Y = cy0 + (np.arange(60) + 0.5) / 60 * s
ax.contourf(X, Y, H2, levels=levels + [H2.max() + 1], colors=["#d7e5f5", "#a9c8ea", "#7aa8dc"])
ax.contour(X, Y, H2, levels=levels, colors=[BLUE], linewidths=1.3)
ax.text(cx0 + s / 2, cy0 - 0.35, r"$T_{\rm int}$", ha="center", va="center", fontsize=FS + 2)
ax.text(cx0 + 1.5 * s, cy0 - 0.35, "C/O", ha="center", va="center", fontsize=FS)
ax.text(cx0 - 0.3, cy0 + s / 2, "C/O", ha="center", va="center", rotation=90, fontsize=FS)
arrow(10.35, 3.0, 11.3, 3.0)


# ---------------------------------------------------------------- brackets
def bracket(x1, x2, y, up, label):
    d = 0.22 if up else -0.22
    line([x1, x1, x2, x2], [y - d, y, y, y - d], lw=1.4)
    ax.text((x1 + x2) / 2, y + (0.32 if up else -0.36), label, ha="center", va="center", fontsize=FT)


bracket(0.15, 10.45, 8.65, True, "Training")
bracket(4.15, 15.75, 0.6, False, "Inference")

fig.savefig("figures/npe-architecture.svg")
fig.savefig(".render/shots/npe-architecture.png", dpi=70)
