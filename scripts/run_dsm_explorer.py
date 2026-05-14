"""DSM explorer.

Four panels:
  1) m[k] integer sequence (short window) for MASH 1 / 2 / 3
  2) m[k] one-sided PSD showing the 1/2/3-rd order shaping slope
  3) e_dsm cumulative residue trace + histogram (per order)
  4) e_dsm PSD (the *DTC-relevant* spectrum)

Saves:
    results/data/dsm_explorer.csv
    results/figures/dsm_explorer.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal as sig

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.dsm import MASH

N      = 200_000
F_REF  = 40e6
ALPHA  = 0.125


def run_order(order: int):
    dsm = MASH(order=order, quant_levels=1 << 24, seed=42 + order)
    m = np.empty(N, dtype=int)
    e = np.empty(N, dtype=float)
    for k in range(N):
        m_k, e_k = dsm.step(ALPHA)
        m[k] = m_k
        e[k] = e_k
    return m, e


def main() -> None:
    out = {o: run_order(o) for o in (1, 2, 3)}

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    colors = {1: "C0", 2: "C2", 3: "C3"}
    labels = {1: "MASH-1", 2: "MASH-1-1", 3: "MASH-1-1-1"}

    # Panel 1: m[k] traces
    win = slice(0, 200)
    for o, (m, _) in out.items():
        axes[0, 0].step(np.arange(win.stop - win.start), m[win],
                        where="post", lw=0.9, color=colors[o], label=labels[o])
    axes[0, 0].axhline(ALPHA, color="k", lw=0.5, ls="--", label=f"α = {ALPHA}")
    axes[0, 0].set_title("m[k] — divider modulus dither")
    axes[0, 0].set_xlabel("ref cycle k")
    axes[0, 0].set_ylabel("m[k]")
    axes[0, 0].grid(True, alpha=0.4)
    axes[0, 0].legend(loc="upper right", fontsize=9)

    # Panel 2: m[k] PSD (with theoretical shaping slope guides)
    for o, (m, _) in out.items():
        f, P = sig.welch(m - m.mean(), fs=F_REF, nperseg=1 << 13)
        axes[0, 1].loglog(f[1:], P[1:], color=colors[o], lw=0.9, label=labels[o])
    # Theoretical slope guides
    fref_marker = np.array([1e4, 1e7])
    for o, slope_dec in zip((1, 2, 3), (2, 4, 6)):
        ref_lvl = 1e-14
        axes[0, 1].loglog(fref_marker, ref_lvl * (fref_marker / 1e4) ** slope_dec,
                          ls=":", lw=0.7, color=colors[o], alpha=0.6)
    axes[0, 1].set_title("m[k] PSD — Lth-order shaping (slope guides dotted)")
    axes[0, 1].set_xlabel("f [Hz]")
    axes[0, 1].set_ylabel("PSD")
    axes[0, 1].grid(True, which="both", alpha=0.4)
    axes[0, 1].legend(loc="lower right", fontsize=9)

    # Panel 3: e_dsm time trace (short window) + histogram inset
    for o, (_, e) in out.items():
        axes[1, 0].plot(np.arange(2000), e[:2000], lw=0.6,
                        color=colors[o], label=labels[o])
    axes[1, 0].set_title("e_dsm cumulative residue (fractional DCO cycles)")
    axes[1, 0].set_xlabel("ref cycle k")
    axes[1, 0].set_ylabel("e_dsm [cycles]")
    axes[1, 0].grid(True, alpha=0.4)
    axes[1, 0].legend(loc="upper right", fontsize=9)

    # Inset histogram
    ax_inset = axes[1, 0].inset_axes([0.6, 0.55, 0.38, 0.42])
    for o, (_, e) in out.items():
        ax_inset.hist(e[N // 4:], bins=80, histtype="step",
                      color=colors[o], lw=1.0, density=True)
    ax_inset.set_title("e_dsm density", fontsize=8)
    ax_inset.tick_params(labelsize=7)
    ax_inset.grid(True, alpha=0.3)

    # Panel 4: e_dsm PSD (this is the *DTC-relevant* spectrum)
    for o, (_, e) in out.items():
        f, P = sig.welch(e[N // 4:] - e[N // 4:].mean(),
                         fs=F_REF, nperseg=1 << 14)
        axes[1, 1].loglog(f[1:], P[1:], color=colors[o], lw=0.9, label=labels[o])
    axes[1, 1].set_title("e_dsm PSD — what the DTC must cancel")
    axes[1, 1].set_xlabel("f [Hz]")
    axes[1, 1].set_ylabel("PSD")
    axes[1, 1].grid(True, which="both", alpha=0.4)
    axes[1, 1].legend(loc="lower right", fontsize=9)

    behavioral_caption(axes[1, 1])
    fig.suptitle(f"DSM behaviour at α = {ALPHA} — behavioural approximation", y=1.0)
    fig.tight_layout()
    fig_path = FIG_DIR / "dsm_explorer.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "k": np.arange(N),
        "m_mash1": out[1][0], "e_dsm_mash1": out[1][1],
        "m_mash2": out[2][0], "e_dsm_mash2": out[2][1],
        "m_mash3": out[3][0], "e_dsm_mash3": out[3][1],
    }).to_csv(DATA_DIR / "dsm_explorer.csv", index=False)

    for o, (m, e) in out.items():
        print(f"[dsm] order={o}  mean(m)={m.mean():.4f}  std(e_dsm)={e[N//4:].std():.3f}")
    print(f"[dsm] saved {fig_path}")


if __name__ == "__main__":
    main()
