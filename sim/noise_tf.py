"""Analytic small-signal noise-transfer functions for the BBPD-DPLL.

Linearized continuous-time approximation (valid for f << f_ref/2).
Plant in time-error domain, referenced to DCO-output time jitter:

    L(s) = K_bb * K_DCO * H_LF(s) / (s * f_DCO_nom)
    H_LF(s) = Kp + Ki / (s * T_ref)        (continuous-time PI)

Closed-loop noise transfer functions:

    H_ref(s)    = L(s) / (1 + L(s))         low-pass   (ref jitter)
    H_dtc(s)    = L(s) / (1 + L(s))         low-pass   (DTC noise)
    H_dcopn(s)  = 1 / (1 + L(s))            high-pass  (DCO PN)

K_bb is the BBPD's small-signal gain and depends on the total dither
seen at its input. The simulator measures that dither and we can plug
it in here; the helper `estimate_kbb_from_sim` does exactly that.

NOTE: This module is a teaching aid. It does not affect the time-domain
simulator. Use it to cross-check that the simulated PSD has the right
shape and roll-off.
"""
import numpy as np

from .bbpd import BBPD
from .pll_params import PLLParams


def open_loop_gain(f, K_bb: float, params: PLLParams) -> np.ndarray:
    """L(s) at frequencies f (Hz). Returns complex array."""
    f = np.asarray(f, dtype=float)
    s = 2j * np.pi * np.maximum(f, 1e-9)
    H_LF = params.Kp + params.Ki / (s * params.T_ref)
    return K_bb * params.K_dco * H_LF / (s * params.f_dco_nominal)


def ntf_ref(f, K_bb: float, params: PLLParams) -> np.ndarray:
    L = open_loop_gain(f, K_bb, params)
    return L / (1.0 + L)


def ntf_dtc(f, K_bb: float, params: PLLParams) -> np.ndarray:
    return ntf_ref(f, K_bb, params)


def ntf_dco_pn(f, K_bb: float, params: PLLParams) -> np.ndarray:
    L = open_loop_gain(f, K_bb, params)
    return 1.0 / (1.0 + L)


def predict_closed_loop_L_dbchz(
    f, K_bb: float, params: PLLParams,
    ref_jitter_rms_s: float = None,
    include_bbpd_noise: bool = True,
) -> np.ndarray:
    """Predict closed-loop output phase-noise L(f) [dBc/Hz] analytically.

    Three contributions, all closed-form:
        * DCO open-loop template, high-pass shaped by 1/(1+L).
        * Reference jitter (white in time), low-pass shaped by L/(1+L).
        * BBPD-folded quantization noise (white in detector output,
          ±1 with variance 1), input-referred by /K_bb^2, low-pass
          shaped by L/(1+L).
    """
    f = np.asarray(f, dtype=float)

    # DCO open-loop PN template (single-sideband, dBc/Hz), interpolated
    log_f = np.log10(np.clip(f, 1.0, None))
    L_open_db = np.interp(log_f,
                          np.log10(params.dco_pn_freqs_hz),
                          params.dco_pn_levels_dbchz,
                          left=params.dco_pn_levels_dbchz[0],
                          right=params.dco_pn_levels_dbchz[-1])
    S_dco_open_phi = 2.0 * 10.0 ** (L_open_db / 10.0)  # one-sided rad^2/Hz

    # Closed-loop DCO-PN contribution
    H_dco = ntf_dco_pn(f, K_bb, params)
    S_phi_closed_dco = np.abs(H_dco) ** 2 * S_dco_open_phi

    # Reference contribution. Reference jitter is modeled as white
    # time-domain noise; convert to phase-noise PSD at the output.
    if ref_jitter_rms_s is None:
        ref_jitter_rms_s = params.ref_jitter_rms_s
    f_ref = params.f_ref
    H_ref = ntf_ref(f, K_bb, params)
    if ref_jitter_rms_s > 0:
        # Single-sided white time-jitter PSD = sigma^2 / (f_ref/2)
        S_t_ref_one = ref_jitter_rms_s ** 2 / (f_ref / 2.0)
        S_phi_ref = (2.0 * np.pi * params.f_dco_nominal) ** 2 * S_t_ref_one
        S_phi_closed_ref = np.abs(H_ref) ** 2 * S_phi_ref
    else:
        S_phi_closed_ref = np.zeros_like(f)

    # BBPD-folded quantization noise. The detector output has variance
    # ~1 (it's ±1 with E[s] = K_bb*e ≈ 0 at lock), spread over the
    # one-sided sampling bandwidth f_ref/2. Input-referred PSD in
    # seconds^2/Hz is therefore (2 / f_ref) / K_bb^2.
    if include_bbpd_noise and K_bb > 0 and np.isfinite(K_bb):
        S_t_bbpd_one = 2.0 / (K_bb ** 2 * f_ref)
        S_phi_bbpd_in = ((2.0 * np.pi * params.f_dco_nominal) ** 2
                         * S_t_bbpd_one)
        S_phi_closed_bbpd = np.abs(H_ref) ** 2 * S_phi_bbpd_in
    else:
        S_phi_closed_bbpd = np.zeros_like(f)

    S_phi_total = S_phi_closed_dco + S_phi_closed_ref + S_phi_closed_bbpd
    with np.errstate(divide="ignore"):
        L_closed = 10.0 * np.log10(np.maximum(S_phi_total / 2.0, 1e-300))
    return L_closed


def estimate_kbb_from_sim(e_bbpd_s: np.ndarray, trim_settling: float = 0.5) -> float:
    """Estimate K_bb = sqrt(2/pi)/sigma from steady-state BBPD input trace."""
    n = len(e_bbpd_s)
    tail = e_bbpd_s[int(trim_settling * n):]
    tail = tail - np.mean(tail)
    sigma = float(np.std(tail))
    if sigma <= 0:
        return float("inf")
    return BBPD.linearized_gain(sigma)
