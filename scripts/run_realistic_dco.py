"""Two-band realistic DCO demo.

Three panels:
  1) f(control_word) for the simple linear DCO vs. coarse-only DCO
     (staircase) vs. coarse + fine vs. coarse + fine + DSM dither.
  2) Time-domain frequency trace at a sub-LSB control word: the
     dithered fine bank visibly cycles between codes; the mean lands
     at the target sub-Hz frequency.
  3) PSD of the per-sample frequency deviation — dither noise is
     shaped to high offsets, leaving the in-band floor clean.

Saves:
    results/data/realistic_dco.csv
    results/figures/realistic_dco.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal as sig

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.dco import DCO
from sim.realistic_dco import RealisticDCO


F0 = 3.605e9
FS = 40e6              # sample rate (call rate of RealisticDCO)


def main() -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: characteristics ----------
    cw = np.linspace(0, 200, 2001)                # in fine-LSB units

    # Simple linear DCO
    dco_lin = DCO(f_dco_nominal=F0, K_dco=1e3)    # 1 kHz/LSB
    f_lin = np.array([dco_lin.frequency(c) for c in cw])

    # Coarse-only DCO: just the coarse bank (1 MHz steps, 1000 fine-LSB apart)
    coarse_lsb = 1e6
    fine_lsb_eq = 1e3
    f_coarse = F0 + np.floor(cw / (coarse_lsb / fine_lsb_eq)) * coarse_lsb

    # Coarse + fine, no dither (use RealisticDCO with very wide dither bits → no dither)
    dco_cf = RealisticDCO(f_nominal=F0, coarse_lsb_hz=1e6, fine_lsb_hz=1e3,
                           dither_bits=24, seed=0)
    f_cf = np.array([dco_cf.frequency(c) for c in cw])

    # Coarse + fine + 1st-order DSM dither
    dco_cfd = RealisticDCO(f_nominal=F0, coarse_lsb_hz=1e6, fine_lsb_hz=1e3,
                            dither_bits=16, dither_order=1, seed=42)
    f_cfd = np.array([dco_cfd.frequency(c) for c in cw])

    ax = axes[0]
    ax.plot(cw, (f_lin - F0) * 1e-3, lw=0.7, color="C0",
            label="linear DCO (sim/dco.py)")
    ax.plot(cw, (f_coarse - F0) * 1e-3, lw=0.8, color="C3",
            label="coarse bank only  (LSB = 1 MHz)")
    ax.plot(cw, (f_cf - F0) * 1e-3, lw=0.6, color="C2",
            label="coarse + fine, no dither  (LSB = 1 kHz)")
    ax.plot(cw, (f_cfd - F0) * 1e-3, "x", color="C4", ms=3, alpha=0.6,
            label="coarse + fine + DSM dither  (per-cycle output)")
    ax.set_xlabel("control word (fine LSBs)")
    ax.set_ylabel("f − f₀ [kHz]")
    ax.set_title("Two-band DCO characteristic")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: time-domain at sub-LSB control word ----------
    sub_target = 73.4    # in fine-LSB units; fractional part is 0.4 LSB = 400 Hz target
    dco_run = RealisticDCO(f_nominal=F0, coarse_lsb_hz=1e6, fine_lsb_hz=1e3,
                            dither_bits=16, dither_order=1, seed=7)
    N_show = 200
    f_seq = np.array([dco_run.frequency(sub_target) for _ in range(20000)])
    mean_offset = (np.mean(f_seq) - F0) - 73.0 * 1e3   # excess over 73 LSBs

    ax = axes[1]
    ax.plot(np.arange(N_show), (f_seq[:N_show] - F0) * 1e-3 - 73,
            "o-", lw=0.8, ms=3, color="C0")
    ax.axhline(0.4, color="C2", lw=0.8, ls="--",
               label=f"target sub-LSB level = 0.4 LSB  (400 Hz)")
    ax.axhline(mean_offset * 1e-3, color="C3", lw=0.8, ls=":",
               label=f"measured mean ≈ {mean_offset:.0f} Hz  "
                     f"(rel. err {(mean_offset - 400) / 400 * 100:+.2f}%)")
    ax.set_xlabel("call index (cycles)")
    ax.set_ylabel("f − f₀ − 73 LSB  [fine-LSB units]")
    ax.set_title(f"Dither realises sub-LSB frequency at control word = {sub_target}")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 3: PSD of frequency deviation ----------
    f_freq, P_freq = sig.welch(f_seq - np.mean(f_seq), fs=FS, nperseg=1 << 12)
    ax = axes[2]
    ax.loglog(f_freq[1:], P_freq[1:], lw=0.8, color="C0")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("PSD of f_DCO [Hz²/Hz]")
    ax.set_title("Per-cycle DCO frequency PSD — DSM dither shapes noise to high offsets")
    ax.grid(True, which="both", alpha=0.4)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "realistic_dco.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "control_word": cw,
        "f_linear_hz":  f_lin,
        "f_coarse_hz":  f_coarse,
        "f_cf_hz":      f_cf,
    }).to_csv(DATA_DIR / "realistic_dco.csv", index=False)

    print(f"[dco-real] sub-LSB target = 400 Hz, measured = {mean_offset:.1f} Hz")
    print(f"[dco-real] saved {fig_path}")


if __name__ == "__main__":
    main()
