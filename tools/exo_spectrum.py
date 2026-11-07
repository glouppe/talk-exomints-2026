"""Spectrum inset for the exoplanet x slide.

Extracts the benchmark spectrum f(θ_obs) of Vasist et al (2023) from the vector figure
(.render/data/vasist/plots/consistency_wlfixed.pdf, arXiv:2301.06575 source, not tracked),
calibrates it with the tick labels, and draws it as a glowing line on a transparent background.

Output: figures/exo-x-spectrum.png

Usage: uvx --from pymupdf --with numpy --with matplotlib python tools/exo_spectrum.py
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pymupdf

PDF = ".render/data/vasist/plots/consistency_wlfixed.pdf"


def extract():
    page = pymupdf.open(PDF)[0]
    words = page.get_text("words")
    # Tick labels: wavelength below the residual panel, flux on the left of the spectrum panel.
    xt = [((w[0] + w[2]) / 2, float(w[4])) for w in words if w[1] > 240 and w[4].replace(".", "").isdigit()]
    yt = [((w[1] + w[3]) / 2, float(w[4])) for w in words if w[0] < 25 and w[3] < 180 and w[4].replace(".", "").isdigit()]
    ax, bx = np.polyfit([p for p, _ in xt], [v for _, v in xt], 1)
    ay, by = np.polyfit([p for p, _ in yt], [v for _, v in yt], 1)
    path = next(d for d in page.get_drawings() if d.get("color") == (0.0, 0.0, 0.0) and len(d["items"]) > 300)
    pts = [it[1] for it in path["items"] if it[0] == "l"] + [path["items"][-1][2]]
    px = np.array([p.x for p in pts])
    py = np.array([p.y for p in pts])
    return ax * px + bx, ay * py + by


def main():
    wl, flux = extract()
    fig = plt.figure(figsize=(8, 3.6), dpi=200)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0.08, 0.2, 0.9, 0.75])
    ax.patch.set_alpha(0)
    for lw, a in [(10, 0.08), (6, 0.15), (3.5, 0.3)]:
        ax.plot(wl, flux, color="#ffb36b", lw=lw, alpha=a, solid_capstyle="round")
    ax.plot(wl, flux, color="#fff1e0", lw=1.6)
    ax.set_xlim(wl.min() - 0.02, wl.max() + 0.02)
    ax.set_ylim(0, flux.max() * 1.1)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9d3ff")
    ax.set_yticks([])
    ax.tick_params(colors="#c9d3ff", labelsize=14)
    ax.set_xlabel("Wavelength (μm)", color="#c9d3ff", fontsize=15)
    fig.savefig("figures/exo-x-spectrum.png", transparent=True)


if __name__ == "__main__":
    main()
