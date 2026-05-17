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
from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np


@dataclass
class PLLParams:
    # ----- Reference clock -----
    f_ref: float = 40e6                  # Hz; PAPER (to confirm in PDF)
    ref_jitter_rms_s: float = 80e-15     # ESTIMATED crystal-class
    # Optional reference phase-noise template; if both freqs and levels
    # are set, the simulator generates coloured ref jitter instead of
    # white sigma noise.
    ref_pn_freqs_hz: Optional[Tuple[float, ...]] = None
    ref_pn_levels_dbchz: Optional[Tuple[float, ...]] = None

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
    bbpd_bits: int = 1                   # 1 = sign(); >1 = mid-tread quantiser
    bbpd_full_scale_s: float = 5e-12     # used only when bbpd_bits > 1

    # ----- DTC -----
    dtc_gain_err: float = 0.0            # relative; 0 = ideal
    dtc_offset_s: float = 0.0            # s
    dtc_quant_lsb_s: float = 1e-12       # s; ESTIMATED 1 ps LSB
    dtc_inl_amp_s: float = 0.0           # s; sinusoidal-INL amplitude
    dtc_inl_periods: int = 4             # ripple periods over full scale
    # Optional lookup table: per-code residual delay (length 2^N_codes).
    # When set, this REPLACES the sinusoidal INL model.
    dtc_inl_table_s: Optional[np.ndarray] = None
    dtc_inl_table_full_scale_s: float = 25e-9

    # ----- Digital loop filter (PI) -----
    # ESTIMATED. With default K_dco = 10 kHz/LSB and f_ref = 40 MHz these
    # settle a ~1 MHz initial frequency offset in ~5 us. Tune if needed.
    Kp: float = 8.0
    Ki: float = 0.5
    u_init: float = 0.0                  # initial DCO tuning word
    # Optional smoothing pole on the integral branch.  alpha in (0,1] is
    # the IIR coefficient: y[k] = alpha*x[k] + (1-alpha)*y[k-1].
    # alpha = 1.0 => no smoothing (default).
    loop_filter_pole_alpha: float = 1.0

    # ----- LMS adaptive DTC calibration -----
    lms_mu: float = 1e-4                 # gain-cal step
    lms_g_hat_init: float = 1.0
    # Offset-cal (subtract a learned constant from DTC drive)
    lms_mu_offset: float = 0.0           # 0 = disabled
    # INL-cal (piecewise: 16-bin table of corrections, learned per code-bin)
    lms_mu_inl: float = 0.0              # 0 = disabled
    lms_inl_n_bins: int = 16

    # ----- DCO phase noise template (corner-point form) -----
    dco_pn_freqs_hz: tuple = (1e3, 10e3, 100e3, 1e6, 10e6, 100e6)
    dco_pn_levels_dbchz: tuple = (-65, -95, -110, -120, -135, -148)

    # ----- Optional realistic DCO (coarse + dithered fine) -----
    use_realistic_dco: bool = False
    realistic_dco_coarse_lsb_hz: float = 1e6
    realistic_dco_fine_lsb_hz: float = 1e3
    realistic_dco_dither_bits: int = 16

    # ----- Reference spur (optional) -----
    ref_spur_amp_s: float = 0.0
    ref_spur_freq_hz: float = 0.0

    # ----- K_bb adaptive scaling (loop-BW invariance) -----
    # An online EMA estimate of sigma at BBPD input is used to scale
    # the BBPD output before it hits the loop filter; this keeps the
    # K_bb*Kp product (and hence the closed-loop bandwidth) constant
    # as the in-loop dither drifts with PVT.
    enable_kbb_track: bool = False
    kbb_track_alpha: float = 1e-3        # EMA coefficient
    kbb_target_sigma_s: float = 5e-13    # target sigma at BBPD input

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
