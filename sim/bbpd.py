"""Bang-bang phase detector / single-bit TDC.

Output: sign(time_error + decision_noise).
Convention: positive time error => output +1.

Includes a static method for the small-signal linearized gain
    K_bb = sqrt(2/pi) / sigma_in        (output per second of input)
which is the classical result for a sign() detector with zero-mean
Gaussian input of standard deviation sigma_in.
"""
import numpy as np


class BBPD:
    def __init__(self, meta_noise_rms_s: float = 0.0, rng=None):
        self.meta_noise_rms_s = float(meta_noise_rms_s)
        self.rng = rng if rng is not None else np.random.default_rng(0)

    def decide(self, time_error_s: float) -> int:
        if self.meta_noise_rms_s > 0:
            time_error_s = time_error_s + self.rng.normal(
                0.0, self.meta_noise_rms_s)
        if time_error_s > 0.0:
            return 1
        if time_error_s < 0.0:
            return -1
        return int(self.rng.choice([-1, 1]))

    @staticmethod
    def linearized_gain(sigma_in_s: float) -> float:
        if sigma_in_s <= 0:
            return float("inf")
        return float(np.sqrt(2.0 / np.pi) / sigma_in_s)
