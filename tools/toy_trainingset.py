"""Animation: building a training set of (θ, f(θ)) pairs from the toy simulator.

Spectra are added one by one, then faster and faster, each drawn bright when it arrives and fading into the fan,
coloured by T_int; a counter shows the number of pairs. The last frame is held.
(The noise is added on the fly during training, so clean spectra are shown.)

Input: .render/data/toy/pairs.npz (python tools/toy_npe.py simulate).
Outputs: figures/videos/toy-trainingset.mp4, figures/toy-trainingset.png (last frame, poster).
"""

import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, "tools")
import toy_exo as T

plt.rcParams.update({"font.size": 20, "axes.spines.top": False, "axes.spines.right": False})

N, FPS, SECONDS, HOLD = 300, 24, 7.0, 2.0
W, H, DPI = 1600, 700, 100

d = np.load(".render/data/toy/pairs.npz")
th, f = d["theta"][:N], d["f"][:N]
cmap = matplotlib.colormaps["plasma"]
norm = matplotlib.colors.Normalize(T.LOWER[0], T.UPPER[0])

# Number of spectra shown at each frame: slow start, then accelerating (quadratic).
n_frames = int(SECONDS * FPS)
counts = np.maximum(1, np.round(N * (np.arange(1, n_frames + 1) / n_frames) ** 2.2)).astype(int)
counts = np.concatenate([counts, np.full(int(HOLD * FPS), N)])

fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
ax = fig.add_axes([0.09, 0.15, 0.80, 0.80])
cax = fig.add_axes([0.905, 0.15, 0.015, 0.80])
cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm, cmap), cax=cax)
cb.set_label(r"$T_{\rm int}$ [K]")
cb.outline.set_visible(False)
ax.set_yscale("log")
ax.set_ylim(1e-3, 3e2)
ax.set_xlim(0.95, 2.45)
ax.set_xlabel("Wavelength [μm]")
ax.set_ylabel(r"Flux [$10^{-16}$ W m$^{-2}$ μm$^{-1}$]")
lines = [ax.plot(T.WL_OUT, fi, color=cmap(norm(t[0])), lw=0.9, alpha=0.0)[0] for t, fi in zip(th, f)]
label = ax.text(0.015, 0.97, "", transform=ax.transAxes, fontsize=24, va="top", color="#222")

cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
       "-i", "-", "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-pix_fmt", "yuv420p",
       "-movflags", "+faststart", "figures/videos/toy-trainingset.mp4"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
arrival = np.full(N, -1)
for k, c in enumerate(counts):
    for i in range(c):
        if arrival[i] < 0:
            arrival[i] = k
    for i, ln in enumerate(lines):
        if arrival[i] < 0:
            continue
        age = k - arrival[i]
        fresh = np.exp(-age / 6)  # bright and thick when new, then settles into the fan
        ln.set_alpha(0.55 + 0.45 * fresh)
        ln.set_linewidth(0.9 + 2.6 * fresh)
    label.set_text(f"{c} simulated pairs " + r"$(\theta_i, x_i)$")
    fig.canvas.draw()
    p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
p.stdin.close()
p.wait()
fig.savefig("figures/toy-trainingset.png", dpi=DPI, facecolor="white")
