"""Digitally controlled oscillator (linearized).

f_DCO(u) = f_dco_nominal + K_dco * u    (Hz)

The simulator samples DCO state once per reference cycle. Per-cycle DCO
phase noise is injected in `pll_model.py` from a pre-generated colored
sequence (see `phase_noise.generate_pn_sequence`).
"""

class DCO:
    def __init__(self, f_dco_nominal: float, K_dco: float):
        self.f_nominal = float(f_dco_nominal)
        self.K_dco = float(K_dco)

    def frequency(self, u: float) -> float:
        return self.f_nominal + self.K_dco * u

    def period(self, u: float) -> float:
        return 1.0 / self.frequency(u)
