"""Two-band DCO model: coarse capacitor bank + dithered fine bank.

Real LC-DCOs reach sub-Hz frequency steps by combining
  * a coarse capacitor bank with large LSB (~MHz / step),
  * a fine bank with smaller LSB (~kHz / step),
  * and a 1st-order DSM that dithers a sub-LSB code into the fine bank.

The effective frequency, averaged over many samples, has resolution
much finer than any single LSB of either bank.

This module is a teaching companion to `sim/dco.py`; the main
simulator still uses the simpler linear DCO.
"""
from __future__ import annotations
import numpy as np


class RealisticDCO:
    def __init__(self, f_nominal: float,
                 coarse_lsb_hz: float = 1e6,
                 fine_lsb_hz: float = 1e3,
                 fine_bits: int = 8,
                 dither_bits: int = 16,
                 dither_order: int = 1,
                 seed: int = 0):
        self.f_nominal = float(f_nominal)
        self.coarse_lsb = float(coarse_lsb_hz)
        self.fine_lsb = float(fine_lsb_hz)
        self.fine_bits = int(fine_bits)
        self.dither_M = 1 << int(dither_bits)
        self.dither_order = int(dither_order)
        self.acc = 0  # 1st-order DSM accumulator for sub-LSB dither
        self.rng = np.random.default_rng(seed)

    def frequency(self, control_word: float) -> float:
        """Map a high-resolution control word to an instantaneous frequency.

        control_word is in fine_lsb units. The integer part picks a fine
        code; the fractional part is dithered into the next code by a
        1st-order DSM running at the call rate.
        """
        cw_int  = int(np.floor(control_word))
        cw_frac = control_word - cw_int          # 0 <= frac < 1
        # Dither
        self.acc += int(round(cw_frac * self.dither_M))
        dither_step = self.acc // self.dither_M
        self.acc -= dither_step * self.dither_M
        # Final integer fine-bank code applied this cycle
        cw_applied = cw_int + dither_step
        # Coarse bank split (top of cw_applied) — rounded to coarse LSB
        coarse_steps = (cw_applied * self.fine_lsb) // self.coarse_lsb
        fine_offset = cw_applied - coarse_steps * int(self.coarse_lsb / self.fine_lsb)
        f = (self.f_nominal
             + coarse_steps * self.coarse_lsb
             + fine_offset * self.fine_lsb)
        return float(f)


def trace_frequency(dco: RealisticDCO, control_word: float, n: int) -> np.ndarray:
    """Return n samples of dco.frequency(control_word) (dither is stateful)."""
    return np.array([dco.frequency(control_word) for _ in range(n)])
