"""Core lock test: start with an initial DCO frequency offset and watch
the digital loop filter pull the DCO tuning word in to lock.

Saves:
    results/data/core_lock_test.csv
    results/figures/core_lock_test.png
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=40_000)
    ap.add_argument("--df-init-hz", type=float, default=2e6,
                    help="initial DCO frequency error to lock out (Hz)")
    args = ap.parse_args()

    p = PLLParams(n_cycles=args.n_cycles)
    # Force an initial frequency error by shifting f_dco_nominal so the
    # zero-tuning DCO sits args.df_init_hz away from the desired carrier.
    p.f_dco_nominal = p.f_out_target - args.df_init_hz

    # Disable DCO and reference phase noise to make the lock transient
    # easy to read; DSM dither and DTC cancellation are on.
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=False, enable_ref_noise=False)

    k = np.arange(p.n_cycles)
    t_us = k * p.T_ref * 1e6
    df_dco = res.f_dco - p.f_out_target

    # ---- Plot ----
    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    axes[0].plot(t_us, df_dco * 1e-3, lw=0.6)
    axes[0].set_ylabel("f_DCO − f_target [kHz]")
    axes[0].set_title(
        "Core lock test — Tasca-style DPLL (behavioral approximation)\n"
        f"Init offset = {args.df_init_hz/1e6:.2f} MHz, "
        f"Kp={p.Kp}, Ki={p.Ki}, DTC on")
    axes[0].axhline(0, color="k", lw=0.4, ls="--")
    axes[0].grid(True, alpha=0.4)

    axes[1].plot(t_us, res.u, lw=0.6)
    axes[1].set_ylabel("DCO tuning word u [LSB]")
    axes[1].grid(True, alpha=0.4)

    axes[2].plot(t_us, res.e_bbpd * 1e12, lw=0.4)
    axes[2].set_ylabel("BBPD input err [ps]")
    axes[2].set_xlabel("Time [us]")
    axes[2].grid(True, alpha=0.4)
    behavioral_caption(axes[2])

    fig.tight_layout()
    fig_path = FIG_DIR / "core_lock_test.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    # ---- CSV ----
    df = pd.DataFrame({
        "k": k,
        "t_s": k * p.T_ref,
        "f_dco_hz": res.f_dco,
        "df_dco_hz": df_dco,
        "u": res.u,
        "e_bbpd_s": res.e_bbpd,
        "s_bbpd": res.s_bbpd,
        "m": res.m,
        "e_dsm_cycles": res.e_dsm,
        "tau_dtc_s": res.tau_dtc,
    })
    csv_path = DATA_DIR / "core_lock_test.csv"
    df.to_csv(csv_path, index=False)

    # ---- Summary ----
    tail = slice(int(0.8 * p.n_cycles), None)
    print(f"[lock] saved {csv_path}")
    print(f"[lock] saved {fig_path}")
    print(f"[lock] final df_dco = {df_dco[tail].mean()*1e-3:+.2f} kHz")
    print(f"[lock] tail RMS BBPD error = {res.e_bbpd[tail].std()*1e12:.2f} ps")


if __name__ == "__main__":
    main()
