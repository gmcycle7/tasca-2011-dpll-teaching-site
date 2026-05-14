"""Minimal regression tests for the behavioural simulator.

These exist to catch silent breakage of the sim/ modules. They are NOT
chip-validation tests — they only assert that the model behaves the way
the docs claim. Run with:

    python -m pytest tests/ -q
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pytest

# Allow `import sim` without a real install
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.bbpd import BBPD                                  # noqa: E402
from sim.dco import DCO                                    # noqa: E402
from sim.dsm import MASH                                   # noqa: E402
from sim.dtc import DTC                                    # noqa: E402
from sim.jitter import integrated_rms_jitter_s             # noqa: E402
from sim.noise_tf import (                                 # noqa: E402
    open_loop_gain, ntf_dco_pn, ntf_ref, estimate_kbb_from_sim,
)
from sim.phase_noise import estimate_psd, generate_pn_sequence  # noqa: E402
from sim.pll_model import run_simulation, excess_phase_at_dco   # noqa: E402
from sim.pll_params import PLLParams                       # noqa: E402


# ---------- Block-level ----------

@pytest.mark.parametrize("order", [1, 2, 3])
def test_dsm_long_run_mean(order):
    dsm = MASH(order=order, quant_levels=1 << 20, seed=order)
    N, alpha = 50_000, 0.275
    m = np.fromiter(
        (dsm.step(alpha)[0] for _ in range(N)), dtype=float, count=N
    )
    assert np.abs(m.mean() - alpha) < 5e-4


def test_dsm_residue_bounded_mash3():
    dsm = MASH(order=3, quant_levels=1 << 20, seed=0)
    e_max = 0.0
    for _ in range(50_000):
        _, e = dsm.step(0.125)
        e_max = max(e_max, abs(e))
    assert e_max < 3.0   # MASH-1-1-1 residue bound; ±2 in theory, allow 3


def test_bbpd_sign_only():
    bb = BBPD(meta_noise_rms_s=0.0)
    assert bb.decide(1e-13) == 1
    assert bb.decide(-1e-13) == -1
    # Tie -> randomized
    seen = {bb.decide(0.0) for _ in range(50)}
    assert seen.issubset({-1, 1})


def test_bbpd_linearized_gain_formula():
    K = BBPD.linearized_gain(1e-12)
    assert abs(K - np.sqrt(2.0 / np.pi) / 1e-12) < 1e-3


def test_dtc_ideal_is_identity():
    d = DTC(full_scale_s=25e-9)
    for tau in (0.0, 1e-12, 1e-10, 1e-9):
        out = float(d.apply(tau))
        # Default lsb_s = 0 → no quantisation
        assert abs(out - tau) < 1e-18


def test_dtc_gain_error_scales_linearly():
    d = DTC(gain_err=0.1, full_scale_s=25e-9)
    assert abs(float(d.apply(1e-9)) - 1.1e-9) < 1e-18


def test_dco_linear_tuning():
    dco = DCO(f_dco_nominal=3.6e9, K_dco=10e3)
    assert abs(dco.frequency(0) - 3.6e9) < 1e-3
    assert abs(dco.frequency(100) - (3.6e9 + 100 * 10e3)) < 1e-3


# ---------- Loop-level ----------

def test_loop_locks_default():
    p = PLLParams(n_cycles=20_000)
    p.f_dco_nominal = p.f_out_target - 1e6
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=False, enable_ref_noise=False)
    tail = slice(int(0.8 * p.n_cycles), None)
    df_mean = res.f_dco[tail].mean() - p.f_out_target
    # The hunting toggle is ±Kp*K_DCO; just check we landed near target
    assert abs(df_mean) < 100e3
    # Mean BBPD output ≈ 0 in lock
    assert abs(res.s_bbpd[tail].mean()) < 0.2


def test_dtc_on_reduces_bbpd_error():
    p = PLLParams(n_cycles=20_000)
    on = run_simulation(p, enable_dtc=True,
                        enable_dco_pn=False, enable_ref_noise=False)
    off = run_simulation(p, enable_dtc=False,
                         enable_dco_pn=False, enable_ref_noise=False)
    tail = slice(int(0.6 * p.n_cycles), None)
    rms_on = on.e_bbpd[tail].std()
    rms_off = off.e_bbpd[tail].std()
    assert rms_on < rms_off / 50.0   # at least 50x reduction


def test_lms_converges_to_inverse_gain():
    p = PLLParams(n_cycles=120_000, dtc_gain_err=0.10, lms_mu=2e-4)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True,
                         enable_lms=True)
    target = 1.0 / 1.10
    tail = res.g_hat[int(0.9 * p.n_cycles):]
    assert abs(tail.mean() - target) < 5e-3


# ---------- Signal-processing pipeline ----------

def test_pn_psd_roundtrip():
    rng = np.random.default_rng(0)
    fs = 40e6
    n = 1 << 14
    target = (-100.0,) * 6
    freqs  = (1e3, 10e3, 100e3, 1e6, 10e6, 1.9e7)
    phi = generate_pn_sequence(n, fs, freqs, target, rng=rng)
    f, L = estimate_psd(phi, fs=fs, nperseg=1 << 12)
    # In-band median should be near the flat target -100 dBc/Hz
    band = (f > 1e4) & (f < 1e7)
    med = float(np.median(L[band]))
    assert abs(med - (-100)) < 2.0   # within 2 dB of target


def test_jitter_integration_white_floor():
    fs = 40e6
    f = np.linspace(1e3, fs / 2, 2000)
    L_db = -120.0 * np.ones_like(f)
    sigma = integrated_rms_jitter_s(f, L_db, 1e3, 1e7, 3.6e9)
    # Predict: 2 * 10^-12 * (1e7 - 1e3) = ~2e-5 rad^2 → sigma_t ~ 0.2 ps
    assert 0.5e-13 < sigma < 1e-12


# ---------- Linear NTF cross-check ----------

def test_ntf_high_low_pass_complementary():
    p = PLLParams()
    K_bb = BBPD.linearized_gain(1e-12)
    f = np.logspace(2, np.log10(p.f_ref / 2), 200)
    Hr = ntf_ref(f, K_bb, p)
    Hd = ntf_dco_pn(f, K_bb, p)
    # By construction L/(1+L) + 1/(1+L) = 1 (complex)
    err = np.max(np.abs((Hr + Hd) - 1.0))
    assert err < 1e-9


def test_open_loop_gain_has_positive_phase_margin():
    p = PLLParams()
    K_bb = BBPD.linearized_gain(1e-12)
    f = np.logspace(2, np.log10(p.f_ref / 2), 600)
    L = open_loop_gain(f, K_bb, p)
    idx_x = int(np.argmin(np.abs(np.abs(L) - 1.0)))
    pm = 180.0 + np.angle(L[idx_x]) * 180.0 / np.pi
    assert pm > 30.0   # plenty of phase margin in default config


def test_estimate_kbb_recovers_analytic():
    rng = np.random.default_rng(0)
    sigma = 0.7e-12
    n = 50_000
    e = rng.normal(0.0, sigma, n)
    K = estimate_kbb_from_sim(e, trim_settling=0.0)
    expected = BBPD.linearized_gain(sigma)
    # Recovery within 5%
    assert abs(K - expected) / expected < 0.05


# ---------- End-to-end headline regression ----------

def test_default_run_integrated_jitter_in_range():
    """Quick PSD+jitter pipeline check on a short run."""
    p = PLLParams(n_cycles=80_000)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True)
    phi = excess_phase_at_dco(res, trim_settling=0.4)
    f, L = estimate_psd(phi, fs=p.f_ref, nperseg=min(len(phi), 1 << 14))
    sigma = integrated_rms_jitter_s(f, L, 3e3, 20e6, p.f_out_target)
    # Demo target is ~500 fs RMS with our defaults; allow factor of 2.
    assert 200e-15 < sigma < 1500e-15
