"""LMS multi-coefficient calibration: gain + offset.

Three panels:
  1) g_hat trajectory — gain learner alone converges to 1/(1+gain_err).
  2) offset_hat trajectory — offset learner alone matches dtc_offset_s.
  3) Tail BBPD-input RMS for: no LMS / gain only / gain + offset.

(INL-table learner is a follow-up: the DTC's lookup-table indexing
only exercises a narrow code window for our default alpha, so per-bin
learning needs an indexing-scheme refactor — tracked in CHANGELOG.)

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
    base = PLLParams(n_cycles=200_000,
                     dtc_gain_err=0.10,
                     dtc_offset_s=4e-12,
                     lms_mu=2e-4)

    cases = {
        "no LMS":        dataclasses.replace(base, lms_mu_offset=0.0),
        "gain only":     dataclasses.replace(base, lms_mu_offset=0.0),
        "gain + offset": dataclasses.replace(base, lms_mu_offset=3e-4),
    }
    enable_lms = {"no LMS": False, "gain only": True, "gain + offset": True}
    results = {
        name: run_simulation(p, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True,
                             enable_lms=enable_lms[name])
        for name, p in cases.items()
    }

    fig, axes = plt.subplots(3, 1, figsize=(10, 11))
    t_us = np.arange(base.n_cycles) * base.T_ref * 1e6

    # ---------- Panel 1: g_hat trajectory ----------
    ax = axes[0]
    for name, res in results.items():
        if name == "no LMS":
            continue
        ax.plot(t_us, res.g_hat, lw=0.8, label=name)
    ax.axhline(1 / 1.10, color="k", lw=0.6, ls="--", label="target 1/1.10")
    ax.set_xlabel("time [µs]")
    ax.set_ylabel("g_hat")
    ax.set_title("Gain coefficient g_hat")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: offset_hat trajectory ----------
    ax = axes[1]
    for name, res in results.items():
        if name in ("no LMS", "gain only"):
            continue
        ax.plot(t_us, res.offset_hat * 1e12, lw=0.8, label=name)
    ax.axhline(4.0, color="k", lw=0.6, ls="--", label="target 4 ps")
    ax.set_xlabel("time [µs]")
    ax.set_ylabel("offset_hat [ps]")
    ax.set_title("Offset coefficient offset_hat")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 3: tail BBPD-input RMS ----------
    rms_by_case = {}
    for name, res in results.items():
        tail = res.e_bbpd[int(0.85 * base.n_cycles):]
        rms_by_case[name] = tail.std() * 1e12
    ax = axes[2]
    ax.bar(list(rms_by_case.keys()), list(rms_by_case.values()),
           color=["C7", "C0", "C3"])
    ax.set_ylabel("tail BBPD-input RMS [ps]")
    ax.set_title("Stacking LMS learners removes each impairment in turn")
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
