"""Top-level phase-domain DPLL simulator.

One simulation step = one reference cycle = one feedback divider cycle.
We track absolute time of every reference and divider edge in SECONDS.

State per step k (all stored in `SimResults`):
    t_ref[k]      reference edge time (with optional reference jitter)
    m[k]          DSM integer dither -> divider modulus D = N_int + m
    e_dsm[k]      cumulative DSM residue (fractional cycles); this is
                  what an ideal DTC would cancel
    t_div[k]      divider edge time before the DTC
    tau_dtc[k]    DTC delay applied to that edge
    t_div_eff[k]  divider edge time after DTC delay (compared to ref)
    e_bbpd[k]     t_div_eff - t_ref           (the BBPD's input)
    s[k]          BBPD output (integer code; ±1 for 1-bit)
    u[k]          DCO tuning word from the digital loop filter
    f_dco[k]      DCO frequency
    g_hat[k]      LMS-learned DTC gain coefficient
    offset_hat[k] LMS-learned DTC offset (digital, in seconds)

Sign convention recap:
    * e_bbpd > 0   feedback edge is LATE        -> BBPD outputs +1
    * s[k] = +1    pushes u positive            -> DCO speeds up
    * Faster DCO   shortens future divider periods -> e_bbpd decreases
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .pll_params import PLLParams
from .dsm import MASH
from .dtc import DTC
from .bbpd import BBPD
from .loop_filter import DigitalPI
from .dco import DCO
from .fractional_divider import FractionalDivider
from .phase_noise import generate_pn_sequence
from .realistic_dco import RealisticDCO


@dataclass
class SimResults:
    t_ref: np.ndarray
    t_div: np.ndarray
    t_div_eff: np.ndarray
    e_bbpd: np.ndarray
    s_bbpd: np.ndarray
    u: np.ndarray
    m: np.ndarray
    e_dsm: np.ndarray
    tau_dtc: np.ndarray
    f_dco: np.ndarray
    g_hat: np.ndarray
    offset_hat: np.ndarray
    inl_table_hat: Optional[np.ndarray]
    kbb_scale: np.ndarray
    sigma_est: np.ndarray
    params: PLLParams
    alpha: float
    lms_enabled: bool


def excess_phase_at_dco(res: SimResults, trim_settling: float = 0.5) -> np.ndarray:
    p = res.params
    n = len(res.t_div_eff)
    delta = res.t_div_eff - (np.arange(n) + 1) * p.T_ref
    i0 = int(trim_settling * n)
    delta = delta[i0:]
    delta = delta - np.mean(delta)
    return 2.0 * np.pi * p.f_dco_nominal * delta


def _build_ref_jitter(params: PLLParams, n: int, T_ref: float,
                     enable_ref_noise: bool, rng) -> np.ndarray:
    if not enable_ref_noise:
        return np.zeros(n)
    # Colored ref PN if template is set
    if (params.ref_pn_freqs_hz is not None
            and params.ref_pn_levels_dbchz is not None):
        phi_ref = generate_pn_sequence(n, params.f_ref,
                                       params.ref_pn_freqs_hz,
                                       params.ref_pn_levels_dbchz, rng)
        ref_jitter = phi_ref / (2.0 * np.pi * params.f_ref)
    else:
        ref_jitter = (rng.normal(0.0, params.ref_jitter_rms_s, n)
                      if params.ref_jitter_rms_s > 0 else np.zeros(n))
    if params.ref_spur_amp_s > 0 and params.ref_spur_freq_hz > 0:
        k_idx = np.arange(n)
        ref_jitter = ref_jitter + params.ref_spur_amp_s * np.sin(
            2.0 * np.pi * params.ref_spur_freq_hz * k_idx * T_ref)
    return ref_jitter


def run_simulation(params: PLLParams,
                   alpha: float = None,
                   enable_dtc: bool = True,
                   enable_dco_pn: bool = True,
                   enable_ref_noise: bool = True,
                   enable_lms: bool = False,
                   u_init: float = None) -> SimResults:
    """Run one closed-loop time-domain simulation.

    Calibration controlled by PLLParams (in addition to the master
    enable_lms switch above):
        * lms_mu        gain coefficient  (active iff enable_lms)
        * lms_mu_offset offset learner    (active iff > 0 and enable_lms)
        * lms_mu_inl    INL-table learner (active iff > 0 and enable_lms)
    """
    if alpha is None:
        alpha = params.alpha
    N_int = params.N_int

    rng = np.random.default_rng(params.rng_seed)
    n = params.n_cycles
    T_ref = params.T_ref

    # ----- Pre-generated noise -----
    ref_jitter = _build_ref_jitter(params, n, T_ref, enable_ref_noise, rng)
    if enable_dco_pn:
        phi_dco_excess = generate_pn_sequence(
            n, params.f_ref,
            params.dco_pn_freqs_hz, params.dco_pn_levels_dbchz, rng)
    else:
        phi_dco_excess = np.zeros(n)

    # ----- Block instances -----
    dsm = MASH(order=params.dsm_order,
               quant_levels=params.dsm_quant_levels,
               seed=params.rng_seed + 1)
    bbpd = BBPD(meta_noise_rms_s=params.bbpd_meta_noise_rms_s,
                n_bits=params.bbpd_bits,
                full_scale_s=params.bbpd_full_scale_s,
                rng=np.random.default_rng(params.rng_seed + 2))
    lpf = DigitalPI(Kp=params.Kp, Ki=params.Ki,
                    u_init=u_init if u_init is not None else params.u_init,
                    pole_alpha=params.loop_filter_pole_alpha)
    if params.use_realistic_dco:
        dco = RealisticDCO(f_nominal=params.f_dco_nominal,
                           coarse_lsb_hz=params.realistic_dco_coarse_lsb_hz,
                           fine_lsb_hz=params.realistic_dco_fine_lsb_hz,
                           dither_bits=params.realistic_dco_dither_bits,
                           seed=params.rng_seed + 4)
    else:
        dco = DCO(f_dco_nominal=params.f_dco_nominal, K_dco=params.K_dco)
    fdiv = FractionalDivider(N_int=N_int)
    # When an INL lookup table is in use, the DTC's full-scale should
    # match the typical tau_target swing (≈ ±2 T_DCO for MASH-1-1-1)
    # so the bins are evenly visited. Otherwise it stays at T_ref.
    dtc_full_scale = (params.dtc_inl_table_full_scale_s
                      if params.dtc_inl_table_s is not None else T_ref)
    dtc = DTC(gain_err=params.dtc_gain_err,
              offset_s=params.dtc_offset_s,
              quant_lsb_s=params.dtc_quant_lsb_s,
              inl_amp_s=params.dtc_inl_amp_s,
              inl_periods=params.dtc_inl_periods,
              full_scale_s=dtc_full_scale,
              inl_table_s=params.dtc_inl_table_s)

    # ----- Output buffers -----
    t_ref_arr = np.empty(n)
    t_div_arr = np.empty(n)
    t_div_eff_arr = np.empty(n)
    e_bbpd_arr = np.empty(n)
    s_bbpd_arr = np.empty(n, dtype=int)
    u_arr = np.empty(n)
    m_arr = np.empty(n, dtype=int)
    e_dsm_arr = np.empty(n)
    tau_dtc_arr = np.empty(n)
    f_dco_arr = np.empty(n)
    g_hat_arr = np.empty(n)
    offset_hat_arr = np.empty(n)
    kbb_scale_arr = np.empty(n)
    sigma_est_arr = np.empty(n)

    # ----- State -----
    t_div_prev = 0.0
    u = lpf.u_init
    inv_2pi_f_dco_nom = 1.0 / (2.0 * np.pi * params.f_dco_nominal)
    g_hat = float(params.lms_g_hat_init)
    offset_hat = 0.0
    lms_mu = float(params.lms_mu)
    lms_mu_offset = float(params.lms_mu_offset)
    lms_mu_inl = float(params.lms_mu_inl)
    inl_n_bins = int(params.lms_inl_n_bins)
    inl_table_hat = (np.zeros(inl_n_bins) if lms_mu_inl > 0 else None)
    # K_bb adaptive scaling state
    kbb_alpha = float(params.kbb_track_alpha)
    kbb_target_sigma2 = float(params.kbb_target_sigma_s) ** 2
    sigma2_est = float(params.kbb_target_sigma_s) ** 2     # warm start

    for k in range(n):
        # 1) Reference edge
        t_ref_k = (k + 1) * T_ref + ref_jitter[k]

        # 2) DSM step (modulus for this cycle + residue used by DTC)
        m_k, e_dsm_k = dsm.step(alpha)
        D_k = fdiv.cycles(m_k)

        # 3) DCO advance; convert injected phase noise (rad) to time (s)
        f_dco_k = dco.frequency(u)
        dt_pn = phi_dco_excess[k] * inv_2pi_f_dco_nom
        t_div_k = t_div_prev + D_k / f_dco_k + dt_pn

        # 4) DTC delay. Pre-scale by LMS coefficients.
        if enable_dtc:
            tau_target = g_hat * e_dsm_k * params.T_dco_nominal - offset_hat
            # Optional piecewise INL pre-distortion (centered indexing
            # to MATCH dtc.py's INL-table indexing exactly).
            if inl_table_hat is not None:
                half_fs = params.dtc_inl_table_full_scale_s / 2.0
                norm = (tau_target + half_fs) / max(
                    params.dtc_inl_table_full_scale_s, 1e-30)
                bin_idx = int(np.clip(np.floor(norm * inl_n_bins),
                                      0, inl_n_bins - 1))
                tau_target = tau_target - inl_table_hat[bin_idx]
            else:
                bin_idx = -1
        else:
            tau_target = 0.0
            bin_idx = -1
        tau_dtc_k = float(dtc.apply(tau_target))
        t_div_eff_k = t_div_k + tau_dtc_k

        # 5) BBPD
        e_k = t_div_eff_k - t_ref_k
        s_k = bbpd.decide(e_k)

        # 6) LMS updates
        if enable_lms:
            g_hat = g_hat - lms_mu * s_k * e_dsm_k
            if lms_mu_offset > 0:
                offset_hat = offset_hat - lms_mu_offset * s_k * params.T_dco_nominal
            if inl_table_hat is not None and bin_idx >= 0:
                inl_table_hat[bin_idx] = (
                    inl_table_hat[bin_idx] - lms_mu_inl * s_k * params.T_dco_nominal)

        # K_bb adaptive scaling: update sigma estimate from |e_bbpd| and
        # rescale BBPD output so that K_bb*Kp (i.e. effective loop gain)
        # is invariant to drifts in the BBPD input dither.
        sigma2_est = (1.0 - kbb_alpha) * sigma2_est + kbb_alpha * (e_k * e_k)
        if params.enable_kbb_track:
            kbb_scale = float(np.sqrt(sigma2_est / max(kbb_target_sigma2, 1e-30)))
            s_k_lpf = s_k * kbb_scale
        else:
            kbb_scale = 1.0
            s_k_lpf = s_k

        # 7) Loop filter -> new DCO control word
        u = lpf.step(s_k_lpf)

        # Store
        t_ref_arr[k] = t_ref_k
        t_div_arr[k] = t_div_k
        t_div_eff_arr[k] = t_div_eff_k
        e_bbpd_arr[k] = e_k
        s_bbpd_arr[k] = s_k
        u_arr[k] = u
        m_arr[k] = m_k
        e_dsm_arr[k] = e_dsm_k
        tau_dtc_arr[k] = tau_dtc_k
        f_dco_arr[k] = f_dco_k
        g_hat_arr[k] = g_hat
        offset_hat_arr[k] = offset_hat
        kbb_scale_arr[k] = kbb_scale
        sigma_est_arr[k] = float(np.sqrt(sigma2_est))

        t_div_prev = t_div_k

    return SimResults(
        t_ref=t_ref_arr, t_div=t_div_arr, t_div_eff=t_div_eff_arr,
        e_bbpd=e_bbpd_arr, s_bbpd=s_bbpd_arr, u=u_arr, m=m_arr,
        e_dsm=e_dsm_arr, tau_dtc=tau_dtc_arr, f_dco=f_dco_arr,
        g_hat=g_hat_arr, offset_hat=offset_hat_arr,
        inl_table_hat=inl_table_hat,
        kbb_scale=kbb_scale_arr, sigma_est=sigma_est_arr,
        params=params, alpha=alpha,
        lms_enabled=bool(enable_lms))
