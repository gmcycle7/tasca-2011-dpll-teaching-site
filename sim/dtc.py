"""Digital-to-time converter model.

The DTC accepts an *intended* delay (seconds) and produces an *actual*
delay after applying:
    * relative gain error      tau' = (1 + g) * tau_target
    * static offset            tau' += offset
    * uniform quantization     tau' = round(tau'/lsb) * lsb
    * static INL ripple        tau' += A * sin(2*pi*N_periods*tau_target/T_FS)

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
                 full_scale_s: float = 25e-9):
        self.gain_err = float(gain_err)
        self.offset_s = float(offset_s)
        self.quant_lsb_s = float(quant_lsb_s)
        self.inl_amp_s = float(inl_amp_s)
        self.inl_periods = int(inl_periods)
        self.full_scale_s = float(full_scale_s)

    def apply(self, tau_target_s):
        tau = (1.0 + self.gain_err) * np.asarray(tau_target_s) + self.offset_s
        if self.inl_amp_s > 0 and self.inl_periods > 0:
            phase = 2.0 * np.pi * self.inl_periods * (
                np.asarray(tau_target_s) / max(self.full_scale_s, 1e-30))
            tau = tau + self.inl_amp_s * np.sin(phase)
        if self.quant_lsb_s > 0:
            tau = np.round(tau / self.quant_lsb_s) * self.quant_lsb_s
        return tau
