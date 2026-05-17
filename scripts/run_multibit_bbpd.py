"""1-bit vs 2-bit vs 3-bit BBPD comparison.

Same loop, same DCO, same DSM — only the comparator bit-count
changes. The Kp/Ki are scaled so each architecture has roughly
the same effective small-signal gain near lock.

Three panels:
  1) Per-cycle detector output histogram (shape changes with bits).
  2) Closed-loop BBPD-input RMS error vs bit count.
  3) Closed-loop L(f) overlay.

Saves:
    results/data/multibit_bbpd.csv
    results/figures/multibit_bbpd.png
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


def run_for_bits(n_bits: int):
    # For multi-bit, the detector code can be larger than ±1 — scale Kp
    # down by 2^(n_bits-1) so the loop gain is comparable.
    base = PLLParams(n_cycles=80_000)
    scale = 1.0 / (1 << (n_bits - 1)) if n_bits > 1 else 1.0
    p = dataclasses.replace(base, bbpd_bits=n_bits,
                            bbpd_full_scale_s=8e-12,
                            Kp=base.Kp * scale, Ki=base.Ki * scale)
    return run_simulation(p, enable_dtc=True,
                          enable_dco_pn=True, enable_ref_noise=True), p


def main() -> None:
    cases = {1: "1-bit (sign)", 2: "2-bit (4 levels)", 3: "3-bit (8 levels)"}
    results = {n: run_for_bits(n) for n in cases}

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: detector output histogram ----------
    ax = axes[0]
    for n, (res, _) in results.items():
        tail = res.s_bbpd[int(0.4 * len(res.s_bbpd)):]
        bins = np.arange(tail.min() - 0.5, tail.max() + 1.5)
        ax.hist(tail, bins=bins, histtype="step", lw=1.2, density=True,
                label=cases[n])
    ax.set_xlabel("detector output code")
    ax.set_ylabel("density")
    ax.set_title("Per-cycle detector output histogram")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: tail RMS ----------
    rms = []
    for n, (res, _) in results.items():
        tail = res.e_bbpd[int(0.4 * len(res.e_bbpd)):]
        rms.append((n, tail.std() * 1e12))
    ax = axes[1]
    ax.plot([r[0] for r in rms], [r[1] for r in rms], "o-",
            lw=1.0, ms=8, color="C3")
    ax.set_xticks([1, 2, 3])
    ax.set_xlabel("detector bit count")
    ax.set_ylabel("tail BBPD-input RMS [ps]")
    ax.set_title("Tail RMS vs. bit count "
                 "(Kp/Ki rescaled so effective loop gain matches)")
    ax.grid(True, alpha=0.4)

    # ---------- Panel 3: L(f) ----------
    ax = axes[2]
    for n, (res, p) in results.items():
        phi = excess_phase_at_dco(res, trim_settling=0.4)
        f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 14))
        m = f > p.f_ref / len(phi)
        ax.semilogx(f[m], L[m], lw=0.6, label=cases[n])
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop L(f) — marginal in-band gain from more bits")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "multibit_bbpd.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"n_bits": [r[0] for r in rms],
                  "tail_rms_ps": [r[1] for r in rms]}).to_csv(
        DATA_DIR / "multibit_bbpd.csv", index=False)
    for r in rms:
        print(f"[mbit-bbpd] {r[0]}-bit  tail RMS = {r[1]:.2f} ps")
    print(f"[mbit-bbpd] saved {fig_path}")


if __name__ == "__main__":
    main()
