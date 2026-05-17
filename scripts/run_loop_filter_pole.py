"""Effect of the loop-filter smoothing pole on tail RMS and L(f).

Three panels:
  1) Closed-loop BBPD-input error trace, no pole vs three pole values.
  2) Tail RMS BBPD-input error vs pole alpha.
  3) Closed-loop L(f) comparison (top-of-band roll-off).

Saves:
    results/data/loop_filter_pole.csv
    results/figures/loop_filter_pole.png
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


def run_with(pole_alpha: float):
    p = dataclasses.replace(PLLParams(n_cycles=80_000),
                            loop_filter_pole_alpha=pole_alpha)
    return run_simulation(p, enable_dtc=True,
                          enable_dco_pn=True, enable_ref_noise=True), p


def main() -> None:
    alphas = [1.0, 0.3, 0.1, 0.03]
    results = {a: run_with(a) for a in alphas}

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: BBPD-input trace ----------
    ax = axes[0]
    for a, (res, p) in results.items():
        tail = res.e_bbpd[int(0.4 * len(res.e_bbpd)):]
        t = np.arange(min(3000, len(tail))) * p.T_ref * 1e6
        ax.plot(t, tail[:len(t)] * 1e12, lw=0.4, label=f"alpha = {a}")
    ax.set_xlabel("Time [µs]  (steady state)")
    ax.set_ylabel("BBPD input error [ps]")
    ax.set_title("Closed-loop BBPD error — smoothing pole sweep")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9, ncol=4, loc="upper right")

    # ---------- Panel 2: tail RMS ----------
    rms = [res.e_bbpd[int(0.4 * len(res.e_bbpd)):].std() * 1e12
           for res, _ in results.values()]
    ax = axes[1]
    ax.semilogx(list(results.keys()), rms, "o-", lw=1.0, color="C3")
    ax.set_xlabel("pole alpha (smaller = stronger smoothing)")
    ax.set_ylabel("tail BBPD RMS [ps]")
    ax.set_title("Tail RMS vs. smoothing strength")
    ax.grid(True, which="both", alpha=0.4)

    # ---------- Panel 3: L(f) ----------
    ax = axes[2]
    for a, (res, p) in results.items():
        phi = excess_phase_at_dco(res, trim_settling=0.4)
        f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 14))
        m = f > p.f_ref / len(phi)
        ax.semilogx(f[m], L[m], lw=0.6, label=f"alpha = {a}")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop L(f) — smoothing pole softens out-of-band peaking")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "loop_filter_pole.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"alpha": list(results.keys()),
                  "tail_rms_ps": rms}).to_csv(
        DATA_DIR / "loop_filter_pole.csv", index=False)
    for a, r in zip(results.keys(), rms):
        print(f"[pole] alpha={a:.2f}  tail BBPD RMS = {r:.2f} ps")
    print(f"[pole] saved {fig_path}")


if __name__ == "__main__":
    main()
