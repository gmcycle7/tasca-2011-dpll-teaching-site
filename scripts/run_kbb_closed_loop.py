"""K_bb adaptive tracking — closed-loop integration demo.

Sweep DCO phase-noise level (so the dither at the BBPD input scales
with it) and compare two scenarios:

  1) Static Kp/Ki: as σ_in grows, K_bb shrinks, loop gain falls,
     closed-loop bandwidth shifts.
  2) K_bb-tracked: an EMA of e_bbpd^2 estimates σ, and the BBPD output
     is multiplied by σ/σ_target before the loop filter. K_bb·Kp
     product (and hence the loop BW) stays put.

Three panels:
  1) Steady-state σ at the BBPD input vs. DCO PN shift, both cases.
  2) Steady-state K_bb scale (1.0 if tracker off; ≈ σ/σ_target if on).
  3) Closed-loop L(f) overlay for ±10 dB PN shifts — with tracking
     the curves nearly overlap; without, they don't.

Saves:
    results/data/kbb_closed_loop.csv
    results/figures/kbb_closed_loop.png
"""
from __future__ import annotations
import dataclasses

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.pll_params import PLLParams
from sim.pll_model import run_simulation, excess_phase_at_dco
from sim.phase_noise import estimate_psd


def run_at_shift(pn_shift_db: float, track: bool):
    base = PLLParams(n_cycles=80_000)
    new_levels = tuple(float(L + pn_shift_db) for L in base.dco_pn_levels_dbchz)
    p = dataclasses.replace(base,
                            dco_pn_levels_dbchz=new_levels,
                            enable_kbb_track=track,
                            kbb_target_sigma_s=5e-13,    # 0.5 ps target
                            kbb_track_alpha=2e-3)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    return res, p


def main() -> None:
    shifts_db = [-10, -5, 0, 5, 10]

    sigma_no  = []   # tail sigma without tracking
    sigma_yes = []   # tail sigma with tracking
    scale_yes = []   # tail mean kbb_scale with tracking
    spectra = {}

    for sh in shifts_db:
        # No tracking
        r_n, p_n = run_at_shift(sh, track=False)
        tail = r_n.e_bbpd[int(0.6 * len(r_n.e_bbpd)):]
        sigma_no.append(float(tail.std()) * 1e12)
        # Tracking
        r_y, p_y = run_at_shift(sh, track=True)
        tail_y = r_y.e_bbpd[int(0.6 * len(r_y.e_bbpd)):]
        sigma_yes.append(float(tail_y.std()) * 1e12)
        scale_yes.append(float(r_y.kbb_scale[int(0.8 * len(r_y.kbb_scale)):].mean()))
        # Spectra for ±10 dB extremes only
        if sh in (-10, 0, 10):
            phi_n = excess_phase_at_dco(r_n, trim_settling=0.5)
            phi_y = excess_phase_at_dco(r_y, trim_settling=0.5)
            f_n, L_n = estimate_psd(phi_n, fs=p_n.f_ref,
                                    nperseg=min(len(phi_n), 1 << 14))
            f_y, L_y = estimate_psd(phi_y, fs=p_y.f_ref,
                                    nperseg=min(len(phi_y), 1 << 14))
            spectra[sh] = (f_n, L_n, f_y, L_y)
        print(f"[kbb-closed] PN shift {sh:+3} dB  no-track σ = {sigma_no[-1]:.2f} ps  "
              f"track σ = {sigma_yes[-1]:.2f} ps  scale = {scale_yes[-1]:.2f}")

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    ax = axes[0]
    ax.plot(shifts_db, sigma_no, "o-", lw=1.0, color="C3",
            label="no tracking")
    ax.plot(shifts_db, sigma_yes, "s-", lw=1.0, color="C0",
            label="K_bb tracking")
    ax.set_xlabel("DCO PN floor shift [dB]")
    ax.set_ylabel("tail σ at BBPD input [ps]")
    ax.set_title("σ_in vs. PN floor — tracker holds it near target")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    ax = axes[1]
    ax.plot(shifts_db, scale_yes, "o-", lw=1.0, color="C0")
    ax.axhline(1.0, color="k", lw=0.4, ls="--")
    ax.set_xlabel("DCO PN floor shift [dB]")
    ax.set_ylabel("tail mean kbb_scale")
    ax.set_title("Adaptive scale factor (with tracking on)")
    ax.grid(True, alpha=0.4)

    ax = axes[2]
    for sh, (f_n, L_n, f_y, L_y) in spectra.items():
        col = {-10: "C2", 0: "C7", 10: "C3"}[sh]
        m = f_n > 1e3
        ax.semilogx(f_n[m], L_n[m], lw=0.5, color=col, alpha=0.5,
                    label=f"{sh:+d} dB no-track")
        ax.semilogx(f_y[m], L_y[m], lw=0.8, color=col,
                    label=f"{sh:+d} dB tracked")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop L(f) — tracker keeps the shape consistent")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=8, ncol=3, loc="upper right")
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "kbb_closed_loop.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"pn_shift_db": shifts_db,
                  "sigma_no_track_ps": sigma_no,
                  "sigma_track_ps": sigma_yes,
                  "kbb_scale_mean": scale_yes}).to_csv(
        DATA_DIR / "kbb_closed_loop.csv", index=False)
    print(f"[kbb-closed] saved {fig_path}")


if __name__ == "__main__":
    main()
