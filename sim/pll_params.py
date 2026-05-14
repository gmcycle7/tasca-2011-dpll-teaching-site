"""Top-level PLLParams dataclass holding every behavioral parameter.

Convention (used consistently across the simulator):
    * Time error is in SECONDS.
    * Positive time error = feedback (DTC-delayed divider) edge LATE
      relative to the reference edge.
    * BBPD output is +1 when feedback is late, -1 when feedback is early.
    * DCO tuning word `u` is dimensionless; f_DCO = f_dco_nominal + K_dco*u.

Source tags in docs/assumptions.md identify which values come from the
paper, which are derived, and which are estimated defaults.
"""
from dataclasses import dataclass


@dataclass
class PLLParams:
    # ----- Reference clock -----
    f_ref: float = 40e6                  # Hz; PAPER (to confirm in PDF)
    ref_jitter_rms_s: float = 80e-15     # ESTIMATED crystal-class

    # ----- Output carrier / DCO nominal -----
    # Default chosen fractional so alpha != 0 exercises the DSM/DTC path.
    f_out_target: float = 3.605e9        # within 2.9-4.0 GHz; PAPER range
    f_dco_nominal: float = 3.605e9       # initial nominal frequency
    K_dco: float = 10e3                  # Hz / LSB; ESTIMATED

    # ----- DSM (MASH 1-1-1) -----
    dsm_order: int = 3                   # 1, 2, or 3
    dsm_quant_levels: int = 1 << 24      # ESTIMATED 24-bit accumulator

    # ----- BBPD -----
    bbpd_meta_noise_rms_s: float = 0.0   # s; optional decision noise

    # ----- DTC -----
    dtc_gain_err: float = 0.0            # relative; 0 = ideal
    dtc_offset_s: float = 0.0            # s
    dtc_quant_lsb_s: float = 1e-12       # s; ESTIMATED 1 ps LSB
    dtc_inl_amp_s: float = 0.0           # s; sinusoidal-INL amplitude
    dtc_inl_periods: int = 4             # ripple periods over full scale

    # ----- Digital loop filter (PI) -----
    # ESTIMATED. With default K_dco = 10 kHz/LSB and f_ref = 40 MHz these
    # settle a ~1 MHz initial frequency offset in ~5 us. Tune if needed.
    Kp: float = 8.0
    Ki: float = 0.5
    u_init: float = 0.0                  # initial DCO tuning word

    # ----- LMS adaptive DTC gain calibration -----
    # When enabled in run_simulation, the digital-side DTC drive is scaled
    # by an adaptive coefficient g_hat updated as
    #   g_hat[k+1] = g_hat[k] - mu * s_bbpd[k] * e_dsm[k]
    # which drives g_hat toward 1/(1 + dtc_gain_err) to null the residual
    # correlation between BBPD output and DSM residue.
    lms_mu: float = 1e-4                 # ESTIMATED; demo-friendly step
    lms_g_hat_init: float = 1.0          # start from "I think the gain is right"

    # ----- DCO phase noise template -----
    dco_pn_freqs_hz: tuple = (1e3, 10e3, 100e3, 1e6, 10e6, 100e6)
    dco_pn_levels_dbchz: tuple = (-65, -95, -110, -120, -135, -148)

    # ----- Reference spur (optional) -----
    # A deterministic sinusoidal component added to the reference edge
    # time. With nonzero amplitude this models supply / substrate
    # leakage of f_ref that periodically shifts the reference edge.
    ref_spur_amp_s: float = 0.0          # peak amplitude [s]
    ref_spur_freq_hz: float = 0.0        # offset frequency [Hz]

    # ----- Simulation control -----
    n_cycles: int = 200_000
    rng_seed: int = 12345

    # ---- Convenience accessors ----
    @property
    def T_ref(self) -> float:
        return 1.0 / self.f_ref

    @property
    def T_dco_nominal(self) -> float:
        return 1.0 / self.f_dco_nominal

    @property
    def N_frac(self) -> float:
        return self.f_out_target / self.f_ref

    @property
    def alpha(self) -> float:
        n = self.N_frac
        return n - int(n)

    @property
    def N_int(self) -> int:
        return int(self.N_frac)
