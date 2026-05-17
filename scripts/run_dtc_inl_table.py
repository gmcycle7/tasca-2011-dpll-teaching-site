"""DTC INL: sinusoidal model vs. arbitrary lookup-table profile.

Three panels:
  1) Two INL profiles plotted against tau_target — sinusoid vs.
     "real-looking" piecewise.
  2) Closed-loop L(f) for each.
  3) Worst-comb-spur level for each (single-number summary).

Saves:
    results/data/dtc_inl_table.csv
    results/figures/dtc_inl_table.png
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
from sim.spurs import detect_spurs


def main() -> None:
    base = PLLParams(n_cycles=120_000)
    rng = np.random.default_rng(7)

    # Build a "real-looking" INL table: low-order polynomial trend
    # plus a small random component, 32 bins over full scale.
    n_bins = 32
    bins = np.arange(n_bins) / n_bins
    inl_table_s = (1.5e-12 * np.sin(2 * np.pi * 2.5 * bins)
                   + 0.8e-12 * (bins - 0.5) ** 2 * 4
                   + rng.normal(0, 0.4e-12, n_bins))

    cases = {
        "ideal":     dataclasses.replace(base),
        "sinusoid":  dataclasses.replace(base, dtc_inl_amp_s=2e-12,
                                          dtc_inl_periods=4),
        "table":     dataclasses.replace(base, dtc_inl_table_s=inl_table_s,
                                          dtc_inl_table_full_scale_s=base.T_ref),
    }

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: INL profile shapes ----------
    tau_grid = np.linspace(0, base.T_ref, 1000)
    ax = axes[0]
    ax.plot(tau_grid * 1e9, np.zeros_like(tau_grid),
            "k:", lw=0.5, label="ideal")
    sin_inl = 2e-12 * np.sin(2 * np.pi * 4 * tau_grid / base.T_ref)
    ax.plot(tau_grid * 1e9, sin_inl * 1e12, color="C0", lw=0.9,
            label="sinusoidal (2 ps, 4 ripples)")
    idx = np.clip((tau_grid / base.T_ref * n_bins).astype(int), 0, n_bins - 1)
    ax.step(tau_grid * 1e9, inl_table_s[idx] * 1e12, where="post",
            color="C3", lw=0.9, label="lookup table (32 bins)")
    ax.set_xlabel("tau_target [ns]")
    ax.set_ylabel("INL residual [ps]")
    ax.set_title("Two INL models — same RMS, very different shape")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: L(f) ----------
    spectra = {}
    for name, p in cases.items():
        res = run_simulation(p, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True)
        phi = excess_phase_at_dco(res, trim_settling=0.4)
        f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 14))
        spectra[name] = (f, L, p)
        print(f"[inl-table] {name}: floor = "
              f"{np.median(L[(f > 1e6) & (f < 5e6)]):.1f} dBc/Hz")
    ax = axes[1]
    for name, (f, L, p) in spectra.items():
        m = f > p.f_ref / 80_000
        ax.semilogx(f[m], L[m], lw=0.6, label=name)
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop L(f) — INL shape matters")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 3: spurs ----------
    worst = {}
    for name, (f, L, p) in spectra.items():
        sp = detect_spurs(f, L, p.alpha, p.f_ref, n_harmonics=8)
        worst[name] = max((s["L_dbchz"] for s in sp), default=float("nan"))
    ax = axes[2]
    ax.bar(list(worst.keys()), list(worst.values()),
           color=["C2", "C0", "C3"])
    ax.set_ylabel("worst predicted-comb spur [dBc/Hz]")
    ax.set_title("Worst-comb spur — table shape can be much worse than a sinusoid")
    ax.grid(True, axis="y", alpha=0.4)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "dtc_inl_table.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame([
        {"model": k, "worst_spur_dbchz": v} for k, v in worst.items()
    ]).to_csv(DATA_DIR / "dtc_inl_table.csv", index=False)
    print(f"[inl-table] saved {fig_path}")


if __name__ == "__main__":
    main()
