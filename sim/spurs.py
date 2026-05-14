"""Fractional-spur detection from a phase-noise PSD.

Fractional spurs in a fractional-N PLL fall at offsets

    f_spur_k = ((k * alpha) mod 1) * f_ref     k = 1, 2, ...

(plus their f_ref-folded images). This module locates the dominant peak
around each predicted offset within a small search window and reports
the level in dBc/Hz.

Note: in our PSD L(f) is dBc/Hz, so a spur reading of -X dBc/Hz over a
narrow bin must be integrated by the Welch resolution bandwidth to get
the true dBc spur level if desired (we report dBc/Hz directly).
"""
import numpy as np


def predicted_spur_offsets(alpha: float, f_ref: float, n_harmonics: int = 12):
    out = []
    for k in range(1, n_harmonics + 1):
        f = ((k * alpha) % 1.0) * f_ref
        if f > 0:
            out.append((k, f))
    return out


def detect_spurs(f, L_dbchz, alpha: float, f_ref: float,
                 n_harmonics: int = 12,
                 search_window_bins: int = 4):
    """Return list of dicts {k, f_target, f_peak, L_dbchz}."""
    f = np.asarray(f)
    L = np.asarray(L_dbchz)
    results = []
    for k, f_target in predicted_spur_offsets(alpha, f_ref, n_harmonics):
        if f_target >= f[-1] or f_target <= f[0]:
            continue
        i0 = int(np.argmin(np.abs(f - f_target)))
        lo = max(i0 - search_window_bins, 0)
        hi = min(i0 + search_window_bins, len(f) - 1)
        i_peak = lo + int(np.argmax(L[lo:hi + 1]))
        results.append({
            "k": k,
            "f_target": float(f_target),
            "f_peak": float(f[i_peak]),
            "L_dbchz": float(L[i_peak]),
        })
    return results
