"""Full-bleed figures for the gravitational-wave example (GW150914).

x: whitened, band-passed strain from LIGO Hanford and Livingston (GWOSC open data).
θ: posterior over the source parameters (GWTC-1 posterior samples).

Inputs are read from .render/data/ (not tracked):
  H-H1_GWOSC_4KHZ_R1-1126259447-32.hdf5, L-L1_GWOSC_4KHZ_R1-1126259447-32.hdf5  (gwosc.org)
  GW150914_GWTC-1.hdf5  (dcc.ligo.org/LIGO-P1800370)

Usage: python tools/gw_figures.py
"""

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.ndimage import gaussian_filter

DATA = ".render/data/"
OUT = "figures/"
T_MERGER = 1126259462.422  # GPS time of the merger
FS = 4096
BG = "#05070d"
W, H = 19.2, 14.4  # inches at 100 dpi -> 1920 x 1440, 4:3


def strain(det):
    with h5py.File(DATA + f"{det[0]}-{det}_GWOSC_4KHZ_R1-1126259447-32.hdf5") as f:
        s = f["strain/Strain"][()]
        t0 = f["meta/GPSstart"][()]
    return t0 + np.arange(len(s)) / FS, s


def whiten_bandpass(s):
    f, psd = signal.welch(s, FS, nperseg=4 * FS)
    S = np.fft.rfft(s * signal.windows.tukey(len(s), 0.1))
    freqs = np.fft.rfftfreq(len(s), 1 / FS)
    S /= np.sqrt(np.interp(freqs, f, psd))
    w = np.fft.irfft(S, n=len(s))
    b, a = signal.butter(4, [35, 350], btype="band", fs=FS)
    return signal.filtfilt(b, a, w)


def fig_strain():
    t, h1 = strain("H1")
    _, l1 = strain("L1")
    h1, l1 = whiten_bandpass(h1), whiten_bandpass(l1)
    # Livingston saw the wave 6.9 ms earlier, with opposite sign (detector orientation).
    l1 = -np.roll(l1, int(0.0069 * FS))
    m = (t > T_MERGER - 0.32) & (t < T_MERGER + 0.06)
    tt = t[m] - T_MERGER

    fig = plt.figure(figsize=(W, H), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
    for y, c, off in [(h1[m], "#ff8a3d", 2.6), (l1[m], "#5ab4ff", 0.2)]:
        y = y / np.abs(h1[m]).max() * 1.4
        ax.plot(tt, y + off, color=c, lw=9, alpha=0.18)  # glow
        ax.plot(tt, y + off, color=c, lw=3)
    ax.text(-0.315, 4.3, "LIGO Hanford", color="#ff8a3d", fontsize=34, alpha=0.9)
    ax.text(-0.315, 1.9, "LIGO Livingston", color="#5ab4ff", fontsize=34, alpha=0.9)
    ax.set_xlim(-0.32, 0.06)
    ax.set_ylim(-4.6, 5.2)  # traces in the upper part, caption box below
    ax.axis("off")
    fig.savefig(OUT + "gw-x.png", facecolor=BG)
    plt.close(fig)


def fig_posterior():
    with h5py.File(DATA + "GW150914_GWTC-1.hdf5") as f:
        d = f["Overall_posterior"][()]
    m1, m2 = d["m1_detector_frame_Msun"], d["m2_detector_frame_Msun"]
    dl = d["luminosity_distance_Mpc"]
    chi_eff = (m1 * d["spin1"] * d["costilt1"] + m2 * d["spin2"] * d["costilt2"]) / (m1 + m2)
    cols = [(m1, r"$m_1$ [$M_\odot$]"), (m2, r"$m_2$ [$M_\odot$]"), (dl, r"$d_L$ [Mpc]")]
    n = len(cols)
    color = "#b07cff"
    plt.rcParams.update({"font.size": 30, "text.color": "w", "axes.labelcolor": "w",
                         "xtick.color": "#9aa3b5", "ytick.color": "#9aa3b5"})
    fig = plt.figure(figsize=(W, H), dpi=100, facecolor=BG)
    # Leave the left part free for the caption box.
    # Large lower-triangular grid; the caption box goes in the empty top-right corner.
    w, h, gap = 0.26, 0.27, 0.012
    x0, y0 = 0.07, 0.13  # clear of the footnote
    for i in range(n):
        for j in range(i + 1):
            ax = fig.add_axes([x0 + j * (w + gap), y0 + (n - 1 - i) * (h + gap * 4 / 3), w, h], facecolor=BG)
            xi, xl = cols[j]
            lo_x, hi_x = np.percentile(xi, [0.5, 99.5])
            if i == j:
                ax.hist(xi, bins=40, range=(lo_x, hi_x), color=color, alpha=0.85, histtype="stepfilled")
                ax.set_yticks([])
            else:
                yi, yl = cols[i]
                lo_y, hi_y = np.percentile(yi, [0.5, 99.5])
                Hh, xe, ye = np.histogram2d(xi, yi, bins=50, range=[[lo_x, hi_x], [lo_y, hi_y]])
                Hh = gaussian_filter(Hh, 1.2).T
                ax.imshow(Hh, origin="lower", extent=[lo_x, hi_x, lo_y, hi_y], aspect="auto",
                          cmap="magma", interpolation="bicubic")
                if j == 0:
                    ax.set_ylabel(yl)
                else:
                    ax.set_yticklabels([])
            if i == n - 1:
                ax.set_xlabel(xl)
            else:
                ax.set_xticklabels([])
            for s in ax.spines.values():
                s.set_color("#2a3142")
            ax.tick_params(labelsize=20)
    fig.savefig(OUT + "gw-theta.png", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_strain()
    fig_posterior()
