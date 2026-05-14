"""Integrated RMS jitter from L(f).

Conventions:
    var_phi  = 2 * integral_{f_lo}^{f_hi} L(f) df            [rad^2]
    sigma_t  = sqrt(var_phi) / (2 * pi * f_carrier)          [s]
"""
import numpy as np


def integrated_phase_variance(f, L_dbchz, f_lo, f_hi) -> float:
    f = np.asarray(f, float)
    L_dbchz = np.asarray(L_dbchz, float)
    m = (f >= f_lo) & (f <= f_hi) & np.isfinite(L_dbchz)
    if m.sum() < 2:
        return float("nan")
    L_lin = 10.0 ** (L_dbchz[m] / 10.0)
    # numpy>=2.0 renamed trapz -> trapezoid
    trapezoid = getattr(np, "trapezoid", None) or np.trapz
    return float(2.0 * trapezoid(L_lin, f[m]))


def integrated_rms_jitter_s(f, L_dbchz, f_lo, f_hi, f_carrier) -> float:
    var_phi = integrated_phase_variance(f, L_dbchz, f_lo, f_hi)
    if not np.isfinite(var_phi) or var_phi < 0:
        return float("nan")
    return float(np.sqrt(var_phi) / (2.0 * np.pi * f_carrier))
