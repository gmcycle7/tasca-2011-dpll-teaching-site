"""Parameter sensitivity sweep.

Walks each of a handful of knobs (DTC gain error, DTC INL, DSM order,
Kp, DCO PN floor offset), running a closed-loop simulation at every
point and reporting integrated RMS jitter + worst predicted-comb spur
level.

Designed for "which knob actually matters?" intuition, not for
exhaustive design-space exploration.

Saves:
    results/data/sensitivity_sweep.csv
    results/figures/sensitivity_sweep.png
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


F_LO_INT = 3e3
F_HI_INT = 20e6


def measure(params: PLLParams):
    """Run one sim; return (jitter_fs_rms, worst_spur_dbchz)."""
    res = run_simulation(params, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    phi = excess_phase_at_dco(res, trim_settling=0.4)
    f, L = estimate_psd(phi, fs=params.f_ref,
                        nperseg=min(len(phi), 1 << 14))
    jitter = integrated_rms_jitter_s(f, L, F_LO_INT, F_HI_INT,
                                     params.f_out_target)
    spurs = detect_spurs(f, L, params.alpha, params.f_ref, n_harmonics=8)
    worst = max((s["L_dbchz"] for s in spurs), default=float("nan"))
    return jitter * 1e15, worst


def replace(base: PLLParams, **kwargs) -> PLLParams:
    return dataclasses.replace(base, **kwargs)


def sweep_dtc_gain_err(base):
    xs = np.linspace(-0.20, 0.20, 9)
    rows = []
    for x in xs:
        p = replace(base, dtc_gain_err=float(x))
        j, s = measure(p)
        rows.append((x, j, s))
        print(f"  gain_err={x:+.2f}  jitter={j:.0f} fs  worst_spur={s:.1f} dBc/Hz")
    return np.array(rows)


def sweep_dtc_inl(base):
    xs = np.linspace(0.0, 6.0, 7)
    rows = []
    for x in xs:
        p = replace(base, dtc_inl_amp_s=float(x) * 1e-12)
        j, s = measure(p)
        rows.append((x, j, s))
        print(f"  INL_amp={x:.1f} ps  jitter={j:.0f} fs  worst_spur={s:.1f} dBc/Hz")
    return np.array(rows)


def sweep_dsm_order(base):
    rows = []
    for order in (1, 2, 3):
        p = replace(base, dsm_order=int(order))
        j, s = measure(p)
        rows.append((order, j, s))
        print(f"  DSM order={order}  jitter={j:.0f} fs  worst_spur={s:.1f} dBc/Hz")
    return np.array(rows)


def sweep_kp(base):
    xs = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 32.0])
    rows = []
    for x in xs:
        p = replace(base, Kp=float(x))
        j, s = measure(p)
        rows.append((x, j, s))
        print(f"  Kp={x:.0f}  jitter={j:.0f} fs  worst_spur={s:.1f} dBc/Hz")
    return np.array(rows)


def sweep_dco_pn_offset(base):
    xs = np.array([-10.0, -5.0, 0.0, 5.0, 10.0])
    rows = []
    for x in xs:
        new_levels = tuple(float(L + x) for L in base.dco_pn_levels_dbchz)
        p = replace(base, dco_pn_levels_dbchz=new_levels)
        j, s = measure(p)
        rows.append((x, j, s))
        print(f"  DCO_PN +{x:+.0f} dB  jitter={j:.0f} fs  worst_spur={s:.1f} dBc/Hz")
    return np.array(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cycles", type=int, default=80_000)
    args = ap.parse_args()

    base = PLLParams(n_cycles=args.n_cycles)

    print("[sweep] DTC gain error ..."); ga = sweep_dtc_gain_err(base)
    print("[sweep] DTC INL ...");         inl = sweep_dtc_inl(base)
    print("[sweep] DSM order ...");       ds = sweep_dsm_order(base)
    print("[sweep] Kp ...");              kp = sweep_kp(base)
    print("[sweep] DCO PN offset ...");   pn = sweep_dco_pn_offset(base)

    fig, axes = plt.subplots(5, 2, figsize=(13, 16))
    panels = [
        ("DTC gain error",        ga, "gain_err"),
        ("DTC INL amplitude [ps]", inl, "INL [ps]"),
        ("DSM order",             ds, "order"),
        ("Kp",                    kp, "Kp"),
        ("DCO PN offset [dB]",    pn, "ΔPN [dB]"),
    ]
    for i, (title, arr, xlabel) in enumerate(panels):
        axes[i, 0].plot(arr[:, 0], arr[:, 1], "o-", lw=1.0, color="C0")
        axes[i, 0].set_xlabel(xlabel)
        axes[i, 0].set_ylabel("Jitter [fs RMS]")
        axes[i, 0].set_title(title)
        axes[i, 0].grid(True, alpha=0.4)
        axes[i, 1].plot(arr[:, 0], arr[:, 2], "s-", lw=1.0, color="C3")
        axes[i, 1].set_xlabel(xlabel)
        axes[i, 1].set_ylabel("Worst spur [dBc/Hz]")
        axes[i, 1].set_title(title)
        axes[i, 1].grid(True, alpha=0.4)
    behavioral_caption(axes[-1, 1])
    fig.suptitle("Parameter sensitivity sweep — behavioral approximation",
                 y=0.995)
    fig.tight_layout()
    fig_path = FIG_DIR / "sensitivity_sweep.png"
    fig.savefig(fig_path, dpi=120)
    plt.close(fig)

    pd.DataFrame({
        "knob": (
            ["gain_err"] * len(ga) + ["inl_amp_ps"] * len(inl) +
            ["dsm_order"] * len(ds) + ["Kp"] * len(kp) +
            ["dco_pn_offset_db"] * len(pn)),
        "x": np.concatenate([ga[:, 0], inl[:, 0], ds[:, 0], kp[:, 0], pn[:, 0]]),
        "jitter_fs": np.concatenate([ga[:, 1], inl[:, 1], ds[:, 1], kp[:, 1], pn[:, 1]]),
        "worst_spur_dbchz": np.concatenate([ga[:, 2], inl[:, 2], ds[:, 2], kp[:, 2], pn[:, 2]]),
    }).to_csv(DATA_DIR / "sensitivity_sweep.csv", index=False)
    print(f"[sweep] saved {fig_path}")


if __name__ == "__main__":
    main()
