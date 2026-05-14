"""Top-level phase-domain DPLL simulator.

One simulation step = one reference cycle = one feedback divider cycle.
We track absolute time of every reference and divider edge in SECONDS.

State per step k:
    t_ref[k]      reference edge time (with optional reference jitter)
    m[k]          DSM integer dither -> divider modulus D = N_int + m
    e_dsm[k]      cumulative DSM residue (fractional cycles); this is
                  what an ideal DTC would cancel
    t_div[k]      divider edge time before the DTC (advances by
                  D/f_DCO + DCO-phase-noise contribution)
    tau_dtc[k]    DTC delay applied to that edge
    t_div_eff[k]  divider edge time after DTC delay (compared to ref)
    e_bbpd[k]     t_div_eff - t_ref           (the BBPD's input)
    s[k]          BBPD output (+/-1)
    u[k]          DCO tuning word from the digital loop filter
    f_dco[k]      DCO frequency = f_dco_nominal + K_dco*u

Sign convention recap:
    * e_bbpd > 0   feedback edge is LATE        -> BBPD outputs +1
    * s[k] = +1    pushes u positive            -> DCO speeds up
    * Faster DCO   shortens future divider periods -> e_bbpd decreases
"""
from dataclasses import dataclass
import numpy as np

from .pll_params import PLLParams
from .dsm import MASH
from .dtc import DTC
from .bbpd import BBPD
from .loop_filter import DigitalPI
from .dco import DCO
from .fractional_divider import FractionalDivider
from .phase_noise import generate_pn_sequence


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
    params: PLLParams
    alpha: float
    lms_enabled: bool


def excess_phase_at_dco(res: SimResults, trim_settling: float = 0.5) -> np.ndarray:
    """Return DCO-equivalent excess phase (rad) sampled at f_ref.

    delta[k] = t_div_eff[k] - k*T_ref          (time error at divider out)
    phi_dco_excess[k] = 2*pi*f_dco_nominal*delta[k]

    DC offset (mean of the trimmed steady-state tail) is removed before
    PSD estimation. `trim_settling` is the fraction of the head to drop.
    """
    p = res.params
    n = len(res.t_div_eff)
    delta = res.t_div_eff - (np.arange(n) + 1) * p.T_ref
    i0 = int(trim_settling * n)
    delta = delta[i0:]
    delta = delta - np.mean(delta)
    return 2.0 * np.pi * p.f_dco_nominal * delta


def run_simulation(params: PLLParams,
                   alpha: float = None,
                   enable_dtc: bool = True,
                   enable_dco_pn: bool = True,
                   enable_ref_noise: bool = True,
                   enable_lms: bool = False,
                   u_init: float = None) -> SimResults:
    """Run one closed-loop time-domain simulation.

    If `enable_lms` is True, an LMS update is applied to the DTC gain
    coefficient g_hat per cycle:
        g_hat <- g_hat - mu * s_bbpd[k] * e_dsm[k]
    g_hat scales the DSM residue *before* it is passed to the DTC, so
    the steady-state value converges to 1 / (1 + dtc_gain_err).
    """
    if alpha is None:
        alpha = params.alpha
    N_int = params.N_int

    rng = np.random.default_rng(params.rng_seed)
    n = params.n_cycles
    T_ref = params.T_ref

    # ----- Pre-generated noise -----
    if enable_ref_noise and params.ref_jitter_rms_s > 0:
        ref_jitter = rng.normal(0.0, params.ref_jitter_rms_s, n)
    else:
        ref_jitter = np.zeros(n)

    # Optional deterministic reference spur (periodic supply / substrate
    # leakage of f_ref shifting the reference edge time).
    if params.ref_spur_amp_s > 0 and params.ref_spur_freq_hz > 0:
        k_idx = np.arange(n)
        ref_jitter = ref_jitter + params.ref_spur_amp_s * np.sin(
            2.0 * np.pi * params.ref_spur_freq_hz * k_idx * T_ref)

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
                rng=np.random.default_rng(params.rng_seed + 2))
    lpf = DigitalPI(Kp=params.Kp, Ki=params.Ki,
                    u_init=u_init if u_init is not None else params.u_init)
    dco = DCO(f_dco_nominal=params.f_dco_nominal, K_dco=params.K_dco)
    fdiv = FractionalDivider(N_int=N_int)
    dtc = DTC(gain_err=params.dtc_gain_err,
              offset_s=params.dtc_offset_s,
              quant_lsb_s=params.dtc_quant_lsb_s,
              inl_amp_s=params.dtc_inl_amp_s,
              inl_periods=params.dtc_inl_periods,
              full_scale_s=T_ref)

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

    # ----- State -----
    t_div_prev = 0.0
    u = lpf.u_init
    inv_2pi_f_dco_nom = 1.0 / (2.0 * np.pi * params.f_dco_nominal)
    g_hat = float(params.lms_g_hat_init)
    lms_mu = float(params.lms_mu)

    for k in range(n):
        # 1) Reference edge.
        #    Both the divider and the reference start aligned at t = 0;
        #    the FIRST emitted divider edge corresponds to the FIRST
        #    post-zero reference edge at t = T_ref, so index from 1.
        t_ref_k = (k + 1) * T_ref + ref_jitter[k]

        # 2) DSM step (modulus for this cycle + residue used by DTC)
        m_k, e_dsm_k = dsm.step(alpha)
        D_k = fdiv.cycles(m_k)

        # 3) DCO advance; convert injected phase noise (rad) to time (s)
        f_dco_k = dco.frequency(u)
        dt_pn = phi_dco_excess[k] * inv_2pi_f_dco_nom
        t_div_k = t_div_prev + D_k / f_dco_k + dt_pn

        # 4) DTC delay. The DSM residue is pre-scaled by the LMS-adapted
        #    coefficient g_hat; in steady state g_hat -> 1/(1 + gain_err).
        tau_target = g_hat * e_dsm_k * params.T_dco_nominal if enable_dtc else 0.0
        tau_dtc_k = float(dtc.apply(tau_target))
        t_div_eff_k = t_div_k + tau_dtc_k

        # 5) BBPD
        e_k = t_div_eff_k - t_ref_k
        s_k = bbpd.decide(e_k)

        # 6) LMS update of DTC gain coefficient (before loop filter so
        #    g_hat[k] is the value used at step k).
        if enable_lms:
            g_hat = g_hat - lms_mu * s_k * e_dsm_k

        # 7) Loop filter -> new DCO control word
        u = lpf.step(s_k)

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

        t_div_prev = t_div_k

    return SimResults(
        t_ref=t_ref_arr, t_div=t_div_arr, t_div_eff=t_div_eff_arr,
        e_bbpd=e_bbpd_arr, s_bbpd=s_bbpd_arr, u=u_arr, m=m_arr,
        e_dsm=e_dsm_arr, tau_dtc=tau_dtc_arr, f_dco=f_dco_arr,
        g_hat=g_hat_arr, params=params, alpha=alpha,
        lms_enabled=bool(enable_lms))
