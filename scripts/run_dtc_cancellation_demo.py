"""DTC cancellation demonstration.

Runs the locked PLL twice: once with the DTC disabled (the BBPD sees
the full DSM-induced time error) and once with the ideal DTC. Both runs
record the BBPD-input time-error trace and its PSD so the cancellation
benefit can be visualised.

Saves:
    results/data/dtc_cancellation.csv
    results/figures/dtc_cancellation.png
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
from sim.pll_model import run_simulation
from sim.phase_noise import estimate_psd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=120_000)
    args = ap.parse_args()

    p = PLLParams(n_cycles=args.n_cycles)
    # Keep DCO/ref noise off to isolate the DSM/DTC contribution
    res_no_dtc = run_simulation(p, enable_dtc=False,
                                enable_dco_pn=False, enable_ref_noise=False)
    res_dtc = run_simulation(p, enable_dtc=True,
                             enable_dco_pn=False, enable_ref_noise=False)

    n = p.n_cycles
    trim = n // 2  # ignore lock transient
    e_nod = res_no_dtc.e_bbpd[trim:]
    e_dtc = res_dtc.e_bbpd[trim:]

    # Time-domain phase-error sequence -> equivalent DCO excess phase
    phi_nod = 2 * np.pi * p.f_dco_nominal * (e_nod - e_nod.mean())
    phi_dtc = 2 * np.pi * p.f_dco_nominal * (e_dtc - e_dtc.mean())

    f_nod, L_nod = estimate_psd(phi_nod, fs=p.f_ref)
    f_dtc, L_dtc = estimate_psd(phi_dtc, fs=p.f_ref)

    # ---- Plot ----
    fig, axes = plt.subplots(3, 1, figsize=(8, 9))
    n_show = min(2000, len(e_nod))
    t_us = np.arange(n_show) * p.T_ref * 1e6

    axes[0].plot(t_us, e_nod[:n_show] * 1e12, lw=0.6, color="C3")
    axes[0].set_ylabel("BBPD err [ps]  (DTC OFF)")
    axes[0].set_title("DTC cancellation of DSM-induced time error "
                      "(behavioral approximation)")
    axes[0].grid(True, alpha=0.4)

    axes[1].plot(t_us, e_dtc[:n_show] * 1e12, lw=0.6, color="C0")
    axes[1].set_ylabel("BBPD err [ps]  (DTC ON)")
    axes[1].set_xlabel("Time [us]")
    axes[1].grid(True, alpha=0.4)
    behavioral_caption(axes[1])

    mask_nod = f_nod > p.f_ref / len(phi_nod)
    mask_dtc = f_dtc > p.f_ref / len(phi_dtc)
    axes[2].semilogx(f_nod[mask_nod], L_nod[mask_nod], lw=0.8, label="DTC OFF",
                     color="C3")
    axes[2].semilogx(f_dtc[mask_dtc], L_dtc[mask_dtc], lw=0.8, label="DTC ON",
                     color="C0")
    axes[2].set_xlabel("Offset frequency [Hz]")
    axes[2].set_ylabel("L(f) [dBc/Hz]")
    axes[2].set_title("Equivalent DCO phase-noise PSD with vs. without DTC")
    axes[2].grid(True, which="both", alpha=0.4)
    axes[2].legend()
    behavioral_caption(axes[2])

    fig.tight_layout()
    fig_path = FIG_DIR / "dtc_cancellation.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    # ---- CSV ----
    pd.DataFrame({
        "f_hz": f_nod,
        "L_dbchz_dtc_off": L_nod,
    }).to_csv(DATA_DIR / "dtc_cancellation_psd_off.csv", index=False)
    pd.DataFrame({
        "f_hz": f_dtc,
        "L_dbchz_dtc_on": L_dtc,
    }).to_csv(DATA_DIR / "dtc_cancellation_psd_on.csv", index=False)
    pd.DataFrame({
        "k": np.arange(len(e_nod)),
        "e_bbpd_off_s": e_nod,
        "e_bbpd_on_s": e_dtc,
    }).to_csv(DATA_DIR / "dtc_cancellation.csv", index=False)

    print(f"[dtc] RMS BBPD err  OFF = {e_nod.std()*1e9:.2f} ns")
    print(f"[dtc] RMS BBPD err  ON  = {e_dtc.std()*1e12:.2f} ps")
    print(f"[dtc] saved {fig_path}")


if __name__ == "__main__":
    main()
