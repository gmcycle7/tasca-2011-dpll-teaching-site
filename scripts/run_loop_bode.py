"""Loop Bode plot.

Three panels:
  1) |L(jω)|  magnitude (dB)
  2) ∠L(jω)  phase, with phase-margin annotation at unity-gain crossover
  3) Closed-loop |H_ref| and |H_dco_pn| magnitudes, marked crossover

Uses the linearized continuous-time approximation from sim/noise_tf.py.

Saves:
    results/data/loop_bode.csv
    results/figures/loop_bode.png
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
from sim.noise_tf import open_loop_gain, ntf_ref, ntf_dco_pn, estimate_kbb_from_sim


def main() -> None:
    p = PLLParams(n_cycles=60_000)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    K_bb = estimate_kbb_from_sim(res.e_bbpd, trim_settling=0.4)

    f = np.logspace(2, np.log10(p.f_ref / 2), 600)
    L  = open_loop_gain(f, K_bb, p)
    Hr = ntf_ref(f, K_bb, p)
    Hd = ntf_dco_pn(f, K_bb, p)

    mag_db = 20 * np.log10(np.maximum(np.abs(L), 1e-30))
    phase  = np.unwrap(np.angle(L)) * 180.0 / np.pi
    idx_x  = int(np.argmin(np.abs(mag_db)))
    f_x    = float(f[idx_x])
    pm_deg = 180.0 + phase[idx_x]

    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)

    # Magnitude
    axes[0].semilogx(f, mag_db, lw=1.0, color="C0")
    axes[0].axhline(0, color="k", lw=0.4, ls="--")
    axes[0].axvline(f_x, color="C2", lw=0.6, ls=":")
    axes[0].set_ylabel("|L(jω)| [dB]")
    axes[0].set_title(f"Open-loop gain  (K_bb estimated {K_bb:.2e} s⁻¹)")
    axes[0].grid(True, which="both", alpha=0.4)

    # Phase
    axes[1].semilogx(f, phase, lw=1.0, color="C0")
    axes[1].axhline(-180, color="C3", lw=0.4, ls="--", label="−180°")
    axes[1].axvline(f_x, color="C2", lw=0.6, ls=":",
                    label=f"unity-gain crossover\n{f_x/1e3:.0f} kHz, PM = {pm_deg:.0f}°")
    axes[1].set_ylabel("∠L(jω) [°]")
    axes[1].set_title("Open-loop phase")
    axes[1].grid(True, which="both", alpha=0.4)
    axes[1].legend(loc="lower left", fontsize=9)

    # Closed-loop magnitudes
    axes[2].loglog(f, np.abs(Hr), lw=1.0, color="C0",
                   label="|H_ref|  = L/(1+L)  (low-pass)")
    axes[2].loglog(f, np.abs(Hd), lw=1.0, color="C3",
                   label="|H_dco_pn| = 1/(1+L)  (high-pass)")
    axes[2].axhline(1.0, color="k", lw=0.4, ls="--")
    axes[2].axvline(f_x, color="C2", lw=0.6, ls=":")
    axes[2].set_xlabel("offset frequency [Hz]")
    axes[2].set_ylabel("|H(f)|")
    axes[2].set_title("Closed-loop noise-transfer-function magnitudes")
    axes[2].grid(True, which="both", alpha=0.4)
    axes[2].legend(fontsize=9)
    behavioral_caption(axes[2])

    fig.tight_layout()
    fig_path = FIG_DIR / "loop_bode.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "f_hz": f, "L_mag_db": mag_db, "L_phase_deg": phase,
        "H_ref_abs": np.abs(Hr), "H_dco_abs": np.abs(Hd),
    }).to_csv(DATA_DIR / "loop_bode.csv", index=False)

    print(f"[bode] K_bb        = {K_bb:.3e} s⁻¹")
    print(f"[bode] crossover   = {f_x/1e3:.1f} kHz")
    print(f"[bode] phase margin = {pm_deg:.1f}°")
    print(f"[bode] saved {fig_path}")


if __name__ == "__main__":
    main()
