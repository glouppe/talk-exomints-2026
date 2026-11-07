"""Dark-mode versions of the figures of Vasist et al (2023), for the exoplanet example.

The paper figures (arXiv:2301.06575 source, plots/*.pdf) are rendered at high resolution,
then recoloured: lightness is inverted and hue kept, so white becomes the dark slide
background, black lines become white, and the blue (NPE) and orange (MultiNest) keep
their colours.

Inputs: .render/data/vasist/plots/{consistency_wlfixed,output-figure0}.pdf (not tracked).
Outputs: figures/exo-x.png (spectrum), figures/exo-z.png (P-T profile), figures/exo-theta.png (corner).

Usage: python tools/exo_figures.py
"""

import subprocess
import tempfile

import numpy as np
from PIL import Image

SRC = ".render/data/vasist/plots/"
OUT = "figures/"
BG = np.array([5, 7, 13]) / 255  # same background as the GW figures


def render(pdf, dpi=600):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-singlefile", SRC + pdf, d + "/p"], check=True)
        return np.asarray(Image.open(d + "/p.png").convert("RGB")) / 255.0


def dark(rgb):
    """Invert lightness (HSL), keep hue and saturation, map white to the slide background."""
    mx, mn = rgb.max(-1), rgb.min(-1)
    l = (mx + mn) / 2
    l2 = 1 - l
    # Rescale chroma so that the colour keeps its saturation at the new lightness.
    c = mx - mn
    s = np.where(c > 0, c / (1 - np.abs(2 * l - 1) + 1e-9), 0)
    c2 = s * (1 - np.abs(2 * l2 - 1))
    hue_part = np.where(c[..., None] > 0, (rgb - mn[..., None]) / (c[..., None] + 1e-9), 0)
    out = l2[..., None] - c2[..., None] / 2 + hue_part * c2[..., None]
    # Pure background (very dark after inversion) -> slide background.
    w = np.clip((0.12 - l2) / 0.12, 0, 1)[..., None]
    out = out * (1 - w) + BG * w
    return np.clip(out, 0, 1)


def place(img, frac_box, name, size=(1920, 1440)):
    """Paste img into a 4:3 canvas inside frac_box = (x0, y0, x1, y1) (fractions), keeping its aspect."""
    W, H = size
    canvas = Image.new("RGB", size, tuple((BG * 255).astype(int)))
    x0, y0, x1, y1 = frac_box
    bw, bh = int((x1 - x0) * W), int((y1 - y0) * H)
    im = Image.fromarray((img * 255).astype(np.uint8))
    im.thumbnail((bw, bh), Image.Resampling.LANCZOS)
    cx, cy = int(x0 * W + (bw - im.width) / 2), int(y0 * H + (bh - im.height) / 2)
    canvas.paste(im, (cx, cy))
    canvas.save(OUT + name)


def crop(a, x0, y0, x1, y1):
    h, w = a.shape[:2]
    return a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


if __name__ == "__main__":
    spec = dark(render("consistency_wlfixed.pdf"))
    # Spectrum, posterior predictive and residuals, in the upper part of the slide (caption box below).
    place(spec, (0.10, 0.03, 0.90, 0.66), "exo-x.png")

    corner = dark(render("output-figure0.pdf"))
    # P-T profile: the inset in the top-right corner of the corner plot.
    place(crop(corner, 0.545, 0.0, 1.0, 0.46), (0.42, 0.04, 0.97, 0.68), "exo-z.png")
    # Corner plot without the P-T inset, so that the caption box fits in the top-right corner.
    h, w = corner.shape[:2]
    corner[: int(0.47 * h), int(0.55 * w):] = BG
    place(corner, (0.0, 0.0, 0.88, 0.92), "exo-theta.png")  # left of the caption box, above the footnote
