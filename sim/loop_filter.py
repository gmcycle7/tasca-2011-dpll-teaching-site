"""Digital PI loop filter with optional smoothing pole.

Input  : BBPD output s[k] in {-1, +1} (or any small integer).
Output : DCO tuning word u[k].

Classic PI:
    u[k] = u_init + Kp * s[k] + Ki * sum(s)

With a 1st-order IIR smoothing pole on the integral branch:
    y_int[k] = pole_alpha * Ki * sum(s) + (1 - pole_alpha) * y_int[k-1]
    u[k]     = u_init + Kp * s[k] + y_int[k]

pole_alpha = 1.0 => no smoothing (default). Smaller alpha = stronger
roll-off above pole_alpha * f_ref / (2*pi). This is the textbook trick
to suppress high-frequency BBPD-driven hunting at the cost of a small
phase-margin reduction.
"""

class DigitalPI:
    def __init__(self, Kp: float, Ki: float, u_init: float = 0.0,
                 pole_alpha: float = 1.0):
        self.Kp = float(Kp)
        self.Ki = float(Ki)
        self.u_init = float(u_init)
        self.pole_alpha = float(pole_alpha)
        self.integ = 0.0
        self.y_int = 0.0     # smoothed integral output

    def reset(self, u_init: float = None):
        self.integ = 0.0
        self.y_int = 0.0
        if u_init is not None:
            self.u_init = float(u_init)

    def step(self, s_k: float) -> float:
        self.integ += s_k
        target = self.Ki * self.integ
        # 1st-order IIR smoothing
        self.y_int = self.pole_alpha * target + (1.0 - self.pole_alpha) * self.y_int
        return self.u_init + self.Kp * s_k + self.y_int
