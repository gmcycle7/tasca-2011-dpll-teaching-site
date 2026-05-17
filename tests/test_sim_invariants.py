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


# =============================================================================
# Tests for newly added features (P1 + P2 build-out)
# =============================================================================
from sim.allan import (                                  # noqa: E402
    overlapping_adev, fractional_frequency_from_edges, adev_from_div_edges,
)
from sim.dtc import DTC                                  # noqa: E402
from sim.loop_filter import DigitalPI                    # noqa: E402
from sim.phase_noise import (                            # noqa: E402
    physics_dco_pn_template, physics_ref_pn_template,
)
from sim.realistic_dco import RealisticDCO               # noqa: E402


# ---------- Loop filter smoothing pole ----------

def test_loop_filter_pole_alpha_smooths_integral_branch():
    # Single +1 impulse, then 30 zeros. Integrator state = 1 throughout,
    # so the un-smoothed integral output is 1 instantly; the IIR-smoothed
    # output starts at alpha and asymptotes to 1 over ~1/alpha samples.
    lf_no  = DigitalPI(Kp=0.0, Ki=1.0, pole_alpha=1.0)
    lf_yes = DigitalPI(Kp=0.0, Ki=1.0, pole_alpha=0.1)
    out_no  = [lf_no.step(1.0)]  + [lf_no.step(0.0)  for _ in range(60)]
    out_yes = [lf_yes.step(1.0)] + [lf_yes.step(0.0) for _ in range(60)]
    # First-sample lag from the smoothing
    assert out_yes[0] < out_no[0]
    assert out_yes[0] == pytest.approx(0.1, rel=0.01)
    # Long-run convergence to the same value
    assert abs(out_yes[-1] - out_no[-1]) < 0.05


# ---------- DTC INL lookup table ----------

def test_dtc_inl_table_overrides_sinusoid():
    table = np.array([1e-12, -2e-12, 3e-12, -1e-12])
    d = DTC(inl_amp_s=999e-12, inl_periods=2,           # would scream if used
            full_scale_s=4e-9, inl_table_s=table)
    # tau_target spanning the full scale (4 ns) should hit each bin
    taus = np.linspace(0.0, 4e-9, 4, endpoint=False)
    expected_inl = table
    actual = np.array([d.apply(t) - t for t in taus])
    np.testing.assert_allclose(actual, expected_inl, atol=1e-15)


# ---------- Multi-bit BBPD ----------

def test_multibit_bbpd_quantises_into_expected_range():
    bb = BBPD(n_bits=3, full_scale_s=8e-12)
    # In-range
    assert bb.decide(0.0) in range(-4, 4)
    # Saturating positive
    assert bb.decide(1.0) == 3
    # Saturating negative
    assert bb.decide(-1.0) == -4


def test_bbpd_default_is_1bit():
    bb = BBPD()
    out = {bb.decide(1e-12), bb.decide(-1e-12)}
    assert out == {-1, 1}


# ---------- DCO PN physics template ----------

def test_physics_dco_pn_anchors_at_1MHz():
    # f_max chosen well above where 1/f^2 hits the floor:
    #   1/f^2 region anchored at -120 dBc/Hz @ 1 MHz, floor at -150 dBc/Hz,
    #   so floor takes over at 1e6 * 10^((-120+150)/20) ≈ 32 MHz.
    freqs, levels = physics_dco_pn_template(L_1MHz_dbchz=-120.0,
                                            flicker_corner_hz=100e3,
                                            thermal_floor_dbchz=-150.0,
                                            f_min_hz=1e4, f_max_hz=300e6,
                                            n_points=300)
    freqs = np.asarray(freqs)
    levels = np.asarray(levels)
    # Anchor at 1 MHz
    i_1m = int(np.argmin(np.abs(freqs - 1e6)))
    assert abs(levels[i_1m] - (-120.0)) < 1.0
    # White floor at very high offset
    assert abs(levels[-1] - (-150.0)) < 2.0
    # Slope steeper than 1/f^2 below the flicker corner
    i_lo = int(np.argmin(np.abs(freqs - 1e4)))
    slope_dec = (levels[i_lo] - levels[i_1m]) / np.log10(1e6 / freqs[i_lo])
    assert slope_dec > 25.0   # near -30 dB/dec in flicker region


def test_physics_ref_pn_floor():
    freqs, levels = physics_ref_pn_template(L_10kHz_dbchz=-150.0,
                                            corner_hz=10e3,
                                            floor_dbchz=-165.0,
                                            f_min_hz=1e3, f_max_hz=10e6,
                                            n_points=50)
    levels = np.asarray(levels)
    # High-frequency end should be near the floor
    assert abs(levels[-1] - (-165.0)) < 2.0


# ---------- RealisticDCO ----------

def test_realistic_dco_sub_lsb_dither_averages():
    dco = RealisticDCO(f_nominal=3.6e9, coarse_lsb_hz=1e6,
                        fine_lsb_hz=1e3, dither_bits=14, seed=1)
    samples = np.array([dco.frequency(50.3) for _ in range(10_000)])
    # Mean should land within 5% of 50.3 fine-LSBs above f_nominal
    target = 3.6e9 + 50.3 * 1e3
    rel_err = abs(samples.mean() - target) / 1e3   # in fine LSBs
    assert rel_err < 0.05


# ---------- Allan deviation ----------

def test_allan_deviation_white_y_slope_minus_half():
    rng = np.random.default_rng(0)
    # 10 000 samples of white fractional-frequency noise at tau0 = 1 us
    y = rng.normal(0.0, 1e-12, 10_000)
    tau, adev = overlapping_adev(y, tau0_s=1e-6)
    # Discard endpoints; fit log-log slope
    mask = (tau > 1e-5) & (tau < 1e-3)
    slope = np.polyfit(np.log10(tau[mask]), np.log10(adev[mask]), 1)[0]
    # White FM gives σ_y ∝ τ^(-1/2)
    assert -0.6 < slope < -0.4


def test_adev_from_div_edges_runs():
    # Stub trace: ideal edges at multiples of T_ref + tiny jitter
    T_ref = 25e-9
    n = 5_000
    rng = np.random.default_rng(0)
    t = np.cumsum(T_ref + rng.normal(0, 1e-14, n))
    tau, adev = adev_from_div_edges(t, T_ref)
    # ADEV should be finite, positive, and decreasing on average
    assert np.all(np.isfinite(adev))
    assert np.all(adev > 0)


# ---------- LMS offset calibration ----------

def test_lms_offset_drives_static_dtc_offset_into_calibration():
    p = PLLParams(n_cycles=100_000,
                  dtc_offset_s=5e-12,     # 5 ps static offset
                  lms_mu_offset=3e-4)
    res = run_simulation(p, enable_dtc=True,
                         enable_dco_pn=True, enable_ref_noise=True,
                         enable_lms=True)
    tail = res.offset_hat[int(0.9 * p.n_cycles):]
    # offset_hat should track the DTC offset (sign-flipped because we
    # subtract offset_hat in the DTC drive)
    assert abs(tail.mean() - 5e-12) < 3e-12
