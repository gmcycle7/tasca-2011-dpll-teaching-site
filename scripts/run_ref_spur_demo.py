"""Reference-spur demo.

Inject a deterministic sinusoidal perturbation into the reference edge
time and look at how the closed loop translates that into a spectral
spike on the DCO output. Three panels:

  1) Reference edge timing — clean vs. with sinusoidal modulation.
  2) Output L(f) — the spur peak at the injected offset frequency.
  3) Sweep of injected amplitude vs. resulting spur level at the
     output, showing the 1:1 dBc/Hz tracking (predicted by H_ref).

Saves:
    results/data/ref_spur.csv
    results/figures/ref_spur.png
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


def main() -> None:
    base = PLLParams(n_cycles=200_000)
    f_spur_hz = 500e3
    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # ---------- Panel 1: reference timing ----------
    n_show = 200
    t_ref_clean = np.arange(n_show) * base.T_ref
    t_ref_spur  = t_ref_clean + 5e-12 * np.sin(
        2 * np.pi * f_spur_hz * np.arange(n_show) * base.T_ref)
    ax = axes[0]
    ax.plot(np.arange(n_show), (t_ref_clean - t_ref_clean) * 1e12,
            "o", ms=2, color="C0", label="clean reference (zero jitter)")
    ax.plot(np.arange(n_show), (t_ref_spur - t_ref_clean) * 1e12,
            "x", ms=3, color="C3",
            label=f"with 5 ps sinusoid @ {f_spur_hz/1e3:.0f} kHz")
    ax.set_xlabel("ref cycle k")
    ax.set_ylabel("ref-edge offset [ps]")
    ax.set_title("Reference edge timing perturbation (k = 0 … 200)")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: output L(f) with vs. without spur ----------
    p_clean = dataclasses.replace(base, ref_spur_amp_s=0.0)
    p_spur  = dataclasses.replace(base, ref_spur_amp_s=5e-12,
                                  ref_spur_freq_hz=f_spur_hz)

    res_c = run_simulation(p_clean, enable_dtc=True,
                           enable_dco_pn=True, enable_ref_noise=True)
    res_s = run_simulation(p_spur,  enable_dtc=True,
                           enable_dco_pn=True, enable_ref_noise=True)
    phi_c = excess_phase_at_dco(res_c, trim_settling=0.3)
    phi_s = excess_phase_at_dco(res_s, trim_settling=0.3)
    f_c, L_c = estimate_psd(phi_c, fs=base.f_ref,
                            nperseg=min(len(phi_c), 1 << 15))
    f_s, L_s = estimate_psd(phi_s, fs=base.f_ref,
                            nperseg=min(len(phi_s), 1 << 15))
    ax = axes[1]
    mask = f_c > base.f_ref / len(phi_c)
    ax.semilogx(f_c[mask], L_c[mask], lw=0.7, color="C0", label="clean ref")
    ax.semilogx(f_s[mask], L_s[mask], lw=0.7, color="C3",
                label=f"with 5 ps spur @ {f_spur_hz/1e3:.0f} kHz")
    ax.axvline(f_spur_hz, color="C2", lw=0.6, ls="--",
               label="injected frequency")
    ax.set_xlabel("offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop L(f) — spike at the injection offset")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 3: amplitude sweep ----------
    amps_ps = np.array([1.0, 2.0, 4.0, 8.0, 16.0])
    peak_lvls = []
    for a in amps_ps:
        p = dataclasses.replace(base, ref_spur_amp_s=a * 1e-12,
                                ref_spur_freq_hz=f_spur_hz)
        res = run_simulation(p, enable_dtc=True,
                             enable_dco_pn=True, enable_ref_noise=True)
        phi = excess_phase_at_dco(res, trim_settling=0.3)
        f, L = estimate_psd(phi, fs=base.f_ref,
                            nperseg=min(len(phi), 1 << 14))
        idx = int(np.argmin(np.abs(f - f_spur_hz)))
        win = max(2, len(f) // 200)
        peak_lvls.append(float(np.max(L[max(idx - win, 0):
                                        min(idx + win, len(f) - 1)])))
        print(f"[ref-spur] amp={a:.1f} ps  →  peak = {peak_lvls[-1]:.1f} dBc/Hz")
    ax = axes[2]
    ax.semilogx(amps_ps, peak_lvls, "o-", lw=1.0, color="C3")
    # Theoretical 20·log10(amp) slope shifted to match
    theory = 20.0 * np.log10(amps_ps / amps_ps[0]) + peak_lvls[0]
    ax.semilogx(amps_ps, theory, lw=0.6, ls="--", color="k",
                label="20·log₁₀(amplitude) slope")
    ax.set_xlabel("injected reference-spur amplitude [ps]")
    ax.set_ylabel("output spur peak [dBc/Hz]")
    ax.set_title("Output spur level scales linearly with reference modulation")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)
    behavioral_caption(ax)

    fig.tight_layout()
    fig_path = FIG_DIR / "ref_spur.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({"amp_ps": amps_ps, "peak_dbchz": peak_lvls}).to_csv(
        DATA_DIR / "ref_spur.csv", index=False)
    print(f"[ref-spur] saved {fig_path}")


if __name__ == "__main__":
    main()
