"""Digital PI loop filter.

Input  : BBPD output s[k] in {-1, +1} (or any small integer).
Output : DCO tuning word u[k] = u_init + Kp*s[k] + Ki*sum(s).

The integral accumulator is updated before the output, so the filter
is causal and has unity-delay-free path from input to output.
"""

class DigitalPI:
    def __init__(self, Kp: float, Ki: float, u_init: float = 0.0):
        self.Kp = float(Kp)
        self.Ki = float(Ki)
        self.u_init = float(u_init)
        self.integ = 0.0

    def reset(self, u_init: float = None):
        self.integ = 0.0
        if u_init is not None:
            self.u_init = float(u_init)

    def step(self, s_k: float) -> float:
        self.integ += s_k
        return self.u_init + self.Kp * s_k + self.Ki * self.integ
