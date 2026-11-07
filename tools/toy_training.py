"""Animation: building the training set, then training NPE on it.

Left: spectra f(θ_i) are added one by one, then faster and faster (coloured by T_int), with a counter.
Right: then the loss curve (training and validation) is drawn epoch by epoch.
1600 x 700 px, shown ~852 px wide on the slide: 20 pt labels, 27 pt titles (as the simulator walk-through).

Inputs: $TOY_OUT/pairs.npz, $TOY_OUT/npe.pt. Outputs: figures/videos/toy-training.mp4, figures/toy-training.png.
Run with .render/venv (torch to read the checkpoint).
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

OUT = os.environ.get("TOY_OUT", ".render/data/toy/")
plt.rcParams.update({"font.size": 20, "axes.spines.top": False, "axes.spines.right": False, "font.family": "Roboto"})
W, H, DPI, FPS = 1600, 700, 100, 24
N_SPEC, T_DATA, T_LOSS, T_HOLD = 300, 6.0, 6.0, 2.5
NPE_COL = "#d1495b"

d = np.load(OUT + "pairs.npz")
th, f = d["theta"][:N_SPEC], d["f"][:N_SPEC]
n_total = len(d["theta"])
log = np.array(torch.load(OUT + "npe.pt", weights_only=False)["log"])
cmap = matplotlib.colormaps["plasma"]
norm = matplotlib.colors.Normalize(T.LOWER[0], T.UPPER[0])

fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
axd = fig.add_axes([0.08, 0.15, 0.48, 0.72])
axl = fig.add_axes([0.67, 0.15, 0.31, 0.72])
axd.set_yscale("log")
axd.set_ylim(1e-3, 3e2)
axd.set_xlim(0.95, 2.45)
axd.set_xlabel("Wavelength [μm]")
axd.set_ylabel("Flux")
axd.set_title("Simulated pairs", loc="left", fontsize=27)
lines = [axd.plot(T.WL_OUT, fi, color=cmap(norm(t[0])), lw=0.9, alpha=0.0)[0] for t, fi in zip(th, f)]
counter = axd.text(0.02, 0.97, "", transform=axd.transAxes, fontsize=22, va="top")
ep = np.arange(1, len(log) + 1)
axl.set_xlim(0, len(log) + 1)
lo, hi = log.min(), np.percentile(log, 98)
axl.set_ylim(lo - 0.08 * (hi - lo), hi + 0.08 * (hi - lo))
axl.set_xlabel("Epoch")
axl.set_ylabel("Loss")
axl.set_title("Training", loc="left", fontsize=27)
l_tr, = axl.plot([], [], color="#888", lw=2.5, label="training")
l_va, = axl.plot([], [], color=NPE_COL, lw=2.5, label="validation")
dot, = axl.plot([], [], "o", color=NPE_COL, ms=9)
axl.legend(frameon=False, fontsize=18, loc="upper right")

n1, n2, n3 = int(T_DATA * FPS), int(T_LOSS * FPS), int(T_HOLD * FPS)
counts = np.maximum(1, np.round(N_SPEC * (np.arange(1, n1 + 1) / n1) ** 2.2)).astype(int)
arrival = np.full(N_SPEC, -1)
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
       "-i", "-", "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-pix_fmt", "yuv420p",
       "-movflags", "+faststart", "figures/videos/toy-training.mp4"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for k in range(n1 + n2 + n3):
    c = counts[min(k, n1 - 1)]
    for i in range(c):
        if arrival[i] < 0:
            arrival[i] = k
    for i, ln in enumerate(lines):
        if arrival[i] >= 0:
            fresh = np.exp(-(k - arrival[i]) / 6)
            ln.set_alpha(0.55 + 0.45 * fresh)
            ln.set_linewidth(0.9 + 2.6 * fresh)
    shown = c if k < n1 else n_total
    counter.set_text(f"{shown:,} pairs " + r"$(\theta_i, x_i)$" if k >= n1 else f"{shown} pairs " + r"$(\theta_i, x_i)$")
    if k >= n1:
        m = min(len(log), int(np.ceil(len(log) * (k - n1 + 1) / n2)))
        l_tr.set_data(ep[:m], log[:m, 0])
        l_va.set_data(ep[:m], log[:m, 1])
        dot.set_data([ep[m - 1]], [log[m - 1, 1]])
    fig.canvas.draw()
    p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
p.stdin.close()
p.wait()
fig.savefig("figures/toy-training.png", dpi=DPI, facecolor="white")
