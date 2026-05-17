"""Digital-to-time converter model.

The DTC accepts an *intended* delay (seconds) and produces an *actual*
delay after applying:
    * relative gain error      tau' = (1 + g) * tau_target
    * static offset            tau' += offset
    * INL ripple               either a sinusoid in code, or a lookup
                               table per code-bin
    * uniform quantization     tau' = round(tau'/lsb) * lsb

All optional; with defaults the DTC is ideal.

When the loop is locked, tau_target equals the DSM residue times
T_DCO_nominal, so the BBPD sees only the residual (cancellation
imperfections + DCO/ref noise).
"""
import numpy as np


class DTC:
    def __init__(self, gain_err: float = 0.0, offset_s: float = 0.0,
                 quant_lsb_s: float = 0.0,
                 inl_amp_s: float = 0.0, inl_periods: int = 0,
                 full_scale_s: float = 25e-9,
                 inl_table_s: np.ndarray = None):
        self.gain_err = float(gain_err)
        self.offset_s = float(offset_s)
        self.quant_lsb_s = float(quant_lsb_s)
        self.inl_amp_s = float(inl_amp_s)
        self.inl_periods = int(inl_periods)
        self.full_scale_s = float(full_scale_s)
        # When a per-code INL lookup table is supplied it OVERRIDES the
        # sinusoidal INL model.
        self.inl_table_s = (np.asarray(inl_table_s, dtype=float)
                            if inl_table_s is not None else None)

    def _inl_correction(self, tau_target):
        if self.inl_table_s is not None and self.inl_table_s.size > 0:
            n = self.inl_table_s.size
            # Map tau_target [0, full_scale_s] to [0, n)
            idx = np.clip(
                np.floor(np.asarray(tau_target) / self.full_scale_s * n).astype(int),
                0, n - 1)
            return self.inl_table_s[idx]
        if self.inl_amp_s > 0 and self.inl_periods > 0:
            phase = 2.0 * np.pi * self.inl_periods * (
                np.asarray(tau_target) / max(self.full_scale_s, 1e-30))
            return self.inl_amp_s * np.sin(phase)
        return np.zeros_like(np.asarray(tau_target, dtype=float))

    def apply(self, tau_target_s):
        tau_target = np.asarray(tau_target_s)
        tau = (1.0 + self.gain_err) * tau_target + self.offset_s
        tau = tau + self._inl_correction(tau_target)
        if self.quant_lsb_s > 0:
            tau = np.round(tau / self.quant_lsb_s) * self.quant_lsb_s
        return tau
