"""Delta-sigma modulator for fractional-N divider control.

Supports order = 1, 2, or 3 (MASH 1-1-1). The modulator takes a
normalized fractional input alpha in [0, 1) and emits an integer dither
sequence m[k]. We also report the cumulative residue

    e_dsm[k] = (alpha-sum over k steps) - sum_{j<=k} m[j]            (cycles)

which is exactly the displacement (in DCO periods) of the k-th divider
edge from where an ideal fractional divider would have emitted it.
The DTC is programmed to cancel this displacement.

Sign convention: if e_dsm > 0, the integer divider has emitted FEWER
DCO cycles than the ideal fractional divider would, so the divider
edge is EARLIER than ideal by e_dsm * T_dco. The DTC delays the
divider edge by tau_dtc = e_dsm * T_dco_nominal (positive delay) to
align with the reference.
"""
import numpy as np


class MASH:
    """Cascaded first-order accumulators (1, 2, or 3 stages)."""

    def __init__(self, order: int, quant_levels: int, seed: int = 0):
        if order not in (1, 2, 3):
            raise ValueError("MASH order must be 1, 2, or 3")
        self.order = order
        self.M = int(quant_levels)
        self.acc1 = 0
        self.acc2 = 0
        self.acc3 = 0
        # History for error-cancellation network
        self.y2_prev = 0
        self.y3_prev = 0
        self.y3_prev2 = 0
        self.rng = np.random.default_rng(seed)
        self._alpha_accum = 0.0
        self._cum_y = 0

    def step(self, alpha: float):
        """Advance one cycle. Returns (m_k, e_dsm_after_k_steps)."""
        x = int(round(alpha * self.M))

        # Stage 1
        self.acc1 += x
        y1 = self.acc1 // self.M
        self.acc1 -= y1 * self.M  # residue in [0, M)

        if self.order == 1:
            y_out = y1
        else:
            # Stage 2 input: stage-1 residue
            self.acc2 += self.acc1
            y2 = self.acc2 // self.M
            self.acc2 -= y2 * self.M

            if self.order == 2:
                # Error-cancel: y = y1 + (1-z^-1) y2
                y_out = y1 + (y2 - self.y2_prev)
                self.y2_prev = y2
            else:
                # Stage 3 input: stage-2 residue
                self.acc3 += self.acc2
                y3 = self.acc3 // self.M
                self.acc3 -= y3 * self.M
                # Error-cancel: y = y1 + (1-z^-1) y2 + (1-z^-1)^2 y3
                y_out = (y1
                         + (y2 - self.y2_prev)
                         + (y3 - 2 * self.y3_prev + self.y3_prev2))
                self.y3_prev2 = self.y3_prev
                self.y3_prev = y3
                self.y2_prev = y2

        # Cumulative residue using running mean (robust to alpha changes)
        self._alpha_accum += alpha
        self._cum_y += y_out
        e_dsm = self._alpha_accum - self._cum_y
        return int(y_out), float(e_dsm)
