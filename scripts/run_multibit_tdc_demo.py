"""Multi-bit TDC vs. BBPD+DTC architecture comparison.

Four closed-loop runs on the same DCO, DSM, and loop bandwidth:

  1. BBPD + ideal DTC                 (paper's choice)
  2. 8-bit TDC, no digital cancel     (DSM dither dominates)
  3. 8-bit TDC + digital DSM cancel   (the digital twin of DTC)
  4. 12-bit TDC + digital DSM cancel  (same architecture, finer LSB)

Cases 3 and 4 match the BBPD+DTC floor closely; case 2 doesn't. The
takeaway: a multi-bit TDC can match BBPD+DTC, but only if you pair it
with the same residue cancellation that the DTC implements — making
the two architectures noise-equivalent and the cost of the TDC bits
the only remaining trade-off.

Saves:
    results/data/multibit_tdc.csv
    results/figures/multibit_tdc.png
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
from sim.multibit_tdc import run_simulation_tdc, tdc_excess_phase
from sim.phase_noise import estimate_psd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=200_000)
    args = ap.parse_args()

    p = PLLParams(n_cycles=args.n_cycles)

    # 1) BBPD + ideal DTC
    res_bbpd = run_simulation(p, enable_dtc=True,
                              enable_dco_pn=True, enable_ref_noise=True)
    phi_bbpd = excess_phase_at_dco(res_bbpd, trim_settling=0.3)
    f_b, L_b = estimate_psd(phi_bbpd, fs=p.f_ref,
                            nperseg=min(len(phi_bbpd), 1 << 15))

    # 2) 8-bit TDC, no cancel
    res_8nc = run_simulation_tdc(p, n_bits=8,
                                 enable_dsm_cancel=False,
                                 enable_dco_pn=True, enable_ref_noise=True)
    phi_8nc = tdc_excess_phase(res_8nc, trim_settling=0.5)
    f_8n, L_8n = estimate_psd(phi_8nc, fs=p.f_ref,
                              nperseg=min(len(phi_8nc), 1 << 15))

    # 3) 8-bit TDC + digital cancel
    res_8c = run_simulation_tdc(p, n_bits=8,
                                enable_dsm_cancel=True,
                                enable_dco_pn=True, enable_ref_noise=True)
    phi_8c = tdc_excess_phase(res_8c, trim_settling=0.3)
    f_8c, L_8c = estimate_psd(phi_8c, fs=p.f_ref,
                              nperseg=min(len(phi_8c), 1 << 15))

    # 4) 12-bit TDC + digital cancel
    res_12c = run_simulation_tdc(p, n_bits=12,
                                 enable_dsm_cancel=True,
                                 enable_dco_pn=True, enable_ref_noise=True)
    phi_12c = tdc_excess_phase(res_12c, trim_settling=0.3)
    f_12, L_12 = estimate_psd(phi_12c, fs=p.f_ref,
                              nperseg=min(len(phi_12c), 1 << 15))

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(9, 5.5))
    series = [
        (f_b,  L_b,  "BBPD + ideal DTC (paper)",          "C0", 1.0),
        (f_8n, L_8n, "8-bit TDC, NO digital cancel",       "C3", 0.8),
        (f_8c, L_8c, "8-bit TDC + digital DSM cancel",     "C2", 0.9),
        (f_12, L_12, "12-bit TDC + digital DSM cancel",    "C4", 0.9),
    ]
    for f, L, lab, c, lw in series:
        mask = f > p.f_ref / len(phi_bbpd)
        ax.semilogx(f[mask], L[mask], lw=lw, label=lab, color=c)
    ax.set_xlabel("Offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Architecture contrast — BBPD+DTC vs. multi-bit TDC "
                 "(behavioral approximation)")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(loc="upper right", fontsize=9)
    behavioral_caption(ax)
    fig.tight_layout()
    fig_path = FIG_DIR / "multibit_tdc.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "f_hz": f_b,
        "L_bbpd_dtc_dbchz":   L_b,
        "L_tdc8_nocancel":    np.interp(f_b, f_8n, L_8n),
        "L_tdc8_with_cancel": np.interp(f_b, f_8c, L_8c),
        "L_tdc12_with_cancel": np.interp(f_b, f_12, L_12),
    }).to_csv(DATA_DIR / "multibit_tdc.csv", index=False)

    def floor(f, L):
        return float(np.median(L[(f > 1e6) & (f < 5e6)]))
    print(f"[mtdc] BBPD+DTC floor:            {floor(f_b, L_b):.1f} dBc/Hz")
    print(f"[mtdc] 8-bit TDC NO cancel:       {floor(f_8n, L_8n):.1f} dBc/Hz")
    print(f"[mtdc] 8-bit TDC + cancel:        {floor(f_8c, L_8c):.1f} dBc/Hz")
    print(f"[mtdc] 12-bit TDC + cancel:       {floor(f_12, L_12):.1f} dBc/Hz")
    print(f"[mtdc] saved {fig_path}")


if __name__ == "__main__":
    main()
