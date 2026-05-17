"""LMS multi-coefficient calibration: gain + offset + INL piecewise.

Four panels:
  1) g_hat trajectory across all calibrated cases.
  2) offset_hat trajectory.
  3) Per-bin INL learned vs. truth.
  4) Tail BBPD-input RMS for: no LMS / gain only / + offset / + INL.

The DTC's INL lookup table and the LMS learner use the SAME centered
bin index now (norm = (tau + FS/2)/FS), with FS set to 4·T_DCO so the
±2-cycle MASH-1-1-1 residue spans the full table.

Saves:
    results/data/lms_multi.csv
    results/figures/lms_multi.png
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


def main() -> None:
    n_bins = 16
    rng = np.random.default_rng(3)
    inl_truth = (1.2e-12 * np.sin(2 * np.pi * 2.0 * np.arange(n_bins) / n_bins)
                 + rng.normal(0, 0.3e-12, n_bins))

    base = PLLParams(n_cycles=200_000,
                     dtc_gain_err=0.10,
                     dtc_offset_s=4e-12,
                     dtc_inl_table_s=inl_truth,
                     dtc_inl_table_full_scale_s=4.0 * (1.0 / 3.605e9),
                     lms_mu=2e-4,
                     lms_inl_n_bins=n_bins)

    cases = {
        "no LMS":              dataclasses.replace(base, lms_mu_offset=0.0,
                                                   lms_mu_inl=0.0),
        "gain only":           dataclasses.replace(base, lms_mu_offset=0.0,
                                                   lms_mu_inl=0.0),
        "gain + offset":       dataclasses.replace(base, lms_mu_offset=3e-4,
                                                   lms_mu_inl=0.0),
        "gain + offset + INL": dataclasses.replace(base, lms_mu_offset=3e-4,
                                                   lms_mu_inl=2e-7),
    }
    enable_lms = {n: n != "no LMS" for n in cases}
    results = {
        name: run_simulation(p, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True,
                             enable_lms=enable_lms[name])
        for name, p in cases.items()
    }

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    t_us = np.arange(base.n_cycles) * base.T_ref * 1e6

    # ---------- Panel 1: g_hat trajectory ----------
    ax = axes[0, 0]
    for name, res in results.items():
        if name == "no LMS":
            continue
        ax.plot(t_us, res.g_hat, lw=0.8, label=name)
    ax.axhline(1 / 1.10, color="k", lw=0.6, ls="--", label="target 1/1.10")
    ax.set_xlabel("time [µs]")
    ax.set_ylabel("g_hat")
    ax.set_title("Gain coefficient g_hat")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8)

    # ---------- Panel 2: offset_hat trajectory ----------
    ax = axes[0, 1]
    for name, res in results.items():
        if name in ("no LMS", "gain only"):
            continue
        ax.plot(t_us, res.offset_hat * 1e12, lw=0.8, label=name)
    ax.axhline(4.0, color="k", lw=0.6, ls="--", label="target 4 ps")
    ax.set_xlabel("time [µs]")
    ax.set_ylabel("offset_hat [ps]")
    ax.set_title("Offset coefficient offset_hat")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8)

    # ---------- Panel 3: learned INL vs truth ----------
    ax = axes[1, 0]
    res_inl = results["gain + offset + INL"]
    bins = np.arange(n_bins)
    ax.step(bins, inl_truth * 1e12, where="mid", color="C2",
            lw=1.2, label="truth")
    if res_inl.inl_table_hat is not None:
        ax.step(bins, res_inl.inl_table_hat * 1e12, where="mid",
                color="C3", lw=1.2, label="learned")
    ax.set_xlabel("INL code bin (centered indexing)")
    ax.set_ylabel("INL [ps]")
    ax.set_title("Per-bin INL: learned vs. truth")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 4: tail BBPD-input RMS ----------
    rms_by_case = {}
    for name, res in results.items():
        tail = res.e_bbpd[int(0.85 * base.n_cycles):]
        rms_by_case[name] = tail.std() * 1e12
    ax = axes[1, 1]
    ax.bar(list(rms_by_case.keys()), list(rms_by_case.values()),
           color=["C7", "C0", "C2", "C3"])
    ax.set_ylabel("tail BBPD-input RMS [ps]")
    ax.set_title("Stacked LMS learners remove each impairment in turn")
    ax.tick_params(axis="x", rotation=10)
    ax.grid(True, axis="y", alpha=0.4)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "lms_multi.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame([{"case": n, "tail_rms_ps": v}
                  for n, v in rms_by_case.items()]).to_csv(
        DATA_DIR / "lms_multi.csv", index=False)
    for n, v in rms_by_case.items():
        print(f"[lms-multi] {n:<22}  tail RMS = {v:.2f} ps")
    print(f"[lms-multi] saved {fig_path}")


if __name__ == "__main__":
    main()
