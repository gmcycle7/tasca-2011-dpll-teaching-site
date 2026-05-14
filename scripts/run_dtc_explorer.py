"""DTC explorer.

Four panels:
  1) Ideal DTC characteristic + four impairments (gain, offset, INL, quant).
  2) Residual delay error after DTC vs. input — same four impairments.
  3) INL profile shapes: sinusoidal at different ripple counts.
  4) Spur level vs. INL amplitude (closed-loop measurement).

Saves:
    results/data/dtc_explorer.csv
    results/figures/dtc_explorer.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.dtc import DTC
from sim.pll_params import PLLParams
from sim.pll_model import run_simulation, excess_phase_at_dco
from sim.phase_noise import estimate_psd
from sim.spurs import detect_spurs


T_FS = 25e-9                                  # one ref period
tau_target = np.linspace(0, T_FS, 1001)        # 0 ... 25 ns input grid


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # ---------- Panel 1: characteristic curves ----------
    cases = [
        ("ideal",                 DTC(full_scale_s=T_FS), "C0"),
        ("gain_err = +0.10",      DTC(gain_err=0.10,  full_scale_s=T_FS), "C3"),
        ("offset = 200 ps",       DTC(offset_s=200e-12, full_scale_s=T_FS), "C2"),
        ("INL 8 cycles × 1 ps",   DTC(inl_amp_s=1e-12, inl_periods=8, full_scale_s=T_FS), "C4"),
        ("LSB = 50 ps quant",     DTC(quant_lsb_s=50e-12, full_scale_s=T_FS), "C1"),
    ]
    ax = axes[0, 0]
    for label, dtc, color in cases:
        tau_out = np.array([dtc.apply(t) for t in tau_target])
        ax.plot(tau_target * 1e9, tau_out * 1e9, lw=0.9, color=color, label=label)
    ax.plot(tau_target * 1e9, tau_target * 1e9, lw=0.5, ls=":", color="k",
            label="y = x")
    ax.set_xlabel("intended τ_target [ns]")
    ax.set_ylabel("DTC output τ_actual [ns]")
    ax.set_title("DTC characteristic — one impairment at a time")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8, loc="upper left")

    # ---------- Panel 2: residual error ----------
    ax = axes[0, 1]
    for label, dtc, color in cases:
        tau_out = np.array([dtc.apply(t) for t in tau_target])
        err = (tau_out - tau_target) * 1e12
        ax.plot(tau_target * 1e9, err, lw=0.9, color=color, label=label)
    ax.axhline(0, color="k", lw=0.4)
    ax.set_xlabel("τ_target [ns]")
    ax.set_ylabel("residual error τ_out − τ_target [ps]")
    ax.set_title("Residual delay error — each impairment alone")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8, loc="upper right")

    # ---------- Panel 3: INL profile shapes ----------
    ax = axes[1, 0]
    for n_periods, color in zip((2, 4, 8, 16), ("C0", "C2", "C3", "C4")):
        dtc = DTC(inl_amp_s=2e-12, inl_periods=n_periods, full_scale_s=T_FS)
        tau_out = np.array([dtc.apply(t) for t in tau_target])
        ax.plot(tau_target * 1e9, (tau_out - tau_target) * 1e12,
                lw=0.8, color=color, label=f"{n_periods} ripples / full-scale")
    ax.set_xlabel("τ_target [ns]")
    ax.set_ylabel("INL residual [ps]")
    ax.set_title("Sinusoidal INL — varying spatial frequency  (amp = 2 ps)")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8, loc="upper right")

    # ---------- Panel 4: worst spur vs INL amplitude (closed loop) ----------
    inl_amps_ps = np.array([0.0, 0.5, 1.0, 2.0, 4.0, 8.0])
    worst = np.zeros_like(inl_amps_ps)
    for i, a in enumerate(inl_amps_ps):
        p = PLLParams(n_cycles=60_000, dtc_inl_amp_s=a * 1e-12, dtc_inl_periods=8)
        res = run_simulation(p, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True)
        phi = excess_phase_at_dco(res, trim_settling=0.4)
        f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 14))
        spurs = detect_spurs(f, L, p.alpha, p.f_ref, n_harmonics=6)
        worst[i] = max((s["L_dbchz"] for s in spurs), default=float("nan"))
        print(f"[dtc] INL amp = {a:.1f} ps  ->  worst spur = {worst[i]:.1f} dBc/Hz")
    ax = axes[1, 1]
    ax.plot(inl_amps_ps, worst, "o-", lw=1.0, color="C3")
    ax.set_xlabel("DTC INL amplitude [ps]")
    ax.set_ylabel("worst predicted-comb spur [dBc/Hz]")
    ax.set_title("Closed-loop spur level vs. DTC INL amplitude")
    ax.grid(True, alpha=0.4)

    behavioral_caption(axes[1, 1])
    fig.suptitle("DTC behaviour and impairments — behavioural approximation",
                 y=1.0)
    fig.tight_layout()
    fig_path = FIG_DIR / "dtc_explorer.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "inl_amp_ps": inl_amps_ps,
        "worst_spur_dbchz": worst,
    }).to_csv(DATA_DIR / "dtc_explorer.csv", index=False)
    print(f"[dtc] saved {fig_path}")


if __name__ == "__main__":
    main()
