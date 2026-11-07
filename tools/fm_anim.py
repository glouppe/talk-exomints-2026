"""Animation: a continuous normalizing flow, as learned by flow matching.

Target: an empirical, non-Gaussian 2D distribution (a crescent and a small second mode). With straight paths
θ_t = (1 - t) θ_0 + t θ_1, θ_0 ~ N(0, I), the flow-matching optimum is the marginal vector field
v_t(θ) = E[θ_1 - θ_0 | θ_t = θ] = Σ_j w_j(θ, t) (θ_1^j - θ) / (1 - t),  w_j ∝ N((θ - t θ_1^j) / (1 - t); 0, I),
computed here exactly over the target samples. Samples are moved by integrating dθ/dt = v_t(θ).
Grey arrows: v_t on a grid. Points coloured by their initial angle, to follow them.

Outputs: figures/videos/fm-flow.mp4, figures/fm-flow.png. Usage: python tools/fm_anim.py
"""

import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(0)
W, H, DPI, FPS = 1500, 900, 100, 24
plt.rcParams.update({"font.size": 22, "font.family": "Roboto", "mathtext.fontset": "cm"})

# Target: a crescent (banana) and a small second mode
n_t = 2500
phi = rng.uniform(0.15 * np.pi, 0.95 * np.pi, n_t)
crescent = np.c_[1.9 * np.cos(phi), 1.9 * np.sin(phi) - 0.9] + 0.18 * rng.standard_normal((n_t, 2))
blob = np.c_[0.0, -1.35] + 0.22 * rng.standard_normal((n_t // 4, 2))
target = np.vstack([crescent, blob])


def field(x, t):
    """Exact marginal flow-matching vector field at points x (n, 2), time t."""
    s = 1.0 - t
    x0 = (x[:, None, :] - t * target[None, :, :]) / s          # implied noise for each target point
    logw = -0.5 * np.sum(x0 * x0, axis=-1)
    logw -= logw.max(axis=1, keepdims=True)
    w = np.exp(logw)
    w /= w.sum(axis=1, keepdims=True)
    return np.einsum("nj,njd->nd", w, (target[None, :, :] - x[:, None, :]) / s)


n = 2500
x = rng.standard_normal((n, 2))
colors = plt.cm.hsv((np.arctan2(x[:, 1], x[:, 0]) + np.pi) / (2 * np.pi))
gx, gy = np.meshgrid(np.linspace(-3.2, 3.2, 21), np.linspace(-2.6, 2.6, 17))
grid = np.c_[gx.ravel(), gy.ravel()]

T_FLOW, T_HOLD0, T_HOLD1, T_BACK = 4.5, 0.8, 1.5, 1.2
ts = np.linspace(0, 0.985, int(T_FLOW * FPS))
traj = [x.copy()]
for k in range(len(ts) - 1):
    dt = ts[k + 1] - ts[k]
    x = x + dt * field(x, ts[k])  # Euler
    traj.append(x.copy())
traj = np.array(traj)

fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
ax = fig.add_axes([0.0, 0.0, 1.0, 0.88])
ax_t = fig.add_axes([0.3, 0.9, 0.4, 0.06])


def draw(pts, t, show_field=True):
    ax.cla()
    ax.set_xlim(-3.4, 3.4)
    ax.set_ylim(-2.75, 2.25)
    ax.set_aspect("equal")
    ax.axis("off")
    if show_field and t < 0.985:
        v = field(grid, t)
        norm = np.linalg.norm(v, axis=1, keepdims=True)
        v = v / np.maximum(norm, 1e-9) * np.minimum(norm, 2.5) * 0.09
        ax.quiver(grid[:, 0], grid[:, 1], v[:, 0], v[:, 1], color="#9a9a9a", angles="xy", scale_units="xy",
                  scale=1, width=0.003, headwidth=4, headlength=4.5, zorder=1)
    ax.scatter(pts[:, 0], pts[:, 1], s=14, c=colors, lw=0, alpha=0.75, zorder=2)
    ax_t.cla()
    ax_t.set_xlim(0, 1)
    ax_t.set_ylim(0, 1)
    ax_t.axis("off")
    ax_t.add_patch(plt.Rectangle((0, 0.35), 1, 0.3, color="#ddd", lw=0))
    ax_t.add_patch(plt.Rectangle((0, 0.35), t / 0.985, 0.3, color="#555", lw=0))
    # shown ~556 px wide out of 1500: 40 pt -> ~15 px on screen
    ax_t.text(-0.04, 0.5, r"$t = 0$", ha="right", va="center", fontsize=40)
    ax_t.text(1.04, 0.5, r"$t = 1$", ha="left", va="center", fontsize=40)


proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "22", "-preset", "slow",
                         "-pix_fmt", "yuv420p", "-movflags", "+faststart", "figures/videos/fm-flow.mp4"],
                        stdin=subprocess.PIPE)


def emit(times=1):
    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba()).tobytes()
    for _ in range(times):
        proc.stdin.write(frame)


draw(traj[0], 0.0)
emit(int(T_HOLD0 * FPS))
for k, t in enumerate(ts):
    draw(traj[k], t)
    emit()
draw(traj[-1], 0.985, show_field=False)
emit(int(T_HOLD1 * FPS))
fig.savefig("figures/fm-flow.png", dpi=DPI)
# Return to the start (fast, reversed), so the loop is seamless
back = np.linspace(len(ts) - 1, 0, int(T_BACK * FPS)).astype(int)
for k in back:
    draw(traj[k], ts[k], show_field=False)
    emit()
proc.stdin.close()
proc.wait()
