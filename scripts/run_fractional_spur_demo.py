"""Fractional-spur behavior demo.

Picks a fractional ratio close to integer (alpha small) so that the
first fractional spur sits at low offset and is easy to see. Runs the
loop with DTC gain error and INL ENABLED to make spurs prominent, then
shows how they collapse when the DTC is calibrated/ideal.

Saves:
    results/data/fractional_spurs.csv
    results/data/fractional_spurs_table.csv
    results/figures/fractional_spurs.png
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
from sim.spurs import detect_spurs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=400_000)
    ap.add_argument("--alpha", type=float, default=0.01,
                    help="fractional part of N (small => low-offset spurs)")
    args = ap.parse_args()

    # Set the carrier so the fractional part equals args.alpha
    f_ref = 40e6
    N_int = 90
    f_out = (N_int + args.alpha) * f_ref

    # Case A: imperfect DTC (gain error + INL) -> spurs prominent
    p_bad = PLLParams(n_cycles=args.n_cycles, f_ref=f_ref, f_out_target=f_out,
                      f_dco_nominal=f_out,
                      dtc_gain_err=0.1, dtc_inl_amp_s=2e-12, dtc_inl_periods=8)
    # Case B: ideal DTC -> spurs much smaller
    p_good = PLLParams(n_cycles=args.n_cycles, f_ref=f_ref, f_out_target=f_out,
                       f_dco_nominal=f_out)

    res_bad = run_simulation(p_bad, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True)
    res_good = run_simulation(p_good, enable_dtc=True,
                              enable_dco_pn=True, enable_ref_noise=True)

    phi_bad = excess_phase_at_dco(res_bad, trim_settling=0.3)
    phi_good = excess_phase_at_dco(res_good, trim_settling=0.3)

    f_b, L_b = estimate_psd(phi_bad, fs=p_bad.f_ref,
                            nperseg=min(len(phi_bad), 1 << 15))
    f_g, L_g = estimate_psd(phi_good, fs=p_good.f_ref,
                            nperseg=min(len(phi_good), 1 << 15))

    spurs_bad = detect_spurs(f_b, L_b, args.alpha, p_bad.f_ref)
    spurs_good = detect_spurs(f_g, L_g, args.alpha, p_good.f_ref)

    fig, ax = plt.subplots(figsize=(8, 5))
    mb = f_b > p_bad.f_ref / len(phi_bad)
    mg = f_g > p_good.f_ref / len(phi_good)
    ax.semilogx(f_b[mb], L_b[mb], lw=0.7, color="C3",
                label=f"DTC g_err=0.1, INL=2 ps")
    ax.semilogx(f_g[mg], L_g[mg], lw=0.7, color="C0",
                label="DTC ideal")
    for s in spurs_bad[:6]:
        ax.axvline(s["f_target"], color="C3", ls=":", lw=0.5, alpha=0.6)
        ax.annotate(f"k={s['k']}", xy=(s["f_peak"], s["L_dbchz"]),
                    fontsize=7, color="C3",
                    xytext=(0, 5), textcoords="offset points", ha="center")
    ax.set_xlabel("Offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title(
        f"Fractional spurs at alpha={args.alpha}, f_spur_1≈{args.alpha*p_bad.f_ref/1e3:.0f} kHz\n"
        "behavioral approximation")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend()
    behavioral_caption(ax)
    fig.tight_layout()
    fig_path = FIG_DIR / "fractional_spurs.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    # Save PSDs and spur tables
    pd.DataFrame({"f_hz": f_b, "L_dbchz_bad": L_b,
                  "L_dbchz_ideal": np.interp(f_b, f_g, L_g)}).to_csv(
        DATA_DIR / "fractional_spurs.csv", index=False)
    rows = []
    for tag, lst in (("bad", spurs_bad), ("ideal", spurs_good)):
        for s in lst:
            rows.append({"case": tag, **s})
    pd.DataFrame(rows).to_csv(
        DATA_DIR / "fractional_spurs_table.csv", index=False)

    if spurs_bad:
        worst = max(spurs_bad, key=lambda r: r["L_dbchz"])
        print(f"[spur] worst-case spur (bad DTC) "
              f"@ {worst['f_peak']/1e3:.1f} kHz = {worst['L_dbchz']:.1f} dBc/Hz")
    print(f"[spur] saved {fig_path}")


if __name__ == "__main__":
    main()
