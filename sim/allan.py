"""Allan deviation from a fractional-frequency time series.

The (overlapping) Allan deviation σ_y(τ) measures clock stability at
averaging time τ. We accept either:
    * a sequence of timestamps t[k] (when each clock edge happened), or
    * a sequence of fractional-frequency samples y[k] = (T_k - T0) / T0.

For our PLL simulator, the natural input is the array of divider-edge
times t_div_eff[k] (in seconds), sampled at T_ref. From this we
compute the per-cycle fractional frequency error and then the
overlapping Allan deviation over a grid of averaging times.

References (not reproduced here): IEEE Std 1139 and Riley, "Handbook
of Frequency Stability Analysis", NIST Special Publication 1065.
"""
from __future__ import annotations
import numpy as np


def fractional_frequency_from_edges(t_edges_s: np.ndarray,
                                    t_nominal_s: float) -> np.ndarray:
    """Return y[k] = (T_k - T_nominal) / T_nominal from edge timestamps.

    Edges are differenced to give per-cycle periods.
    """
    t = np.asarray(t_edges_s, dtype=float)
    T = np.diff(t)
    return (T - t_nominal_s) / t_nominal_s


def overlapping_adev(y: np.ndarray, tau0_s: float,
                     m_values: np.ndarray = None) -> tuple[np.ndarray, np.ndarray]:
    """Overlapping Allan deviation σ_y(τ) using the y-series formula.

    σ²_y(τ) = (1/(2·(N - 2m)·τ²)) · Σ_{i=0..N-2m-1} (x[i+2m] - 2 x[i+m] + x[i])²

    where x[k] is the cumulative phase: x[k] = τ0 · sum_{j<k} y[j],
    and τ = m·τ0. Returns (tau_array, adev_array).
    """
    y = np.asarray(y, dtype=float)
    N = y.size
    # Phase samples x[k] in seconds
    x = np.concatenate(([0.0], np.cumsum(y) * tau0_s))
    if m_values is None:
        # Log-spaced m up to N/4 so the estimate has at least 4 averages
        m_values = np.unique(np.round(
            np.geomspace(1, max(2, N // 4), 30)).astype(int))
    tau_arr, adev_arr = [], []
    for m in m_values:
        if m < 1 or 2 * m >= N:
            continue
        d = x[2 * m:] - 2 * x[m:-m] + x[: -2 * m]
        if d.size < 2:
            continue
        var = np.mean(d ** 2) / (2.0 * (m * tau0_s) ** 2)
        tau_arr.append(m * tau0_s)
        adev_arr.append(float(np.sqrt(var)))
    return np.asarray(tau_arr), np.asarray(adev_arr)


def adev_from_div_edges(t_div_s: np.ndarray, T_ref_s: float,
                        m_values: np.ndarray = None
                        ) -> tuple[np.ndarray, np.ndarray]:
    """Convenience: ADEV from PLL simulator's t_div_eff trace."""
    y = fractional_frequency_from_edges(t_div_s, t_nominal_s=T_ref_s)
    return overlapping_adev(y, tau0_s=T_ref_s, m_values=m_values)
