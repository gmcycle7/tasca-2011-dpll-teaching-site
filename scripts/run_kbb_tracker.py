"""K_bb adaptive tracker (post-processing).

K_bb = sqrt(2/pi) / sigma_in depends on the dither at the BBPD input.
If σ changes (PVT, temperature) the effective loop gain follows. A
practical PLL needs to *track* σ so it can adjust Kp/Ki to keep the
loop bandwidth on target.

This script demonstrates the principle by post-processing the BBPD
input trace from a single simulation. We compute σ in a rolling
window, then K_bb = sqrt(2/π)/σ, then the implied loop-BW. Real
hardware would use the same idea via an online estimator (Bertulessi
et al., 2020, build a sign-correlation-based estimator).

Two panels:
  1) σ and K_bb estimate over time, with the analytic K_bb from the
     final-tail σ as reference.
  2) BBPD output switching density (fraction of cycles where the sign
     flipped) — an alternative σ-proxy used in some chips.

Saves:
    results/data/kbb_tracker.csv
    results/figures/kbb_tracker.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.pll_params import PLLParams
from sim.pll_model import run_simulation
from sim.bbpd import BBPD


def main() -> None:
    p = PLLParams(n_cycles=200_000)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)

    n = len(res.e_bbpd)
    window = 2000   # cycles
    sigma_t = np.empty(n)
    sigma_t.fill(np.nan)
    for k in range(window, n):
        tail = res.e_bbpd[k - window:k]
        sigma_t[k] = float(np.std(tail - tail.mean()))
    K_bb_t = np.sqrt(2.0 / np.pi) / np.maximum(sigma_t, 1e-15)

    # Switching density: fraction of sign flips in a rolling window
    s_arr = np.sign(res.e_bbpd).astype(int)
    flips = (s_arr[1:] != s_arr[:-1]).astype(int)
    flip_density = np.empty(n - 1)
    flip_density.fill(np.nan)
    for k in range(window, n - 1):
        flip_density[k] = flips[k - window:k].mean()

    # Reference K_bb from steady-state tail
    sigma_steady = res.e_bbpd[int(0.7 * n):].std()
    K_bb_ref = BBPD.linearized_gain(sigma_steady)

    t_us = np.arange(n) * p.T_ref * 1e6

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax = axes[0]
    ax_t = ax.twinx()
    ax.plot(t_us, sigma_t * 1e12, color="C0", lw=0.7,
            label="σ (rolling 2000-cycle)")
    ax_t.plot(t_us, K_bb_t, color="C3", lw=0.7,
              label="K_bb estimate (right axis)")
    ax_t.axhline(K_bb_ref, color="k", lw=0.6, ls="--",
                 label=f"tail K_bb = {K_bb_ref:.2e}")
    ax.set_ylabel("σ at BBPD [ps]", color="C0")
    ax_t.set_ylabel("K_bb [1/s]", color="C3")
    ax.set_title("Rolling σ and K_bb estimate over a single run")
    ax.grid(True, alpha=0.4)
    ax_t.legend(loc="upper right", fontsize=9)

    ax = axes[1]
    ax.plot(t_us[:-1], flip_density, color="C2", lw=0.7)
    ax.set_xlabel("time [µs]")
    ax.set_ylabel("BBPD sign-flip density")
    ax.set_title("Switching-density proxy (alternative on-chip σ estimator)")
    ax.grid(True, alpha=0.4)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "kbb_tracker.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"t_us": t_us, "sigma_t_ps": sigma_t * 1e12,
                  "K_bb": K_bb_t}).to_csv(
        DATA_DIR / "kbb_tracker.csv", index=False)
    print(f"[kbb-track] tail σ = {sigma_steady * 1e12:.2f} ps")
    print(f"[kbb-track] K_bb = {K_bb_ref:.3e} s⁻¹")
    print(f"[kbb-track] saved {fig_path}")


if __name__ == "__main__":
    main()
