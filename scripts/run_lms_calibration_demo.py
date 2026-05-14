"""LMS adaptive DTC gain-calibration demo.

Runs the loop with a deliberate DTC gain error (default 10%) twice:
    A) LMS disabled  -> residual BBPD error / spurs dominated by mis-cal
    B) LMS enabled   -> g_hat converges to 1/(1+gain_err)

Saves:
    results/data/lms_calibration.csv
    results/data/lms_calibration_psd.csv
    results/figures/lms_calibration.png
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=200_000)
    ap.add_argument("--gain-err", type=float, default=0.10,
                    help="DTC gain error to be corrected by LMS (relative)")
    ap.add_argument("--mu", type=float, default=1e-4,
                    help="LMS step size")
    args = ap.parse_args()

    target_g_hat = 1.0 / (1.0 + args.gain_err)
    p_off = PLLParams(n_cycles=args.n_cycles,
                      dtc_gain_err=args.gain_err, lms_mu=args.mu)
    p_on = PLLParams(n_cycles=args.n_cycles,
                     dtc_gain_err=args.gain_err, lms_mu=args.mu)

    res_off = run_simulation(p_off, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True,
                             enable_lms=False)
    res_on = run_simulation(p_on, enable_dtc=True,
                            enable_dco_pn=True, enable_ref_noise=True,
                            enable_lms=True)

    n = p_on.n_cycles
    k = np.arange(n)
    t_us = k * p_on.T_ref * 1e6

    # PSDs comparing converged steady state
    phi_off = excess_phase_at_dco(res_off, trim_settling=0.5)
    phi_on = excess_phase_at_dco(res_on, trim_settling=0.7)
    f_off, L_off = estimate_psd(phi_off, fs=p_off.f_ref)
    f_on, L_on = estimate_psd(phi_on, fs=p_on.f_ref)

    fig, axes = plt.subplots(3, 1, figsize=(9, 9))

    axes[0].plot(t_us, res_on.g_hat, lw=0.8, label="LMS on")
    axes[0].plot(t_us, res_off.g_hat, lw=0.8, label="LMS off",
                 color="gray", alpha=0.8)
    axes[0].axhline(target_g_hat, color="C2", ls="--", lw=0.8,
                    label=f"target 1/(1+gerr)={target_g_hat:.3f}")
    axes[0].set_title("LMS DTC-gain calibration "
                      "(behavioral approximation)")
    axes[0].set_ylabel("g_hat")
    axes[0].set_xlabel("Time [us]")
    axes[0].grid(True, alpha=0.4)
    axes[0].legend(loc="best")

    win = max(200, n // 200)
    e_off_rms = pd.Series(res_off.e_bbpd ** 2).rolling(win, min_periods=win).mean().pow(0.5)
    e_on_rms = pd.Series(res_on.e_bbpd ** 2).rolling(win, min_periods=win).mean().pow(0.5)
    axes[1].semilogy(t_us, e_off_rms * 1e12, lw=0.8, label="LMS off",
                     color="C3")
    axes[1].semilogy(t_us, e_on_rms * 1e12, lw=0.8, label="LMS on",
                     color="C0")
    axes[1].set_ylabel("Rolling BBPD RMS err [ps]")
    axes[1].set_xlabel("Time [us]")
    axes[1].grid(True, which="both", alpha=0.4)
    axes[1].legend()

    mo = f_off > p_off.f_ref / len(phi_off)
    mn = f_on > p_on.f_ref / len(phi_on)
    axes[2].semilogx(f_off[mo], L_off[mo], lw=0.8, color="C3",
                     label="Steady state, LMS off")
    axes[2].semilogx(f_on[mn], L_on[mn], lw=0.8, color="C0",
                     label="Steady state, LMS on")
    axes[2].set_xlabel("Offset frequency [Hz]")
    axes[2].set_ylabel("L(f) [dBc/Hz]")
    axes[2].grid(True, which="both", alpha=0.4)
    axes[2].legend()
    behavioral_caption(axes[2])
    fig.tight_layout()
    fig_path = FIG_DIR / "lms_calibration.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "k": k, "t_s": k * p_on.T_ref,
        "g_hat_lms_on": res_on.g_hat, "g_hat_lms_off": res_off.g_hat,
        "e_bbpd_on_s": res_on.e_bbpd, "e_bbpd_off_s": res_off.e_bbpd,
    }).to_csv(DATA_DIR / "lms_calibration.csv", index=False)
    pd.DataFrame({"f_hz": f_off,
                  "L_dbchz_off": L_off,
                  "L_dbchz_on": np.interp(f_off, f_on, L_on)}).to_csv(
        DATA_DIR / "lms_calibration_psd.csv", index=False)

    print(f"[lms] target g_hat = {target_g_hat:.4f}")
    print(f"[lms] LMS-off final g_hat = {res_off.g_hat[-1]:.4f}")
    print(f"[lms] LMS-on  final g_hat = {res_on.g_hat[-1]:.4f}  "
          f"(mean last 10%: {res_on.g_hat[int(0.9*n):].mean():.4f})")
    print(f"[lms] BBPD tail RMS  OFF = {res_off.e_bbpd[-10000:].std()*1e12:.2f} ps")
    print(f"[lms] BBPD tail RMS  ON  = {res_on.e_bbpd[-10000:].std()*1e12:.2f} ps")
    print(f"[lms] saved {fig_path}")


if __name__ == "__main__":
    main()
