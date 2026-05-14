"""NTF family overlay.

Two panels:
  1) |H_ref|, |H_dco|, |H_dtc|, |H_bbpd_in| magnitudes (closed-loop).
  2) The same four NTFs applied to representative noise sources, on a
     dBc/Hz axis, showing which contribution dominates at each offset.

Saves:
    results/data/ntf_family.csv
    results/figures/ntf_family.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DATA_DIR, FIG_DIR, behavioral_caption
from sim.pll_params import PLLParams
from sim.noise_tf import open_loop_gain, ntf_ref, ntf_dco_pn
from sim.bbpd import BBPD


def main() -> None:
    p = PLLParams()
    K_bb = BBPD.linearized_gain(1e-12)               # σ ≈ 1 ps reference

    f = np.logspace(2, np.log10(p.f_ref / 2), 600)
    L = open_loop_gain(f, K_bb, p)
    H_ref = L / (1.0 + L)        # ref jitter, DTC noise both come in here
    H_dco = 1.0 / (1.0 + L)      # DCO PN

    # Magnitudes
    fig, axes = plt.subplots(2, 1, figsize=(9, 9))
    ax = axes[0]
    ax.loglog(f, np.abs(H_ref), lw=1.1, color="C0",
              label="|H_ref|     = L/(1+L)  (reference jitter)")
    ax.loglog(f, np.abs(H_dco), lw=1.1, color="C3",
              label="|H_DCO|    = 1/(1+L)  (DCO phase noise)")
    ax.loglog(f, np.abs(H_ref), lw=1.1, color="C2", ls="--",
              label="|H_DTC|    = L/(1+L)  (DTC residual noise)")
    ax.loglog(f, np.abs(H_ref), lw=1.1, color="C4", ls=":",
              label="|H_BBPD_in| = L/(1+L)  (BBPD-folded noise)")
    ax.axhline(1.0, color="k", lw=0.4, ls="--")
    idx_x = int(np.argmin(np.abs(np.abs(L) - 1.0)))
    f_x = float(f[idx_x])
    ax.axvline(f_x, color="C2", lw=0.5, ls=":")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("|H(f)|")
    ax.set_title("Closed-loop NTF magnitudes "
                 "(ref/DTC/BBPD overlap — same loop entry)")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)

    # Apply to noise sources
    # DCO PN template
    log_f = np.log10(np.clip(f, 1.0, None))
    L_open_db = np.interp(log_f,
                          np.log10(p.dco_pn_freqs_hz), p.dco_pn_levels_dbchz,
                          left=p.dco_pn_levels_dbchz[0],
                          right=p.dco_pn_levels_dbchz[-1])
    S_phi_dco_open = 2.0 * 10.0 ** (L_open_db / 10.0)
    # Reference jitter PSD as L(f) referred to DCO carrier
    S_t_ref_one = p.ref_jitter_rms_s ** 2 / (p.f_ref / 2.0)
    S_phi_ref = (2 * np.pi * p.f_dco_nominal) ** 2 * S_t_ref_one
    # BBPD noise PSD (input-referred / detector-output)
    S_t_bbpd_in = 2.0 / (K_bb ** 2 * p.f_ref)
    S_phi_bbpd = (2 * np.pi * p.f_dco_nominal) ** 2 * S_t_bbpd_in

    contribs = {
        "DCO PN (HP shaped)":     np.abs(H_dco) ** 2 * S_phi_dco_open,
        "Reference jitter (LP)":  np.abs(H_ref) ** 2 * np.full_like(f, S_phi_ref),
        "BBPD quantization (LP)": np.abs(H_ref) ** 2 * np.full_like(f, S_phi_bbpd),
    }
    total = sum(contribs.values())

    def to_dbchz(S):
        return 10.0 * np.log10(np.maximum(S / 2.0, 1e-300))

    ax = axes[1]
    colors = {"DCO PN (HP shaped)": "C3",
              "Reference jitter (LP)": "C0",
              "BBPD quantization (LP)": "C4"}
    for name, S in contribs.items():
        ax.semilogx(f, to_dbchz(S), lw=1.0, color=colors[name], label=name)
    ax.semilogx(f, to_dbchz(total), lw=1.4, color="k", label="total")
    ax.axvline(f_x, color="C2", lw=0.5, ls=":")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Per-source closed-loop contributions and their sum")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9, loc="lower left")
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "ntf_family.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "f_hz": f,
        "H_ref_abs": np.abs(H_ref),
        "H_dco_abs": np.abs(H_dco),
        "L_dco_dbchz": to_dbchz(contribs["DCO PN (HP shaped)"]),
        "L_ref_dbchz": to_dbchz(contribs["Reference jitter (LP)"]),
        "L_bbpd_dbchz": to_dbchz(contribs["BBPD quantization (LP)"]),
        "L_total_dbchz": to_dbchz(total),
    }).to_csv(DATA_DIR / "ntf_family.csv", index=False)
    print(f"[ntf-family] crossover ≈ {f_x/1e3:.0f} kHz")
    print(f"[ntf-family] saved {fig_path}")


if __name__ == "__main__":
    main()
