"""Animated time-frequency map of GW150914 (LIGO Hanford), revealed from left to right.

Whitened strain from GWOSC, Morlet wavelet transform (constant Q) between 20 and 512 Hz,
rendered full-bleed on a 4:3 canvas, with the whitened and band-passed strain time series
overlaid in the lower part, and encoded with ffmpeg.

Input: .render/data/H-H1_GWOSC_4KHZ_R1-1126259447-32.hdf5 (gwosc.org, not tracked).
Outputs: figures/videos/gw-x.mp4, figures/gw-x-poster.jpg (last frame).

Usage: python tools/gw_spectrogram.py
"""

import subprocess

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import signal

DATA = ".render/data/H-H1_GWOSC_4KHZ_R1-1126259447-32.hdf5"
T_MERGER = 1126259462.422
FS = 4096
W, H = 1280, 960
FPS, T_REVEAL, T_HOLD = 30, 5.0, 2.5
T0, T1 = -0.9, 0.15  # window around the merger [s]


def whiten(s):
    f, psd = signal.welch(s, FS, nperseg=4 * FS)
    S = np.fft.rfft(s * signal.windows.tukey(len(s), 0.1))
    freqs = np.fft.rfftfreq(len(s), 1 / FS)
    S /= np.sqrt(np.interp(freqs, f, psd))
    return np.fft.irfft(S, n=len(s))


def morlet_power(x, freqs, q=8.0):
    n = len(x)
    X = np.fft.fft(x)
    nu = np.fft.fftfreq(n, 1 / FS)
    out = np.empty((len(freqs), n))
    for i, f0 in enumerate(freqs):
        sigma_f = f0 / q
        G = np.exp(-0.5 * ((nu - f0) / sigma_f) ** 2)  # analytic Morlet in the frequency domain
        out[i] = np.abs(np.fft.ifft(X * G)) ** 2
    return out / np.median(out, axis=1, keepdims=True)


def trace_layer(t, x):
    """RGBA layer (H, W, 4) with the strain drawn as a glowing white line in the lower part."""
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.patch.set_alpha(0)
    y = x / np.abs(x).max()
    for lw, a in [(14, 0.06), (8, 0.12), (4.5, 0.25)]:
        ax.plot(t, y, color="#9fd3ff", lw=lw, alpha=a, solid_capstyle="round")
    ax.plot(t, y, color="white", lw=2.2)
    ax.set_xlim(T0, T1)
    ax.set_ylim(-2.6, 9.2)  # trace centred at 22% from the bottom, about 17% of the height
    ax.axis("off")
    fig.canvas.draw()
    layer = np.asarray(fig.canvas.buffer_rgba()).astype(float) / 255.0
    plt.close(fig)
    return layer


def main():
    with h5py.File(DATA) as f:
        s = f["strain/Strain"][()]
        t0 = f["meta/GPSstart"][()]
    t = t0 + np.arange(len(s)) / FS - T_MERGER
    w = whiten(s)
    freqs = np.geomspace(20, 512, 300)
    P = morlet_power(w, freqs)
    m = (t >= T0) & (t <= T1)
    P = P[:, m]
    b, a = signal.butter(4, [35, 350], btype="band", fs=FS)
    layer = trace_layer(t[m], signal.filtfilt(b, a, w)[m])
    l_rgb, l_a = layer[..., :3], layer[..., 3:]

    # Colour map, high frequencies on top, upsampled to the canvas.
    P = np.clip(P / 40.0, 0, 1) ** 0.7
    rgb = matplotlib.colormaps["magma"](P[::-1])[..., :3]
    img = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BICUBIC)) / 255.0
    dim = img * 0.12

    n_reveal, n_hold = int(FPS * T_REVEAL), int(FPS * T_HOLD)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "24", "-preset", "slow",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "figures/videos/gw-x.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cols = np.arange(W)
    for k in range(n_reveal + n_hold):
        c = W * min(1.0, (k + 1) / n_reveal)
        a = np.clip((c - cols) / 6.0, 0, 1)[None, :, None]  # soft edge
        frame = img * a + dim * (1 - a)
        la = l_a * a
        frame = frame * (1 - la) + l_rgb * la
        if k < n_reveal:  # bright cursor
            frame = frame + 0.5 * np.exp(-0.5 * ((cols - c) / 2.5) ** 2)[None, :, None]
        p.stdin.write((np.clip(frame, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    poster = img * (1 - l_a) + l_rgb * l_a
    Image.fromarray((np.clip(poster, 0, 1) * 255).astype(np.uint8)).save("figures/gw-x-poster.jpg", quality=90)


if __name__ == "__main__":
    main()
