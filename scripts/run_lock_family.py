"""Lock-transient family.

Three panels sweeping different knobs to teach how each affects the
locking behaviour:

  1) Sweep Kp at fixed Ki — overshoot and ring-down period.
  2) Sweep Ki at fixed Kp — settling time / DC tracking speed.
  3) Sweep initial DCO frequency offset Δf₀ at default Kp/Ki — pull-in
     time vs. how far we start from the target.

Saves:
    results/data/lock_family.csv
    results/figures/lock_family.png
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
from sim.pll_model import run_simulation


N_CYCLES = 40_000


def run_with(df_init_hz: float, **kw) -> tuple[np.ndarray, np.ndarray]:
    p = PLLParams(n_cycles=N_CYCLES)
    p = dataclasses.replace(p, **kw)
    p.f_dco_nominal = p.f_out_target - df_init_hz
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=False, enable_ref_noise=False)
    t_us = np.arange(N_CYCLES) * p.T_ref * 1e6
    df = res.f_dco - p.f_out_target
    return t_us, df * 1e-3   # kHz


def main() -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)

    # ---------- Panel 1: sweep Kp ----------
    ax = axes[0]
    kp_set = [2.0, 4.0, 8.0, 16.0, 32.0]
    for kp in kp_set:
        t, df = run_with(df_init_hz=2e6, Kp=kp)
        ax.plot(t, df, lw=0.7, label=f"Kp = {kp:g}")
    ax.set_ylabel("f_DCO − target [kHz]")
    ax.set_title("Sweep Kp  (Ki = 0.5, Δf₀ = 2 MHz)")
    ax.axhline(0, color="k", lw=0.4, ls="--")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9, ncol=5, loc="upper right")

    # ---------- Panel 2: sweep Ki ----------
    ax = axes[1]
    ki_set = [0.05, 0.1, 0.25, 0.5, 1.0]
    for ki in ki_set:
        t, df = run_with(df_init_hz=2e6, Ki=ki)
        ax.plot(t, df, lw=0.7, label=f"Ki = {ki:g}")
    ax.set_ylabel("f_DCO − target [kHz]")
    ax.set_title("Sweep Ki  (Kp = 8, Δf₀ = 2 MHz)")
    ax.axhline(0, color="k", lw=0.4, ls="--")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9, ncol=5, loc="upper right")

    # ---------- Panel 3: sweep initial offset ----------
    ax = axes[2]
    df_set_mhz = [-4.0, -2.0, -0.5, 0.5, 2.0, 4.0]
    for d in df_set_mhz:
        t, df = run_with(df_init_hz=d * 1e6)
        ax.plot(t, df, lw=0.7, label=f"Δf₀ = {d:+.1f} MHz")
    ax.set_ylabel("f_DCO − target [kHz]")
    ax.set_xlabel("Time [µs]")
    ax.set_title("Sweep initial DCO offset Δf₀  (Kp = 8, Ki = 0.5)")
    ax.axhline(0, color="k", lw=0.4, ls="--")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9, ncol=6, loc="upper right")
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "lock_family.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"swept_values": ["Kp"] * len(kp_set) + ["Ki"] * len(ki_set)
                                   + ["df_init_MHz"] * len(df_set_mhz),
                  "value": kp_set + ki_set + df_set_mhz}).to_csv(
        DATA_DIR / "lock_family.csv", index=False)
    print(f"[lock-family] saved {fig_path}")


if __name__ == "__main__":
    main()
