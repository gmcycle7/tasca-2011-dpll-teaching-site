"""DCO phase-noise physics template — 1/f^3 + 1/f^2 + white floor.

Three panels:
  1) Template family: anchor L(1 MHz) at three levels, see how the
     entire curve shifts and where it crosses the flicker corner.
  2) Decompose one template into its three regions to show how the
     dominant region changes with offset frequency.
  3) Resulting closed-loop L(f) for each anchor (uses ntf_dco_pn);
     teaches "DCO PN matters only above the loop bandwidth".

Saves:
    results/data/dco_pn_physics.csv
    results/figures/dco_pn_physics.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.pll_params import PLLParams
from sim.phase_noise import physics_dco_pn_template
from sim.noise_tf import open_loop_gain, ntf_dco_pn
from sim.bbpd import BBPD


def main() -> None:
    p = PLLParams()
    K_bb = BBPD.linearized_gain(1e-12)

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: anchor sweep ----------
    anchors = [-105, -115, -125]
    flicker_corner = 100e3
    floor = -150
    f = np.geomspace(100, 100e6, 300)
    ax = axes[0]
    for L_1M, col in zip(anchors, ["C3", "C0", "C2"]):
        fr, lv = physics_dco_pn_template(L_1M, flicker_corner, floor,
                                          n_points=300,
                                          f_min_hz=100, f_max_hz=100e6)
        ax.semilogx(np.asarray(fr), np.asarray(lv), lw=1.0, color=col,
                    label=f"L(1 MHz) = {L_1M} dBc/Hz")
    ax.axvline(flicker_corner, color="grey", lw=0.5, ls=":",
               label=f"flicker corner {flicker_corner/1e3:.0f} kHz")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("DCO PN templates with anchor sweep "
                 f"(floor = {floor} dBc/Hz)")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: regional decomposition ----------
    L_1M = -120.0
    S_thermal = 10.0 ** (L_1M / 10.0) * (1e6 / f) ** 2
    L_at_corner = L_1M + 20.0 * np.log10(1e6 / flicker_corner)
    S_flicker = 10.0 ** (L_at_corner / 10.0) * (flicker_corner / f) ** 3
    S_floor = 10.0 ** (floor / 10.0) * np.ones_like(f)
    S_tot = S_thermal + S_flicker + S_floor
    def db(s): return 10 * np.log10(np.maximum(s, 1e-300))
    ax = axes[1]
    ax.semilogx(f, db(S_flicker), color="C3", lw=0.9, label="1/f³ (flicker)")
    ax.semilogx(f, db(S_thermal), color="C0", lw=0.9, label="1/f² (thermal)")
    ax.semilogx(f, db(S_floor),   color="grey", lw=0.9, ls="--", label="white floor")
    ax.semilogx(f, db(S_tot),     color="k", lw=1.4, label="sum")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Regional decomposition (anchor = −120 dBc/Hz @ 1 MHz)")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9, loc="upper right")

    # ---------- Panel 3: closed-loop result for each anchor ----------
    ax = axes[2]
    f_loop = np.geomspace(1e3, p.f_ref / 2, 400)
    H_dco = ntf_dco_pn(f_loop, K_bb, p)
    log_f = np.log10(np.clip(f_loop, 1, None))
    for L_1M, col in zip(anchors, ["C3", "C0", "C2"]):
        fr, lv = physics_dco_pn_template(L_1M, flicker_corner, floor,
                                          n_points=200,
                                          f_min_hz=100, f_max_hz=100e6)
        L_template_db = np.interp(log_f, np.log10(fr), lv)
        S_dco_open = 2.0 * 10.0 ** (L_template_db / 10.0)
        S_closed = np.abs(H_dco) ** 2 * S_dco_open
        L_closed = 10 * np.log10(np.maximum(S_closed / 2.0, 1e-300))
        ax.semilogx(f_loop, L_template_db, color=col, lw=0.6, ls="--",
                    alpha=0.6, label=f"open-loop, L₁ᴹ = {L_1M}")
        ax.semilogx(f_loop, L_closed, color=col, lw=1.0,
                    label=f"closed-loop, L₁ᴹ = {L_1M}")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop result vs. open-loop template")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    behavioral_caption(ax)

    fig.suptitle("DCO phase-noise physics template "
                 "(1/f³ + 1/f² + white)", y=1.0)
    fig.tight_layout()
    fig_path = FIG_DIR / "dco_pn_physics.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"f_hz": f, "L_total_dbchz": db(S_tot)}).to_csv(
        DATA_DIR / "dco_pn_physics.csv", index=False)
    print(f"[pn-physics] saved {fig_path}")


if __name__ == "__main__":
    main()
