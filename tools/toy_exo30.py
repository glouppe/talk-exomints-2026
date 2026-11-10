"""A 30-parameter version of the toy emission-spectrum simulator (toy_exo.py), shaped like a free retrieval.

θ (30 parameters) -> z (temperature profile, constant abundances, cloud) -> f(θ) (spectrum) -> x (binned, noisy).

    log_g                  surface gravity [cgs]                          U(3.0, 5.0)
    R_p                    radius [R_Jup]                                 U(0.8, 1.6)
    T_0                    temperature at the bottom node (100 bar) [K]   U(1500, 6000)
    r_1 ... r_9            T_{i} / T_{i-1} between consecutive nodes     U(0.55, 1.05)
    log_X (15 species)     constant volume mixing ratio                   U(-10, -2)
    log_Pc                 cloud-top pressure [bar]                       U(-2, 2)
    log_tau_c              cloud optical depth per dex below the top      U(-1, 2)
    alpha_c                cloud slope, tau ∝ (λ / 1 μm)^-alpha           U(0, 4)

Differences from toy_exo.py:
- Free P–T profile: 10 nodes equally spaced in log P from 100 bar to 1e-5 bar, the bottom temperature and nine
  ratios (as in Zhang et al. 2023-style free profiles), linear in log P between nodes, floored at 100 K.
- Free chemistry: 15 species with vertically constant abundances, no equilibrium. Bands are schematic, at roughly
  the real positions, so that some species overlap (HCN / C2H2 / NH3 at 3 μm, CO2 / PH3 at 4.3 μm) and some are
  barely visible: many parameters will be prior-dominated, as in real retrievals.
- A non-grey cloud deck with an optical depth and a slope.
- Wider range, 0.8–5.0 μm at R ≈ 100 (a NIRSpec PRISM-like range), so the 3–5 μm bands constrain carbon.

Usage: from toy_exo30 import Simulator, LOWER, UPPER, NAMES, THETA_STAR
"""

import numpy as np

SPECIES = ["H2O", "CH4", "CO", "CO2", "NH3", "H2S", "HCN", "C2H2", "PH3", "FeH", "CrH", "TiO", "VO", "K", "SiO"]
N_NODES = 10
NAMES = (["log_g", "R_p", "T_0"] + [f"r_{i}" for i in range(1, N_NODES)] + [f"log_{s}" for s in SPECIES]
         + ["log_Pc", "log_tau_c", "alpha_c"])
LOWER = np.array([3.0, 0.8, 1500.0] + [0.55] * (N_NODES - 1) + [-10.0] * len(SPECIES) + [-2.0, -1.0, 0.0])
UPPER = np.array([5.0, 1.6, 6000.0] + [1.05] * (N_NODES - 1) + [-2.0] * len(SPECIES) + [2.0, 2.0, 4.0])
assert len(NAMES) == len(LOWER) == len(UPPER) == 30

H, C, KB = 6.626e-34, 2.998e8, 1.381e-23
R_JUP, PC = 7.1492e7, 3.0857e16
DIST = 40 * PC

# Native grids. 40 layers and 4000 wavelengths (4 points per pseudo-line period) keep a simulation's arrays in
# cache: with 80 x 8000, 100+ simulations at once on one node were memory-bound at ~0.4 s each.
import os as _os
P = np.logspace(-5, 2, int(_os.environ.get("TOY30_NLAYER", 40)))
LOGP_NODES = np.linspace(2, -5, N_NODES)  # bottom to top
WL = np.linspace(0.8, 5.0, int(_os.environ.get("TOY30_NWL", 4000)))
R_OUT = 100
_edges = np.exp(np.arange(np.log(0.85), np.log(4.95), 1 / R_OUT))
WL_OUT = np.sqrt(_edges[:-1] * _edges[1:])


def _bands(cws, seed):
    rng = np.random.default_rng(seed)
    s = np.zeros_like(WL)
    for c, w, a in cws:
        s += a * np.exp(-0.5 * ((WL - c) / w) ** 2)
    lines = 1 + 0.6 * np.sin(2 * np.pi * WL / 0.004 + rng.uniform(0, 2 * np.pi)) * np.sin(2 * np.pi * WL / 0.0113)
    return s * np.clip(lines, 0.2, None) + 1e-4


# (centre μm, width μm, strength). Strengths relative to H2O's 1.88 μm band = 10, as in toy_exo.py.
BANDS = {
    "H2O": [(0.94, 0.02, 0.3), (1.13, 0.03, 1.0), (1.39, 0.045, 6.0), (1.88, 0.06, 10.0), (2.7, 0.09, 20.0), (3.2, 0.1, 2.0)],
    "CH4": [(1.17, 0.02, 0.4), (1.38, 0.03, 1.0), (1.67, 0.035, 3.0), (2.20, 0.04, 2.0), (2.32, 0.06, 8.0), (3.31, 0.08, 30.0)],
    "CO": [(1.58, 0.02, 0.05), (2.33, 0.04, 4.0), (4.67, 0.08, 30.0)],
    "CO2": [(1.43, 0.015, 0.05), (1.6, 0.02, 0.1), (2.0, 0.03, 0.5), (2.7, 0.04, 3.0), (4.27, 0.05, 80.0)],
    "NH3": [(1.5, 0.04, 0.5), (2.0, 0.04, 0.8), (3.0, 0.08, 4.0)],
    "H2S": [(1.59, 0.03, 0.1), (2.6, 0.05, 1.0), (3.7, 0.08, 0.5)],
    "HCN": [(1.53, 0.02, 0.3), (3.0, 0.04, 10.0)],
    "C2H2": [(1.52, 0.02, 0.1), (3.0, 0.05, 6.0)],
    "PH3": [(2.15, 0.04, 0.5), (4.3, 0.08, 10.0)],
    "FeH": [(0.99, 0.01, 3.0), (1.2, 0.03, 1.0), (1.6, 0.03, 0.5)],
    "CrH": [(0.87, 0.02, 2.0), (1.0, 0.02, 1.0)],
    "TiO": [(0.85, 0.05, 5.0), (0.95, 0.05, 3.0), (1.1, 0.06, 1.0)],
    "VO": [(1.05, 0.04, 3.0), (1.2, 0.04, 1.0)],
    "K": [(1.17, 0.003, 0.8), (1.25, 0.003, 1.0)],
    "SiO": [(4.05, 0.1, 5.0)],
}
SIGMA = np.stack([_bands(BANDS[s], seed=i + 1) for i, s in enumerate(SPECIES)])  # (species, wl)
CIA = (0.02 * np.exp(-0.5 * ((WL - 2.15) / 0.25) ** 2) + 0.008 * np.exp(-0.5 * ((WL - 1.2) / 0.15) ** 2)
       + 0.01 * np.exp(-0.5 * ((WL - 4.5) / 0.6) ** 2))

MOL_SCALE = 50.0
CIA_SCALE = 0.5


def pt_profile(T_0, ratios):
    T_nodes = T_0 * np.concatenate([[1.0], np.cumprod(ratios)])
    T = np.interp(np.log10(P), LOGP_NODES[::-1], T_nodes[::-1])
    return np.maximum(T, 100.0)


def unpack(theta):
    theta = np.asarray(theta, dtype=float)
    log_g, R_p, T_0 = theta[:3]
    ratios = theta[3:3 + N_NODES - 1]
    log_X = theta[3 + N_NODES - 1:3 + N_NODES - 1 + len(SPECIES)]
    log_Pc, log_tau_c, alpha_c = theta[-3:]
    return log_g, R_p, T_0, ratios, log_X, log_Pc, log_tau_c, alpha_c


def planck(wl_um, T):
    wl = wl_um[None, :] * 1e-6
    return 2 * H * C ** 2 / wl ** 5 / np.expm1(H * C / (wl * KB * T[:, None]))


def spectrum(theta):
    """θ -> f(θ) on the native grid [W m^-2 μm^-1] at Earth."""
    log_g, R_p, T_0, ratios, log_X, log_Pc, log_tau_c, alpha_c = unpack(theta)
    g = 10 ** log_g
    T = pt_profile(T_0, ratios)
    dP = np.gradient(P)
    kappa_mol = (10 ** log_X) @ SIGMA * MOL_SCALE                     # constant abundances: one spectrum
    kappa = kappa_mol[None, :] + CIA_SCALE * P[:, None] * CIA[None, :]  # (layers, wl)
    dtau = kappa * dP[:, None] * 1e6 / g
    # Cloud: optical depth 10^log_tau_c per dex of pressure below the top, with a wavelength slope
    dlogP = dP / P / np.log(10)
    below = 1 / (1 + np.exp(-(np.log10(P) - log_Pc) / 0.05))
    dtau = dtau + (10 ** log_tau_c * below * dlogP)[:, None] * WL[None, :] ** (-alpha_c)
    mu = 2 / 3
    tau = np.cumsum(dtau, axis=0) / mu
    w = np.exp(-(tau - dtau / mu)) - np.exp(-tau)
    I = np.sum(w * planck(WL, T), axis=0)
    return np.pi * I * (R_p * R_JUP / DIST) ** 2 * 1e-6


THETA_STAR = np.array(
    [3.75, 1.0, 4900.0]
    + [0.62, 0.66, 0.72, 0.80, 0.88, 0.95, 0.98, 1.0, 1.0]
    + [-3.3, -3.6, -3.5, -5.0, -4.5, -4.5, -5.0, -6.0, -5.5, -6.0, -6.5, -8.0, -8.0, -5.5, -5.0]
    + [0.5, 0.5, 1.0])

# Noise: S/N ≈ 30 at the peak of the benchmark spectrum, as in toy_exo.py (set below, once the binning exists).
SIGMA_NOISE = None


class Simulator:
    """θ -> x. Binned spectra in units of 1e-16 W m^-2 μm^-1."""

    scale = 1e16

    def __init__(self, noisy=True, seed=None):
        self.noisy = noisy
        self.rng = np.random.default_rng(seed)
        self._idx = np.digitize(WL, _edges) - 1
        self._m = (self._idx >= 0) & (self._idx < len(WL_OUT))
        self._counts = np.bincount(self._idx[self._m], minlength=len(WL_OUT))

    def clean(self, theta):
        F = spectrum(theta)
        f = np.bincount(self._idx[self._m], weights=F[self._m], minlength=len(WL_OUT)) / self._counts
        return f * self.scale

    def __call__(self, theta):
        f = self.clean(theta)
        if self.noisy:
            f = f + SIGMA_NOISE * self.scale * self.rng.standard_normal(f.shape)
        return f

    def sample_prior(self, n):
        return LOWER + (UPPER - LOWER) * self.rng.random((n, len(LOWER)))


SIGMA_NOISE = float(Simulator(noisy=False).clean(THETA_STAR).max() / Simulator.scale / 30)
