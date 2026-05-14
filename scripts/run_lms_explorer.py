"""LMS DTC-gain calibration explorer.

Four panels:
  1) g_hat trajectory family: sweep μ at fixed gain_err=0.1.
  2) Steady-state misadjustment vs μ (log-log).
  3) g_hat trajectory family: sweep gain_err at fixed μ=1e-4.
  4) Closed-loop L(f) before and after LMS convergence.

Saves:
    results/data/lms_explorer.csv
    results/figures/lms_explorer.png
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


def main() -> None:
    base = PLLParams(n_cycles=200_000)

    # ---------- Panel 1: μ sweep ----------
    mus = np.array([1e-5, 3e-5, 1e-4, 3e-4, 1e-3])
    traj_mu = {}
    misadj  = []
    for mu in mus:
        p = dataclasses.replace(base, dtc_gain_err=0.10, lms_mu=float(mu))
        res = run_simulation(p, enable_dtc=True, enable_dco_pn=True,
                             enable_ref_noise=True, enable_lms=True)
        traj_mu[mu] = res.g_hat
        tail = res.g_hat[int(0.8 * base.n_cycles):]
        target = 1.0 / 1.10
        misadj.append(np.std(tail))
        print(f"[lms] μ={mu:.0e}  steady g_hat={tail.mean():.4f}  "
              f"std={tail.std():.5f}  target={target:.4f}")

    # ---------- Panel 3: gain_err sweep ----------
    g_errs = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]
    traj_g = {}
    for g in g_errs:
        p = dataclasses.replace(base, dtc_gain_err=float(g), lms_mu=1e-4)
        res = run_simulation(p, enable_dtc=True, enable_dco_pn=True,
                             enable_ref_noise=True, enable_lms=True)
        traj_g[g] = res.g_hat

    # ---------- Panel 4: PSD before/after ----------
    p_imp = dataclasses.replace(base, dtc_gain_err=0.10, lms_mu=1e-4)
    res_off = run_simulation(p_imp, enable_dtc=True, enable_dco_pn=True,
                             enable_ref_noise=True, enable_lms=False)
    res_on  = run_simulation(p_imp, enable_dtc=True, enable_dco_pn=True,
                             enable_ref_noise=True, enable_lms=True)
    phi_off = excess_phase_at_dco(res_off, trim_settling=0.4)
    phi_on  = excess_phase_at_dco(res_on,  trim_settling=0.7)
    f_off, L_off = estimate_psd(phi_off, fs=p_imp.f_ref,
                                nperseg=min(len(phi_off), 1 << 15))
    f_on,  L_on  = estimate_psd(phi_on,  fs=p_imp.f_ref,
                                nperseg=min(len(phi_on),  1 << 15))

    # ---------- Plot ----------
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    ax = axes[0, 0]
    t_us = np.arange(base.n_cycles) * base.T_ref * 1e6
    for mu, g in traj_mu.items():
        ax.plot(t_us, g, lw=0.8, label=f"μ = {mu:.0e}")
    ax.axhline(1 / 1.10, color="k", lw=0.6, ls="--", label="target 0.909")
    ax.axhline(1.00,    color="grey", lw=0.4, ls=":", label="init 1.00")
    ax.set_xlabel("time [µs]")
    ax.set_ylabel("g_hat")
    ax.set_title("LMS g_hat trajectory — sweep μ  (gain_err = 0.10)")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    ax.set_xlim(0, 1500)

    ax = axes[0, 1]
    ax.loglog(mus, np.array(misadj), "o-", lw=1.0, color="C3")
    ax.set_xlabel("LMS step size μ")
    ax.set_ylabel("steady-state std(g_hat)")
    ax.set_title("Misadjustment vs μ — faster ↔ noisier trade-off")
    ax.grid(True, which="both", alpha=0.4)

    ax = axes[1, 0]
    for g, gh in traj_g.items():
        target = 1 / (1 + g)
        ax.plot(t_us, gh, lw=0.8,
                label=f"gain_err = {g:+.2f}  → target {target:.3f}")
    ax.set_xlabel("time [µs]")
    ax.set_ylabel("g_hat")
    ax.set_title("LMS g_hat trajectory — sweep gain_err  (μ = 1e-4)")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    ax.set_xlim(0, 1500)

    ax = axes[1, 1]
    mask_off = f_off > p_imp.f_ref / len(phi_off)
    mask_on  = f_on  > p_imp.f_ref / len(phi_on)
    ax.semilogx(f_off[mask_off], L_off[mask_off], lw=0.7, color="C3",
                label="LMS off (gain_err = 0.10)")
    ax.semilogx(f_on[mask_on],  L_on[mask_on],   lw=0.7, color="C0",
                label="LMS on  (after convergence)")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop L(f) — LMS off vs on")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "lms_explorer.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"mu": mus, "g_hat_std_tail": misadj}).to_csv(
        DATA_DIR / "lms_explorer.csv", index=False)
    print(f"[lms] saved {fig_path}")


if __name__ == "__main__":
    main()
