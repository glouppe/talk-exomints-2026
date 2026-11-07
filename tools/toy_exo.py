"""A minimal emission-spectrum simulator for the guiding example (toy, not petitRADTRANS).

θ (6 parameters) -> z (atmosphere: temperature and abundance profiles, cloud) -> f(θ) (spectrum) -> x (binned, noisy).

    T_int     internal temperature [K]                 U(700, 1700)
    log_g     surface gravity [cgs]                    U(3.0, 5.0)
    MH        metallicity [M/H] (dex)                  U(-1.0, 1.0)
    CO        carbon-to-oxygen ratio                   U(0.2, 1.2)
    log_Pc    cloud-top pressure [bar]                 U(-1.5, 1.5)
    R_p       radius [R_Jup]                           U(0.8, 1.6)

Physics (deliberately simple):
- Grey Eddington P–T profile, T^4 = 3/4 T_int^4 (τ + 2/3), with τ = κ_IR P / g.
- Chemistry: carbon and oxygen scale with 10^[M/H]; carbon sits in CH4 at low T / high P and in CO otherwise
  (smooth transition along T_tr(P)); the oxygen not in CO forms H2O.
- Opacities: schematic absorption bands of H2O, CH4 and CO at their real wavelengths, with pseudo-line structure,
  plus a smooth H2–H2 collision-induced continuum (∝ P) and an opaque grey cloud deck below P_c.
- Emission: non-scattering 1D radiative transfer, I = ∫ B(T) e^{-τ} dτ along μ = 2/3, flux at 40 pc.
- Instrument: binned to R ≈ 100 between 0.95 and 2.45 μm, Gaussian noise of fixed σ.

Usage: from toy_exo import Simulator, LOWER, UPPER, NAMES
"""

import numpy as np

NAMES = ["T_int", "log_g", "MH", "CO", "log_Pc", "R_p"]
LABELS = [r"$T_{\rm int}$", r"$\log g$", r"$[{\rm M/H}]$", r"${\rm C/O}$", r"$\log P_{\rm cloud}$", r"$R_P$"]
UNITS = ["K", "", "", "", "bar", r"$R_{\rm J}$"]
LOWER = np.array([700.0, 3.0, -1.0, 0.2, -1.5, 0.8])
UPPER = np.array([1700.0, 5.0, 1.0, 1.2, 1.5, 1.6])

# Physical constants (SI unless noted)
H, C, KB = 6.626e-34, 2.998e8, 1.381e-23
R_JUP, PC = 7.1492e7, 3.0857e16
DIST = 40 * PC

# Solar abundances (number fractions relative to H2, roughly)
C_SUN, O_SUN = 5.4e-4, 9.8e-4

# Pressure grid [bar], native wavelength grid [μm], output bins (R ≈ 100)
P = np.logspace(-5, 2, 80)
WL = np.linspace(0.9, 2.5, 3000)
R_OUT = 100
_edges = np.exp(np.arange(np.log(0.95), np.log(2.45), 1 / R_OUT))
WL_OUT = np.sqrt(_edges[:-1] * _edges[1:])


def _bands(centers_widths_strengths, wl=WL, seed=0):
    """Absorption cross-section: Gaussian bands with pseudo-line structure."""
    rng = np.random.default_rng(seed)
    s = np.zeros_like(wl)
    for c, w, a in centers_widths_strengths:
        s += a * np.exp(-0.5 * ((wl - c) / w) ** 2)
    lines = 1 + 0.6 * np.sin(2 * np.pi * wl / 0.004 + rng.uniform(0, 2 * np.pi)) * np.sin(2 * np.pi * wl / 0.0113)
    return s * np.clip(lines, 0.2, None) + 1e-4


# Band positions [μm], widths [μm], relative strengths. Positions are those of the real bands; shapes are schematic.
SIGMA = {
    "H2O": _bands([(0.94, 0.02, 0.3), (1.13, 0.03, 1.0), (1.39, 0.045, 6.0), (1.88, 0.06, 10.0), (2.65, 0.09, 20.0)], seed=1),
    "CH4": _bands([(1.17, 0.02, 0.4), (1.38, 0.03, 1.0), (1.67, 0.035, 3.0), (2.20, 0.04, 2.0), (2.32, 0.06, 8.0)], seed=2),
    "CO": _bands([(1.58, 0.02, 0.05), (2.33, 0.04, 4.0)], seed=3),
}
CIA = 0.02 * np.exp(-0.5 * ((WL - 2.15) / 0.25) ** 2) + 0.008 * np.exp(-0.5 * ((WL - 1.2) / 0.15) ** 2)

KAPPA_IR = 3e-2          # grey opacity for the P–T profile [cm^2 / g]
MOL_SCALE = 50.0         # cross-section scale: τ ≈ MOL_SCALE * X * σ(λ) * P / g (strong bands τ=1 near 0.01 bar)
CIA_SCALE = 0.5          # collision-induced: ∝ P^2 / g (windows τ=1 near 1 bar)
SIGMA_NOISE = 2.5e-17    # noise [W m^-2 μm^-1]: S/N ≈ 30 at the benchmark peaks, as in Vasist et al (2023)


def pt_profile(T_int, log_g):
    g = 10 ** log_g  # cm s^-2
    tau = KAPPA_IR * P * 1e6 / g
    return (0.75 * T_int ** 4 * (tau + 2 / 3)) ** 0.25


def chemistry(T, MH, CO):
    """Volume mixing ratios of H2O, CH4, CO along the profile."""
    C_tot = C_SUN * 10 ** MH * CO / (C_SUN / O_SUN)
    O_tot = O_SUN * 10 ** MH
    T_tr = 1100 + 120 * np.log10(P)          # CO/CH4 equal-abundance curve (rough)
    f_ch4 = 1 / (1 + np.exp((T - T_tr) / 60))
    x_ch4 = C_tot * f_ch4
    x_co = np.minimum(C_tot * (1 - f_ch4), O_tot)
    x_h2o = np.clip(O_tot - x_co, 1e-12, None)
    return {"H2O": x_h2o, "CH4": x_ch4, "CO": x_co}


def latent(theta):
    """θ -> z: temperature profile, abundance profiles, cloud-top pressure."""
    T_int, log_g, MH, CO, log_Pc, R_p = theta
    T = pt_profile(T_int, log_g)
    return {"P": P, "T": T, "X": chemistry(T, MH, CO), "P_cloud": 10 ** log_Pc}


def planck(wl_um, T):
    wl = wl_um[None, :] * 1e-6
    return 2 * H * C ** 2 / wl ** 5 / np.expm1(H * C / (wl * KB * T[:, None]))  # W m^-2 m^-1 sr^-1


def spectrum(theta, z=None):
    """θ (and z) -> f(θ) on the native grid [W m^-2 μm^-1] at Earth."""
    T_int, log_g, MH, CO, log_Pc, R_p = theta
    z = latent(theta) if z is None else z
    g = 10 ** log_g
    dP = np.gradient(P)
    kappa = sum(z["X"][s][:, None] * SIGMA[s][None, :] for s in SIGMA) * MOL_SCALE
    kappa = kappa + CIA_SCALE * P[:, None] * CIA[None, :]
    dtau = kappa * dP[:, None] * 1e6 / g
    # Opaque grey cloud deck below the cloud top (smooth over ~0.1 dex)
    cloud = 50.0 / (1 + np.exp(-(np.log10(P) - log_Pc) / 0.05))
    dtau = dtau + cloud[:, None] * dP[:, None] / P[:, None]
    mu = 2 / 3
    tau = np.cumsum(dtau, axis=0) / mu
    w = np.exp(-(tau - dtau / mu)) - np.exp(-tau)  # emission weight of each layer
    I = np.sum(w * planck(WL, z["T"]), axis=0)
    F = np.pi * I * (R_p * R_JUP / DIST) ** 2 * 1e-6  # W m^-2 μm^-1
    return F


def bin_spectrum(F):
    idx = np.digitize(WL, _edges) - 1
    out = np.zeros(len(WL_OUT))
    for i in range(len(WL_OUT)):
        out[i] = F[idx == i].mean()
    return out


class Simulator:
    """θ -> x. Returns binned spectra in units of 1e-16 W m^-2 μm^-1."""

    scale = 1e16

    def __init__(self, noisy=True, seed=None):
        self.noisy = noisy
        self.rng = np.random.default_rng(seed)
        self._idx = np.digitize(WL, _edges) - 1
        self._counts = np.bincount(self._idx[(self._idx >= 0) & (self._idx < len(WL_OUT))], minlength=len(WL_OUT))

    def clean(self, theta):
        F = spectrum(theta)
        m = (self._idx >= 0) & (self._idx < len(WL_OUT))
        f = np.bincount(self._idx[m], weights=F[m], minlength=len(WL_OUT)) / self._counts
        return f * self.scale

    def __call__(self, theta):
        f = self.clean(theta)
        if self.noisy:
            f = f + SIGMA_NOISE * self.scale * self.rng.standard_normal(f.shape)
        return f

    def sample_prior(self, n):
        return LOWER + (UPPER - LOWER) * self.rng.random((n, len(LOWER)))


THETA_STAR = np.array([1100.0, 3.75, 0.0, 0.55, 0.5, 1.0])  # benchmark, close in spirit to Vasist et al (2023)
