"""Thin wrapper that turns a DSM output into a per-cycle divider modulus.

The divider counts D[k] = N_int + m[k] DCO cycles before emitting an
edge. Where the simulator needs the (modulus, residue) pair, it reads
them directly from the DSM. This file is kept for diagrammatic clarity
and to be the natural extension point for adding modulus randomization,
duty-cycle effects, etc.
"""

class FractionalDivider:
    def __init__(self, N_int: int):
        self.N_int = int(N_int)

    def cycles(self, m_k: int) -> int:
        return self.N_int + int(m_k)
