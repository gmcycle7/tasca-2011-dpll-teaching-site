"""PVT Monte-Carlo: jitter and spur yield over process / supply / temperature corners.

Each Monte-Carlo trial perturbs the impairment parameters by a Gaussian
draw representing the kind of run-to-run variation a real chip sees.
We measure integrated RMS jitter and worst predicted-comb spur for
each trial and plot the distributions.

Four panels:
  1) Jitter histogram with quantile markers.
  2) Worst-spur histogram.
  3) Scatter (jitter, worst-spur) — does one predict the other?
  4) Yield curves vs. jitter / spur specs.

Saves:
    results/data/pvt_monte_carlo.csv
    results/figures/pvt_monte_carlo.png
"""
from __future__ import annotations
import argparse
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
from sim.jitter import integrated_rms_jitter_s
from sim.spurs import detect_spurs


def perturb(base: PLLParams, rng) -> PLLParams:
    """Apply a one-sigma perturbation to each impairment knob."""
    # Process variation in DCO K_dco (±20% Gaussian, 3-sigma)
    K_dco = base.K_dco * (1.0 + rng.normal(0, 0.20 / 3))
    # DCO PN template floor shifted ±5 dB (3-sigma)
    pn_shift_db = rng.normal(0, 5.0 / 3)
    pn_levels = tuple(float(L + pn_shift_db) for L in base.dco_pn_levels_dbchz)
    # DTC gain error ±0.10 (3-sigma)
    g_err = rng.normal(0, 0.10 / 3)
    # DTC static offset ±5 ps (3-sigma)
    offset_s = rng.normal(0, 5e-12 / 3)
    # BBPD metastability up to 1 ps RMS
    meta_s = abs(rng.normal(0, 1e-12 / 3))
    # Small Kp/Ki manufacturing tolerance
    Kp = base.Kp * (1.0 + rng.normal(0, 0.05 / 3))
    Ki = base.Ki * (1.0 + rng.normal(0, 0.05 / 3))
    return dataclasses.replace(
        base, K_dco=K_dco,
        dco_pn_levels_dbchz=pn_levels,
        dtc_gain_err=float(g_err), dtc_offset_s=float(offset_s),
        bbpd_meta_noise_rms_s=float(meta_s),
        Kp=float(Kp), Ki=float(Ki),
    )


def measure(p: PLLParams) -> tuple[float, float]:
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    phi = excess_phase_at_dco(res, trim_settling=0.4)
    f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 14))
    sigma = integrated_rms_jitter_s(f, L, 3e3, 20e6, p.f_out_target) * 1e15
    spurs = detect_spurs(f, L, p.alpha, p.f_ref, n_harmonics=8)
    worst = max((s["L_dbchz"] for s in spurs), default=float("nan"))
    return float(sigma), float(worst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-trials", type=int, default=30)
    ap.add_argument("--n-cycles", type=int, default=60_000)
    args = ap.parse_args()

    base = PLLParams(n_cycles=args.n_cycles)
    rng = np.random.default_rng(20260515)

    jitters, spurs = [], []
    for i in range(args.n_trials):
        p = perturb(base, rng)
        # Force a unique seed per trial too so the PSD has independent
        # noise realisations as well as parameter perturbations.
        p = dataclasses.replace(p, rng_seed=base.rng_seed + i + 1)
        s, w = measure(p)
        jitters.append(s); spurs.append(w)
        print(f"[pvt-mc] trial {i+1:02d}/{args.n_trials}: "
              f"jitter = {s:6.0f} fs   worst spur = {w:6.1f} dBc/Hz")

    jitters = np.array(jitters); spurs = np.array(spurs)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # ---------- Panel 1: jitter histogram ----------
    ax = axes[0, 0]
    ax.hist(jitters, bins=15, color="C0", alpha=0.7, edgecolor="white")
    for q, col, lab in [(0.5, "C2", "median"),
                         (0.9, "C3", "90th percentile")]:
        ax.axvline(np.quantile(jitters, q), color=col, lw=1.0, ls="--",
                   label=f"{lab}: {np.quantile(jitters, q):.0f} fs")
    ax.set_xlabel("integrated jitter [fs RMS]")
    ax.set_ylabel("count")
    ax.set_title(f"Jitter distribution over {args.n_trials} PVT trials")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: worst-spur histogram ----------
    ax = axes[0, 1]
    valid = np.isfinite(spurs)
    ax.hist(spurs[valid], bins=15, color="C3", alpha=0.7, edgecolor="white")
    ax.axvline(np.median(spurs[valid]), color="C0", lw=1.0, ls="--",
               label=f"median: {np.median(spurs[valid]):.1f} dBc/Hz")
    ax.set_xlabel("worst predicted-comb spur [dBc/Hz]")
    ax.set_ylabel("count")
    ax.set_title("Worst-spur distribution")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 3: scatter ----------
    ax = axes[1, 0]
    ax.scatter(jitters, spurs, c="C4", s=24, alpha=0.7)
    ax.set_xlabel("jitter [fs RMS]")
    ax.set_ylabel("worst spur [dBc/Hz]")
    ax.set_title("(jitter, worst-spur) per trial — checks for correlation")
    ax.grid(True, alpha=0.4)

    # ---------- Panel 4: yield curves ----------
    ax = axes[1, 1]
    jit_specs = np.linspace(jitters.min() * 0.95, jitters.max() * 1.05, 80)
    spur_specs = np.linspace(spurs[valid].min() - 1, spurs[valid].max() + 1, 80)
    yield_j = np.array([np.mean(jitters <= s) for s in jit_specs]) * 100
    yield_s = np.array([np.mean(spurs[valid] <= s) for s in spur_specs]) * 100
    ax.plot(jit_specs, yield_j, color="C0", lw=1.0, label="jitter ≤ spec [fs]")
    ax_t = ax.twiny()
    ax_t.plot(spur_specs, yield_s, color="C3", lw=1.0, ls="--",
              label="worst spur ≤ spec [dBc/Hz]")
    ax.set_xlabel("jitter spec [fs]", color="C0")
    ax_t.set_xlabel("worst spur spec [dBc/Hz]", color="C3")
    ax.set_ylabel("cumulative yield [%]")
    ax.set_title("Yield = fraction of trials meeting spec")
    ax.grid(True, alpha=0.4)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "pvt_monte_carlo.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"trial": np.arange(args.n_trials),
                  "jitter_fs": jitters,
                  "worst_spur_dbchz": spurs}).to_csv(
        DATA_DIR / "pvt_monte_carlo.csv", index=False)

    print(f"[pvt-mc] jitter:     median={np.median(jitters):.0f} fs, "
          f"P90={np.quantile(jitters, 0.9):.0f} fs")
    if valid.any():
        print(f"[pvt-mc] worst spur: median={np.median(spurs[valid]):.1f}, "
              f"P10={np.quantile(spurs[valid], 0.1):.1f} dBc/Hz")
    print(f"[pvt-mc] saved {fig_path}")


if __name__ == "__main__":
    main()
