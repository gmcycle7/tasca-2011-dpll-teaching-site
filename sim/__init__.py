"""Behavioral simulator for the Tasca 2011 JSSC fractional-N DPLL.

All signals use SI units. The canonical "phase error" is in SECONDS:
the time difference between the (DTC-delayed) feedback edge and the
reference edge, positive = feedback edge LATE.

This is a behavioral approximation, NOT a silicon-accurate model.
"""
