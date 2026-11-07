"""Same equations, different parameters: beta-plane turbulence at three viscosities.

Barotropic vorticity equation on a doubly periodic beta-plane, pseudo-spectral, 2/3 dealiasing,
RK4 time stepping:
    dq/dt + J(psi, q) + beta dpsi/dx = f - mu q + nu lap q,   q = lap psi,
with a stochastic forcing f at wavenumber k_f (white in time) and linear bottom drag mu.
Only the viscosity nu changes between the three runs; the forcing realisation is shared.

Field shown: current speed |u|.
Output: figures/videos/ocean-theta.mp4 (three panels side by side, 4:3 canvas, top band left
free for the caption box), figures/ocean-theta-poster.jpg.

Usage: python tools/ocean_theta.py [--quick]
"""

import subprocess
import sys

import matplotlib
import matplotlib.colors
import matplotlib.font_manager
import numpy as np
from PIL import Image, ImageDraw, ImageFont

N = 256
L = 2 * np.pi
BETA, MU = 8.0, 0.08
NUS = [1e-2, 1e-3, 1e-4]
LABELS = ["ν = 10⁻²", "ν = 10⁻³", "ν = 10⁻⁴"]
KF, DKF, EPS = 10.0, 1.5, 1e-1  # forcing ring and energy injection rate
DT = 4e-3
W, H = 1280, 960
FPS = 24


def grid():
    k = np.fft.fftfreq(N, d=L / N / (2 * np.pi))
    kx, ky = np.meshgrid(np.fft.rfftfreq(N, d=L / N / (2 * np.pi)), k)
    k2 = kx ** 2 + ky ** 2
    k2i = np.where(k2 == 0, 0, 1 / np.where(k2 == 0, 1, k2))
    kmax = N / 2
    dealias = (np.abs(kx) < 2 / 3 * kmax) & (np.abs(ky) < 2 / 3 * kmax)
    return kx, ky, k2, k2i, dealias


KX, KY, K2, K2I, DEALIAS = grid()
FMASK = (np.sqrt(K2) > KF - DKF) & (np.sqrt(K2) < KF + DKF)


def rhs(qh, nu):
    psih = -qh * K2I
    u = np.fft.irfft2(-1j * KY * psih)
    v = np.fft.irfft2(1j * KX * psih)
    qx = np.fft.irfft2(1j * KX * qh)
    qy = np.fft.irfft2(1j * KY * qh)
    adv = np.fft.rfft2(u * qx + v * qy) * DEALIAS
    return -adv - BETA * 1j * KX * psih - MU * qh - nu * K2 * qh


def forcing(rng):
    # White-in-time forcing on a ring, normalised to inject ~EPS (per unit time, applied as sqrt(dt) kicks).
    phase = np.exp(2j * np.pi * rng.random(KX.shape))
    fh = FMASK * phase
    e = 0.5 * np.sum(np.abs(fh) ** 2 * K2I) / (N ** 4)
    return fh * np.sqrt(EPS / max(e, 1e-30))


def run(nu, n_spin, n_frames, every, seed=0):
    rng = np.random.default_rng(seed)
    qh = np.zeros(KX.shape, complex)
    frames = []
    for step in range(n_spin + n_frames * every):
        k1 = rhs(qh, nu)
        k2 = rhs(qh + 0.5 * DT * k1, nu)
        k3 = rhs(qh + 0.5 * DT * k2, nu)
        k4 = rhs(qh + DT * k3, nu)
        qh = qh + DT / 6 * (k1 + 2 * k2 + 2 * k3 + k4) + np.sqrt(DT) * forcing(rng)
        if step >= n_spin and (step - n_spin) % every == 0:
            psih = -qh * K2I
            u = np.fft.irfft2(-1j * KY * psih)
            v = np.fft.irfft2(1j * KX * psih)
            frames.append(np.hypot(u, v))  # current speed
    return frames


def render(all_frames, out_mp4, out_poster):
    # Blue palette, from deep navy (still water) to near white (fast currents).
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "ocean_blue", ["#020817", "#0a2a66", "#1f5fae", "#5fa3e0", "#e6f3ff"])
    scales = [np.percentile(np.abs(np.stack(f)), 99) for f in all_frames]
    size, gap = 380, 30
    x0 = (W - 3 * size - 2 * gap) // 2
    y0 = 380
    font = ImageFont.truetype(matplotlib.font_manager.findfont("DejaVu Sans"), 30)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "22", "-preset", "slow",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    poster = None
    for t in range(len(all_frames[0])):
        canvas = Image.new("RGB", (W, H), (5, 7, 13))
        draw = ImageDraw.Draw(canvas)
        for i, frames in enumerate(all_frames):
            q = np.clip(frames[t] / scales[i], 0, 1) ** 0.8
            rgb = (cmap(q)[..., :3] * 255).astype(np.uint8)
            tile = Image.fromarray(rgb).resize((size, size), Image.Resampling.BICUBIC)
            x = x0 + i * (size + gap)
            canvas.paste(tile, (x, y0))
            tw = draw.textlength(LABELS[i], font=font)
            draw.text((x + (size - tw) / 2, y0 + size + 18), LABELS[i], fill=(220, 225, 235), font=font)
        if poster is None:
            poster = canvas.copy()
        p.stdin.write(canvas.tobytes())
    p.stdin.close()
    p.wait()
    poster.save(out_poster, quality=90)


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    n_spin, n_frames, every = (10000, 4, 5) if quick else (10000, 192, 6)
    all_frames = [run(nu, n_spin, n_frames, every) for nu in NUS]
    suffix = "-quick" if quick else ""
    render(all_frames, f".render/data/ocean-theta{suffix}.mp4" if quick else "figures/videos/ocean-theta.mp4",
           f".render/data/ocean-theta{suffix}.jpg" if quick else "figures/ocean-theta-poster.jpg")
