"""BBPD explorer.

Four panels:
  1) Static sign() vs ensemble-averaged S-curve with Gaussian dither.
  2) Linearized gain K_bb vs input sigma: analytic + Monte-Carlo.
  3) BBPD output autocorrelation — show it is approximately white.
  4) BBPD output PSD — confirm flat spectrum.

Saves:
    results/data/bbpd_explorer.csv
    results/figures/bbpd_explorer.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal as sig
from scipy.special import erf

from _common import DATA_DIR, FIG_DIR, behavioral_caption


F_REF = 40e6
N_MC  = 200_000


def main() -> None:
    rng = np.random.default_rng(0)

    # ---------- Panel 1: static + averaged S-curves ----------
    e_grid = np.linspace(-5e-12, 5e-12, 401)         # input time error [s]
    sigmas = [0.5e-12, 1.0e-12, 2.0e-12]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    ax = axes[0, 0]
    ax.step(e_grid * 1e12, np.sign(e_grid), where="mid",
            color="k", lw=1.2, label="sign(e) — no noise")
    for s in sigmas:
        # E[sign(e + n)] = erf(e / (σ·√2))
        ax.plot(e_grid * 1e12, erf(e_grid / (s * np.sqrt(2))),
                lw=1.0, label=f"E[sign(e+n)], σ = {s*1e12:.1f} ps")
    ax.axhline(0, color="grey", lw=0.4, ls=":")
    ax.axvline(0, color="grey", lw=0.4, ls=":")
    ax.set_xlabel("input time error e  [ps]")
    ax.set_ylabel("BBPD averaged output")
    ax.set_title("Static vs. averaged BBPD characteristic")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 2: K_bb vs sigma ----------
    sigma_sweep = np.logspace(-13, -10, 25)        # 0.1 ps - 100 ps
    K_analytic = np.sqrt(2.0 / np.pi) / sigma_sweep
    K_mc = np.zeros_like(sigma_sweep)
    for i, s in enumerate(sigma_sweep):
        # Small probing signal, large dither
        e_probe = 0.05 * s
        n = rng.normal(0.0, s, N_MC)
        s_plus  = np.sign(e_probe + n).mean()
        s_minus = np.sign(-e_probe + n).mean()
        K_mc[i] = (s_plus - s_minus) / (2 * e_probe)

    ax = axes[0, 1]
    ax.loglog(sigma_sweep * 1e12, K_analytic, color="C0", lw=1.2,
              label="K_bb = √(2/π)/σ  (analytic)")
    ax.loglog(sigma_sweep * 1e12, K_mc, "x", color="C3", ms=6,
              label=f"Monte-Carlo  (N = {N_MC:,})")
    ax.set_xlabel("input σ [ps]")
    ax.set_ylabel("K_bb [s⁻¹]")
    ax.set_title("Linearised BBPD gain")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)

    # ---------- Panel 3: BBPD output autocorrelation at lock ----------
    sigma_lock = 1e-12
    e_zero = np.zeros(N_MC)
    n = rng.normal(0.0, sigma_lock, N_MC)
    s_seq = np.sign(e_zero + n).astype(float)
    # Unbiased autocorrelation, normalized
    n_lags = 50
    r = np.array([np.mean(s_seq[:N_MC - lag] * s_seq[lag:])
                  for lag in range(n_lags)])
    r = r / r[0]
    ax = axes[1, 0]
    ax.stem(np.arange(n_lags), r, basefmt=" ")
    ax.axhline(0, color="grey", lw=0.5)
    ax.set_xlabel("lag k")
    ax.set_ylabel("normalized R_s[k]")
    ax.set_title(f"BBPD output autocorrelation  (e=0, σ={sigma_lock*1e12:.0f} ps)")
    ax.grid(True, alpha=0.4)
    ax.set_ylim(-0.2, 1.05)

    # ---------- Panel 4: BBPD output PSD ----------
    f, P = sig.welch(s_seq - s_seq.mean(), fs=F_REF, nperseg=1 << 13)
    ax = axes[1, 1]
    ax.semilogx(f[1:], 10 * np.log10(P[1:]), color="C0", lw=0.8,
                label="PSD of s[k]")
    # Theory: one-sided PSD of unit-variance white seq = 2/f_ref
    theory = 10 * np.log10(2.0 / F_REF)
    ax.axhline(theory, color="C3", lw=1.0, ls="--",
               label=f"theory: 2/f_ref ≈ {theory:.1f} dB")
    ax.set_xlabel("f [Hz]")
    ax.set_ylabel("PSD [dB/Hz]")
    ax.set_title("BBPD output PSD — approximately white")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend(fontsize=9)

    behavioral_caption(axes[1, 1])
    fig.suptitle("BBPD characterisation — behavioural approximation", y=1.0)
    fig.tight_layout()
    fig_path = FIG_DIR / "bbpd_explorer.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    pd.DataFrame({
        "sigma_s": sigma_sweep,
        "K_bb_analytic": K_analytic,
        "K_bb_mc": K_mc,
    }).to_csv(DATA_DIR / "bbpd_explorer.csv", index=False)

    print("[bbpd] Monte-Carlo K_bb matches analytic to "
          f"{np.median(np.abs(K_mc - K_analytic) / K_analytic) * 100:.1f}% "
          "(median rel. error)")
    print(f"[bbpd] saved {fig_path}")


if __name__ == "__main__":
    main()
