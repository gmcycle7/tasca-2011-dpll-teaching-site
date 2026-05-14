"""Multi-bit TDC alternative simulator (for the architecture-contrast page).

A behavioral closed-loop sim that uses a multi-bit time-to-digital
converter instead of the bang-bang detector. The DSM-driven divider is
still in place; we simply skip the DTC and let the TDC measure the
hundreds-of-ps DSM dither directly.

This is intentionally NOT what the paper builds. It exists so the
architecture-contrast page has a real, runnable comparison: same DCO,
same DSM, same loop bandwidth, different detector. The trade-off you
see is "bit budget for the TDC vs. the DTC's analog calibration burden".
"""
from dataclasses import dataclass
import numpy as np

from .pll_params import PLLParams
from .dsm import MASH
from .dco import DCO
from .fractional_divider import FractionalDivider
from .loop_filter import DigitalPI
from .phase_noise import generate_pn_sequence


class MultiBitTDC:
    """Mid-tread N-bit TDC of full-scale ±FS_s/2 in seconds.

    Output is the quantized time error in seconds (not in codes), so the
    downstream loop filter gain has the same units as the BBPD case
    times one LSB.
    """

    def __init__(self, n_bits: int, full_scale_s: float,
                 thermal_noise_rms_s: float = 0.0,
                 inl_rms_lsb: float = 0.0, rng=None):
        self.n_bits = int(n_bits)
        self.levels = 1 << self.n_bits
        self.full_scale_s = float(full_scale_s)
        self.lsb_s = self.full_scale_s / self.levels
        self.thermal_noise_rms_s = float(thermal_noise_rms_s)
        self.rng = rng if rng is not None else np.random.default_rng(0)
        # Per-code INL table (fixed-pattern offsets in seconds)
        self._inl = self.rng.normal(
            0.0, inl_rms_lsb * self.lsb_s, self.levels)

    def measure(self, time_error_s: float) -> float:
        e = time_error_s
        if self.thermal_noise_rms_s > 0:
            e = e + self.rng.normal(0.0, self.thermal_noise_rms_s)
        half = self.levels // 2
        idx = int(np.clip(np.round(e / self.lsb_s), -half, half - 1))
        return idx * self.lsb_s + self._inl[idx + half]


@dataclass
class TDCSimResults:
    t_ref: np.ndarray
    t_div: np.ndarray
    e_in: np.ndarray         # raw time error before TDC quantization
    e_q: np.ndarray          # TDC-quantized error
    e_after_cancel: np.ndarray  # after optional digital DSM-residue subtraction
    u: np.ndarray
    f_dco: np.ndarray
    params: PLLParams


def run_simulation_tdc(
    params: PLLParams,
    n_bits: int = 8,
    full_scale_s: float = None,
    tdc_inl_rms_lsb: float = 0.0,
    tdc_thermal_rms_s: float = 0.0,
    enable_dco_pn: bool = True,
    enable_ref_noise: bool = True,
    enable_dsm_cancel: bool = False,
    cancel_gain: float = 1.0,
    sigma_ref_s: float = None,
) -> TDCSimResults:
    """Run one closed-loop sim using a multi-bit TDC instead of BBPD.

    Two flavours, selected by `enable_dsm_cancel`:

    1. **No cancellation.** TDC measures the full divider edge time
       error (including the hundreds-of-ps DSM dither). The loop has
       to track that or be heavily band-limited.

    2. **Digital DSM cancellation.** The simulator subtracts
       `cancel_gain * e_dsm[k] * T_DCO_nom` from the TDC output
       before the loop filter. This is the digital twin of what the
       analog DTC does in the paper's architecture; with
       `cancel_gain = 1` it ideally cancels the DSM contribution.

    For a fair loop-bandwidth comparison across cases, the TDC output
    is normalized by `sigma_ref_s` (so the LPF input is dimensionless,
    roughly in BBPD-equivalent units). Auto-default:
    `T_DCO_nominal / 800` ≈ 0.35 ps.
    """
    rng = np.random.default_rng(params.rng_seed)
    n = params.n_cycles
    T_ref = params.T_ref
    alpha = params.alpha
    N_int = params.N_int

    if full_scale_s is None:
        full_scale_s = 4.0 * params.T_dco_nominal
    if sigma_ref_s is None:
        sigma_ref_s = params.T_dco_nominal / 800.0

    ref_jitter = (rng.normal(0.0, params.ref_jitter_rms_s, n)
                  if enable_ref_noise and params.ref_jitter_rms_s > 0
                  else np.zeros(n))
    phi_dco_excess = (generate_pn_sequence(
        n, params.f_ref,
        params.dco_pn_freqs_hz, params.dco_pn_levels_dbchz, rng)
        if enable_dco_pn else np.zeros(n))

    dsm = MASH(order=params.dsm_order,
               quant_levels=params.dsm_quant_levels,
               seed=params.rng_seed + 1)
    dco = DCO(f_dco_nominal=params.f_dco_nominal, K_dco=params.K_dco)
    fdiv = FractionalDivider(N_int=N_int)
    tdc = MultiBitTDC(n_bits=n_bits, full_scale_s=full_scale_s,
                      thermal_noise_rms_s=tdc_thermal_rms_s,
                      inl_rms_lsb=tdc_inl_rms_lsb,
                      rng=np.random.default_rng(params.rng_seed + 3))
    lpf = DigitalPI(Kp=params.Kp, Ki=params.Ki, u_init=params.u_init)

    t_ref_arr = np.empty(n); t_div_arr = np.empty(n)
    e_in_arr = np.empty(n);  e_q_arr  = np.empty(n)
    e_ac_arr = np.empty(n)
    u_arr    = np.empty(n);  f_dco_arr = np.empty(n)

    t_div_prev = 0.0
    u = lpf.u_init
    inv_2pi_f0 = 1.0 / (2.0 * np.pi * params.f_dco_nominal)

    for k in range(n):
        t_ref_k = (k + 1) * T_ref + ref_jitter[k]
        m_k, e_dsm_k = dsm.step(alpha)
        D_k = fdiv.cycles(m_k)

        f_dco_k = dco.frequency(u)
        dt_pn = phi_dco_excess[k] * inv_2pi_f0
        t_div_k = t_div_prev + D_k / f_dco_k + dt_pn

        e_in = t_div_k - t_ref_k
        e_q = tdc.measure(e_in)

        # Digital DSM cancellation: subtract predicted residue
        if enable_dsm_cancel:
            e_ac = e_q - cancel_gain * e_dsm_k * params.T_dco_nominal
        else:
            e_ac = e_q

        u = lpf.step(e_ac / sigma_ref_s)

        t_ref_arr[k] = t_ref_k; t_div_arr[k] = t_div_k
        e_in_arr[k] = e_in;     e_q_arr[k] = e_q
        e_ac_arr[k] = e_ac;     u_arr[k] = u
        f_dco_arr[k] = f_dco_k
        t_div_prev = t_div_k

    return TDCSimResults(t_ref=t_ref_arr, t_div=t_div_arr,
                         e_in=e_in_arr, e_q=e_q_arr,
                         e_after_cancel=e_ac_arr,
                         u=u_arr, f_dco=f_dco_arr, params=params)


def tdc_excess_phase(res: TDCSimResults, trim_settling: float = 0.5) -> np.ndarray:
    """DCO-equivalent excess phase from a TDC sim, ready for Welch."""
    p = res.params
    n = len(res.t_div)
    delta = res.t_div - (np.arange(n) + 1) * p.T_ref
    delta = delta[int(trim_settling * n):]
    return 2.0 * np.pi * p.f_dco_nominal * (delta - np.mean(delta))
