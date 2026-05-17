"""Realistic two-band DCO (coarse + dithered fine) in the closed loop.

Three panels:
  1) DCO frequency trace over time — coarse jumps + fine dither hops
     visible.
  2) Effective average frequency vs. simulation cycle — converging to
     target with sub-Hz residual.
  3) Closed-loop L(f) — linear vs. realistic DCO comparison.

Saves:
    results/data/realistic_dco_closed.csv
    results/figures/realistic_dco_closed.png
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

    p_lin = dataclasses.replace(base, use_realistic_dco=False)
    p_real = dataclasses.replace(base, use_realistic_dco=True,
                                  realistic_dco_coarse_lsb_hz=1e6,
                                  realistic_dco_fine_lsb_hz=1e3,
                                  realistic_dco_dither_bits=16)

    res_lin = run_simulation(p_lin, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True)
    res_real = run_simulation(p_real, enable_dtc=True,
                              enable_dco_pn=True, enable_ref_noise=True)

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: short frequency trace ----------
    ax = axes[0]
    n_show = 1500
    t_us = np.arange(n_show) * base.T_ref * 1e6
    ax.plot(t_us, (res_lin.f_dco[:n_show] - base.f_out_target) * 1e-3,
            lw=0.4, color="C0", label="linear DCO")
    ax.plot(t_us, (res_real.f_dco[:n_show] - base.f_out_target) * 1e-3,
            lw=0.4, color="C3", label="realistic DCO")
    ax.set_xlabel("Time [µs]  (after settle)")
    ax.set_ylabel("f_DCO − target [kHz]")
    ax.set_title("Per-cycle DCO frequency — realistic DCO shows coarse + dither")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: running mean ----------
    ax = axes[1]
    tail = int(0.3 * base.n_cycles)
    cyc = np.arange(base.n_cycles - tail) + tail
    cumlin = np.cumsum(res_lin.f_dco[tail:]) / (cyc - tail + 1)
    cumreal = np.cumsum(res_real.f_dco[tail:]) / (cyc - tail + 1)
    ax.plot(cyc * base.T_ref * 1e6, (cumlin - base.f_out_target) * 1e-3,
            color="C0", lw=0.8, label="linear DCO running mean")
    ax.plot(cyc * base.T_ref * 1e6, (cumreal - base.f_out_target) * 1e-3,
            color="C3", lw=0.8, label="realistic DCO running mean")
    ax.axhline(0, color="k", lw=0.4, ls="--")
    ax.set_xlabel("Time [µs]")
    ax.set_ylabel("running mean (f_DCO − target) [kHz]")
    ax.set_title("Cycle-averaged frequency converges to target")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 3: L(f) ----------
    ax = axes[2]
    for res, p, c, lab in [(res_lin, p_lin, "C0", "linear DCO"),
                            (res_real, p_real, "C3", "realistic DCO")]:
        phi = excess_phase_at_dco(res, trim_settling=0.4)
        f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 15))
        m = f > p.f_ref / len(phi)
        ax.semilogx(f[m], L[m], lw=0.6, color=c, label=lab)
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop L(f) — DCO dither noise sits high (loop suppresses)")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "realistic_dco_closed.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "k": np.arange(base.n_cycles),
        "f_dco_linear_hz": res_lin.f_dco,
        "f_dco_realistic_hz": res_real.f_dco,
    }).to_csv(DATA_DIR / "realistic_dco_closed.csv", index=False)
    print("[real-dco] linear  final mean offset = "
          f"{(res_lin.f_dco[-1000:].mean()-base.f_out_target):.1f} Hz")
    print("[real-dco] realist final mean offset = "
          f"{(res_real.f_dco[-1000:].mean()-base.f_out_target):.1f} Hz")
    print(f"[real-dco] saved {fig_path}")


if __name__ == "__main__":
    main()
