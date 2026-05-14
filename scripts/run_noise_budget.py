"""Per-source noise-budget visualisation.

Three panels:
  1) Stacked closed-loop L(f) decomposition: DCO PN, ref jitter,
     BBPD-folded noise — sum equals the simulated total.
  2) Integrated RMS jitter vs. integration upper limit f_hi, with the
     paper's stated 560 fs marker.
  3) Pie of jitter² budget over the paper's band (3 kHz – 20 MHz),
     showing which source contributes how much variance.

Saves:
    results/data/noise_budget.csv
    results/figures/noise_budget.png
"""
from __future__ import annotations

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
from sim.noise_tf import open_loop_gain, ntf_ref, ntf_dco_pn, estimate_kbb_from_sim


def main() -> None:
    p = PLLParams(n_cycles=200_000)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    phi = excess_phase_at_dco(res, trim_settling=0.3)
    f_sim, L_sim = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 15))
    K_bb = estimate_kbb_from_sim(res.e_bbpd, trim_settling=0.3)

    f = f_sim.copy()
    L = open_loop_gain(f, K_bb, p)
    H_ref = ntf_ref(f, K_bb, p)
    H_dco = ntf_dco_pn(f, K_bb, p)

    log_f = np.log10(np.clip(f, 1.0, None))
    L_open_db = np.interp(log_f,
                          np.log10(p.dco_pn_freqs_hz), p.dco_pn_levels_dbchz,
                          left=p.dco_pn_levels_dbchz[0],
                          right=p.dco_pn_levels_dbchz[-1])
    S_phi_dco_open = 2.0 * 10.0 ** (L_open_db / 10.0)
    S_t_ref_one = p.ref_jitter_rms_s ** 2 / (p.f_ref / 2.0)
    S_phi_ref = (2 * np.pi * p.f_dco_nominal) ** 2 * S_t_ref_one
    S_t_bbpd_in = 2.0 / (K_bb ** 2 * p.f_ref)
    S_phi_bbpd = (2 * np.pi * p.f_dco_nominal) ** 2 * S_t_bbpd_in

    S_dco = np.abs(H_dco) ** 2 * S_phi_dco_open
    S_ref = np.abs(H_ref) ** 2 * S_phi_ref
    S_bbp = np.abs(H_ref) ** 2 * S_phi_bbpd

    def to_dbchz(S): return 10 * np.log10(np.maximum(S / 2.0, 1e-300))
    L_dco, L_ref, L_bbp = to_dbchz(S_dco), to_dbchz(S_ref), to_dbchz(S_bbp)
    L_total_an = to_dbchz(S_dco + S_ref + S_bbp)

    fig, axes = plt.subplots(3, 1, figsize=(10, 12))

    # ---------- Panel 1: stacked decomposition ----------
    ax = axes[0]
    mask = f > p.f_ref / len(phi)
    ax.semilogx(f[mask], L_sim[mask], lw=0.8, color="C7",
                label="Simulated L(f)")
    ax.semilogx(f[mask], L_dco[mask], lw=1.0, color="C3", label="DCO PN")
    ax.semilogx(f[mask], L_ref[mask], lw=1.0, color="C0", label="Reference jitter")
    ax.semilogx(f[mask], L_bbp[mask], lw=1.0, color="C4", label="BBPD quantization")
    ax.semilogx(f[mask], L_total_an[mask], lw=1.4, color="k",
                label="analytic sum")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Per-source contribution to closed-loop L(f)")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9, loc="lower left")

    # ---------- Panel 2: integrated jitter vs f_hi ----------
    f_hi_grid = np.logspace(np.log10(2e3), np.log10(p.f_ref / 2), 60)
    sigma_dco  = [integrated_rms_jitter_s(f, L_dco,  3e3, fh, p.f_out_target) for fh in f_hi_grid]
    sigma_ref  = [integrated_rms_jitter_s(f, L_ref,  3e3, fh, p.f_out_target) for fh in f_hi_grid]
    sigma_bbp  = [integrated_rms_jitter_s(f, L_bbp,  3e3, fh, p.f_out_target) for fh in f_hi_grid]
    sigma_sim  = [integrated_rms_jitter_s(f, L_sim,  3e3, fh, p.f_out_target) for fh in f_hi_grid]

    ax = axes[1]
    ax.semilogx(f_hi_grid, np.array(sigma_sim) * 1e15, lw=1.1, color="C7",
                label="Simulated")
    ax.semilogx(f_hi_grid, np.array(sigma_dco) * 1e15, lw=0.9, color="C3",
                label="DCO PN only")
    ax.semilogx(f_hi_grid, np.array(sigma_ref) * 1e15, lw=0.9, color="C0",
                label="Ref only")
    ax.semilogx(f_hi_grid, np.array(sigma_bbp) * 1e15, lw=0.9, color="C4",
                label="BBPD only")
    ax.axhline(560, color="C2", lw=0.8, ls="--", label="paper headline 560 fs")
    ax.set_xlabel("integration upper bound f_hi [Hz]  (f_lo = 3 kHz)")
    ax.set_ylabel("integrated jitter [fs RMS]")
    ax.set_title("RMS jitter accumulated up to f_hi")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9, loc="upper left")

    # ---------- Panel 3: variance pie over 3 kHz - 20 MHz ----------
    def var(S):
        m = (f >= 3e3) & (f <= 20e6)
        return 2.0 * np.trapezoid(S[m] / 2.0, f[m]) if hasattr(np, "trapezoid") \
               else 2.0 * np.trapz(S[m] / 2.0, f[m])
    v_dco = var(S_dco); v_ref = var(S_ref); v_bbp = var(S_bbp)
    total_v = v_dco + v_ref + v_bbp
    sizes  = [v_dco, v_ref, v_bbp]
    labels = [f"DCO PN  ({100*v_dco/total_v:.0f}%)",
              f"Ref     ({100*v_ref/total_v:.0f}%)",
              f"BBPD    ({100*v_bbp/total_v:.0f}%)"]
    ax = axes[2]
    ax.pie(sizes, labels=labels, colors=["C3", "C0", "C4"],
           wedgeprops=dict(width=0.4, edgecolor="white"),
           autopct=None, startangle=90)
    ax.set_title("Phase-variance budget over 3 kHz – 20 MHz "
                 f"(σ_total ≈ {np.sqrt(total_v)/(2*np.pi*p.f_dco_nominal)*1e15:.0f} fs)")
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "noise_budget.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "f_hi_hz": f_hi_grid,
        "sigma_sim_fs": np.array(sigma_sim) * 1e15,
        "sigma_dco_fs": np.array(sigma_dco) * 1e15,
        "sigma_ref_fs": np.array(sigma_ref) * 1e15,
        "sigma_bbpd_fs": np.array(sigma_bbp) * 1e15,
    }).to_csv(DATA_DIR / "noise_budget.csv", index=False)

    print(f"[budget] DCO contribution: {100*v_dco/total_v:.1f}%")
    print(f"[budget] Ref contribution: {100*v_ref/total_v:.1f}%")
    print(f"[budget] BBPD contribution: {100*v_bbp/total_v:.1f}%")
    print(f"[budget] saved {fig_path}")


if __name__ == "__main__":
    main()
