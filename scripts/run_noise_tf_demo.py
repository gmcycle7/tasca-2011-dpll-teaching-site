"""Analytic noise-transfer function vs. simulated PSD.

Runs one default-parameter simulation, estimates K_bb from the BBPD
input trace, computes the analytic closed-loop L(f) prediction from
sim/noise_tf.py, and overlays the two.

Saves:
    results/data/noise_tf.csv
    results/figures/noise_tf.png
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
from sim.noise_tf import (
    open_loop_gain, ntf_ref, ntf_dco_pn,
    predict_closed_loop_L_dbchz, estimate_kbb_from_sim,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=300_000)
    args = ap.parse_args()

    p = PLLParams(n_cycles=args.n_cycles)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)

    # Simulated PSD
    phi = excess_phase_at_dco(res, trim_settling=0.3)
    f_sim, L_sim = estimate_psd(phi, fs=p.f_ref,
                                nperseg=min(len(phi), 1 << 15))

    # Effective K_bb from the actual BBPD input trace
    K_bb = estimate_kbb_from_sim(res.e_bbpd, trim_settling=0.3)

    # Analytic prediction on the same grid
    L_an = predict_closed_loop_L_dbchz(f_sim, K_bb, p)

    # NTF magnitudes for the educational panel
    H_ref = ntf_ref(f_sim, K_bb, p)
    H_dco = ntf_dco_pn(f_sim, K_bb, p)
    L_open = open_loop_gain(f_sim, K_bb, p)

    # Unity-gain crossover (where |L(jw)| = 1)
    mag = np.abs(L_open)
    idx_xover = int(np.argmin(np.abs(mag - 1.0)))
    f_xover = float(f_sim[idx_xover])

    # ---- Plot ----
    fig, axes = plt.subplots(2, 1, figsize=(9, 8))
    mask = f_sim > p.f_ref / len(phi)
    axes[0].semilogx(f_sim[mask], L_sim[mask], lw=0.7,
                     color="C0", label="Simulated L(f)")
    axes[0].semilogx(f_sim[mask], L_an[mask], lw=1.0,
                     color="C3", linestyle="--", label="Analytic prediction")
    axes[0].axvline(f_xover, color="C2", lw=0.8, ls=":",
                    label=f"Unity-gain crossover ≈ {f_xover/1e3:.0f} kHz")
    axes[0].set_xlabel("Offset frequency [Hz]")
    axes[0].set_ylabel("L(f) [dBc/Hz]")
    axes[0].set_title(
        f"Analytic NTF prediction vs. simulated PSD  "
        f"(K_bb = {K_bb:.2e} s⁻¹, behavioral approximation)")
    axes[0].grid(True, which="both", alpha=0.4)
    axes[0].legend()

    # NTF magnitudes
    axes[1].loglog(f_sim[mask], np.abs(H_ref[mask]),
                   lw=0.9, color="C0", label="|H_ref| = L/(1+L)")
    axes[1].loglog(f_sim[mask], np.abs(H_dco[mask]),
                   lw=0.9, color="C3", label="|H_dco_pn| = 1/(1+L)")
    axes[1].axvline(f_xover, color="C2", lw=0.8, ls=":",
                    label="crossover")
    axes[1].axhline(1.0, color="k", lw=0.4, ls="--")
    axes[1].set_xlabel("Offset frequency [Hz]")
    axes[1].set_ylabel("|H(f)|")
    axes[1].set_title("Closed-loop noise transfer functions")
    axes[1].grid(True, which="both", alpha=0.4)
    axes[1].legend()
    behavioral_caption(axes[1])

    fig.tight_layout()
    fig_path = FIG_DIR / "noise_tf.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "f_hz": f_sim,
        "L_simulated_dbchz": L_sim,
        "L_analytic_dbchz": L_an,
        "abs_H_ref": np.abs(H_ref),
        "abs_H_dco_pn": np.abs(H_dco),
    }).to_csv(DATA_DIR / "noise_tf.csv", index=False)

    print(f"[ntf] K_bb estimated from sim: {K_bb:.3e} s^-1")
    print(f"[ntf] unity-gain crossover:    {f_xover/1e3:.1f} kHz")
    print(f"[ntf] saved {fig_path}")


if __name__ == "__main__":
    main()
