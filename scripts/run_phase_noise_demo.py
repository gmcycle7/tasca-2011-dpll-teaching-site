"""Closed-loop phase-noise spectrum and integrated RMS jitter.

Runs the full PLL (DSM dither, ideal DTC, DCO PN, reference jitter on),
extracts the DCO-equivalent excess phase, estimates L(f), and integrates
to RMS time jitter over a configurable band.

Saves:
    results/data/phase_noise.csv
    results/data/phase_noise_summary.csv
    results/figures/phase_noise.png
"""
from __future__ import annotations
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.pll_params import PLLParams
from sim.pll_model import run_simulation, excess_phase_at_dco
from sim.phase_noise import estimate_psd
from sim.jitter import integrated_rms_jitter_s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=400_000)
    # Paper uses 3 kHz - 30 MHz for the 560 fs RMS jitter number.
    # Our sim samples at f_ref = 40 MHz so the highest meaningful PSD bin
    # is f_ref/2 = 20 MHz; integrating beyond that is aliased.
    ap.add_argument("--f-lo", type=float, default=3e3)
    ap.add_argument("--f-hi", type=float, default=20e6)
    args = ap.parse_args()

    p = PLLParams(n_cycles=args.n_cycles)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    phi = excess_phase_at_dco(res, trim_settling=0.3)
    f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 15))

    rms_jit = integrated_rms_jitter_s(f, L, args.f_lo, args.f_hi, p.f_out_target)

    fig, ax = plt.subplots(figsize=(8, 5))
    mask = f > p.f_ref / len(phi)
    ax.semilogx(f[mask], L[mask], lw=0.8, label="Simulated closed-loop L(f)")
    # Overlay the DCO free-running PN template for context
    L_dco_open = np.interp(np.log10(np.clip(f, 1, None)),
                            np.log10(p.dco_pn_freqs_hz),
                            p.dco_pn_levels_dbchz)
    ax.semilogx(f[mask], L_dco_open[mask], "--", lw=0.7,
                color="gray", label="DCO open-loop template")
    ax.set_xlabel("Offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title(
        f"Closed-loop phase noise — behavioral approximation\n"
        f"Integrated jitter ({args.f_lo:.0e}..{args.f_hi:.0e} Hz) = "
        f"{rms_jit*1e15:.0f} fs RMS")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend()
    behavioral_caption(ax)
    fig.tight_layout()
    fig_path = FIG_DIR / "phase_noise.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"f_hz": f, "L_dbchz": L}).to_csv(
        DATA_DIR / "phase_noise.csv", index=False)
    pd.DataFrame([{
        "f_lo_hz": args.f_lo,
        "f_hi_hz": args.f_hi,
        "f_carrier_hz": p.f_out_target,
        "rms_jitter_s": rms_jit,
    }]).to_csv(DATA_DIR / "phase_noise_summary.csv", index=False)

    print(f"[pn]  integrated jitter ({args.f_lo:.0e}..{args.f_hi:.0e} Hz)"
          f" = {rms_jit*1e15:.0f} fs RMS")
    print(f"[pn]  saved {fig_path}")


if __name__ == "__main__":
    main()
