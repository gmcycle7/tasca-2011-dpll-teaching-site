"""Bang-bang phase detector / single-bit TDC + multi-bit option.

Default behaviour: sign(time_error + decision_noise) emits {-1, +1}.
With n_bits > 1, the detector becomes a small mid-tread quantiser
spanning ±full_scale/2; useful for the architecture-comparison page
that asks "does adding bits to the detector buy you anything?".

Sign convention: positive time error => output > 0.

The static method `linearized_gain` returns
    K_bb = sqrt(2/pi) / sigma_in
which is the classical result for a sign() detector with zero-mean
Gaussian input of standard deviation sigma_in. For multi-bit operation
the small-signal gain is 1 (output in seconds tracks input in seconds)
until saturation; that limit is not encoded here.
"""
import numpy as np


class BBPD:
    def __init__(self, meta_noise_rms_s: float = 0.0,
                 n_bits: int = 1, full_scale_s: float = 5e-12,
                 rng=None):
        self.meta_noise_rms_s = float(meta_noise_rms_s)
        self.n_bits = int(n_bits)
        self.full_scale_s = float(full_scale_s)
        if self.n_bits > 1:
            self.levels = 1 << self.n_bits
            self.lsb_s = self.full_scale_s / self.levels
        else:
            self.levels = 2
            self.lsb_s = self.full_scale_s          # only used by callers
        self.rng = rng if rng is not None else np.random.default_rng(0)

    def decide(self, time_error_s: float):
        if self.meta_noise_rms_s > 0:
            time_error_s = time_error_s + self.rng.normal(
                0.0, self.meta_noise_rms_s)
        if self.n_bits == 1:
            if time_error_s > 0.0:
                return 1
            if time_error_s < 0.0:
                return -1
            return int(self.rng.choice([-1, 1]))
        # Multi-bit mid-tread quantiser; return signed integer code,
        # bounded in [-levels/2, +levels/2-1].
        half = self.levels // 2
        return int(np.clip(np.round(time_error_s / self.lsb_s),
                           -half, half - 1))

    def linearised_continuous_output(self, time_error_s: float) -> float:
        """Same as decide() but returns a real-valued output (for multi-bit).

        For 1-bit this is just sign(); for N-bit it is the quantised
        signed code times the LSB so the units stay in seconds. Used by
        the loop filter when multi-bit detector is selected.
        """
        if self.n_bits == 1:
            return float(self.decide(time_error_s))
        return float(self.decide(time_error_s)) * self.lsb_s

    @staticmethod
    def linearized_gain(sigma_in_s: float) -> float:
        if sigma_in_s <= 0:
            return float("inf")
        return float(np.sqrt(2.0 / np.pi) / sigma_in_s)
