"""Allan deviation σ_y(τ) from a simulator-produced edge timestamp series.

Three panels:
  1) Overlapping ADEV of the closed-loop DCO edges, in log-log.
  2) Same plot with theoretical slope guides for white-FM (τ^-1/2),
     flicker-FM (τ^0), and random-walk FM (τ^+1/2).
  3) Compare three loop bandwidths: smaller BW lets DCO PN show up at
     longer τ, larger BW pushes the white-FM dominated region farther
     out.

Saves:
    results/data/allan.csv
    results/figures/allan.png
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
from sim.allan import adev_from_div_edges


def main() -> None:
    p = PLLParams(n_cycles=200_000)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    tau, adev = adev_from_div_edges(res.t_div_eff, p.T_ref)

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: ADEV ----------
    ax = axes[0]
    ax.loglog(tau, adev, "o-", lw=1.0, ms=4, color="C0")
    ax.set_xlabel("averaging time τ [s]")
    ax.set_ylabel("σ_y(τ)")
    ax.set_title("Overlapping Allan deviation — closed-loop DPLL output")
    ax.grid(True, which="both", alpha=0.4)

    # ---------- Panel 2: with theoretical slope guides ----------
    ax = axes[1]
    ax.loglog(tau, adev, "o-", lw=1.0, ms=4, color="C0", label="simulated")
    # Slope guides anchored at log-center
    i_anchor = len(tau) // 2
    a0, t0 = adev[i_anchor], tau[i_anchor]
    for slope, name, col in [(-0.5, "white FM  (τ^-1/2)", "C3"),
                              (0.0,  "flicker FM (τ^0)",  "C2"),
                              (0.5,  "random-walk FM (τ^+1/2)", "C4")]:
        ax.loglog(tau, a0 * (tau / t0) ** slope, ls=":",
                  lw=0.8, color=col, label=name)
    ax.set_xlabel("averaging time τ [s]")
    ax.set_ylabel("σ_y(τ)")
    ax.set_title("With theoretical slope guides — read off the dominant noise type")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9, loc="lower left")

    # ---------- Panel 3: loop-BW sweep ----------
    ax = axes[2]
    for (Kp, lab) in [(2.0, "low BW (Kp=2)"),
                      (8.0, "default (Kp=8)"),
                      (32.0, "high BW (Kp=32)")]:
        p2 = dataclasses.replace(p, Kp=Kp)
        r2 = run_simulation(p2, enable_dtc=True,
                            enable_dco_pn=True, enable_ref_noise=True)
        t2, a2 = adev_from_div_edges(r2.t_div_eff, p2.T_ref)
        ax.loglog(t2, a2, lw=1.0, label=lab)
    ax.set_xlabel("averaging time τ [s]")
    ax.set_ylabel("σ_y(τ)")
    ax.set_title("ADEV vs. loop bandwidth")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "allan.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"tau_s": tau, "adev": adev}).to_csv(
        DATA_DIR / "allan.csv", index=False)
    print(f"[allan] minimum ADEV = {adev.min():.2e} at τ = "
          f"{tau[np.argmin(adev)]*1e6:.1f} µs")
    print(f"[allan] saved {fig_path}")


if __name__ == "__main__":
    main()
