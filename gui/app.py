"""Streamlit GUI for the Tasca 2011 DPLL behavioral simulator.

Launch from the project root:

    streamlit run gui/app.py

Every plot is a behavioral approximation, NOT a silicon measurement.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from sim.pll_params import PLLParams
from sim.pll_model import run_simulation, excess_phase_at_dco
from sim.phase_noise import estimate_psd
from sim.jitter import integrated_rms_jitter_s
from sim.spurs import detect_spurs


# -----------------------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Tasca 2011 DPLL — Behavioral GUI",
                   layout="wide")
st.title("Tasca 2011 Fractional-N DPLL — Behavioral Simulator")
st.caption("Behavioral approximation — NOT a silicon measurement. "
           "Defaults are estimated; see docs/assumptions.md.")


# -----------------------------------------------------------------------------
# Sidebar: parameters
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Core PLL parameters")
    f_ref_mhz = st.number_input("f_ref [MHz]", 1.0, 200.0, 40.0, step=1.0)
    f_out_ghz = st.number_input("f_out [GHz]", 0.5, 10.0, 3.605,
                                step=0.001, format="%.3f")
    K_dco_khz = st.number_input("K_DCO [kHz / LSB]", 0.1, 1000.0, 10.0,
                                step=0.5)
    col_kp, col_ki = st.columns(2)
    Kp = col_kp.number_input("Kp", 0.0, 100.0, 8.0, step=0.5)
    Ki = col_ki.number_input("Ki", 0.0, 10.0, 0.5, step=0.05)
    n_cycles = st.select_slider(
        "n_cycles",
        options=[5_000, 10_000, 20_000, 40_000, 60_000, 80_000,
                 120_000, 200_000, 300_000, 400_000],
        value=60_000)
    rng_seed = st.number_input("RNG seed", 0, 10_000_000, 12345, step=1)

    st.header("DSM / DTC impairments")
    dsm_order = st.selectbox("DSM order (MASH)", [1, 2, 3], index=2)
    dtc_gain_err = st.slider("DTC gain error [-]",
                             -0.30, 0.30, 0.00, step=0.01)
    dtc_inl_amp_ps = st.slider("DTC INL amplitude [ps]",
                               0.0, 10.0, 0.0, step=0.1)
    dtc_inl_periods = st.slider("DTC INL ripple periods", 1, 20, 4)
    dtc_lsb_ps = st.slider("DTC quantization LSB [ps]",
                           0.1, 50.0, 1.0, step=0.1)

    st.subheader("LMS DTC-gain calibration")
    enable_lms = st.checkbox("Enable LMS calibration", value=False)
    lms_mu_log = st.slider("LMS step size mu (log10)",
                           -7.0, -2.0, -4.0, step=0.25)
    lms_mu = 10.0 ** lms_mu_log
    st.caption(f"mu = {lms_mu:.1e}")

    st.header("Noise sources")
    enable_dco_pn = st.checkbox("DCO phase noise", value=True)
    enable_ref_noise = st.checkbox("Reference jitter", value=True)
    bbpd_meta_ps = st.slider("BBPD metastability RMS [ps]",
                             0.0, 20.0, 0.0, step=0.1)
    ref_jit_fs = st.slider("Reference RMS jitter [fs]",
                           0.0, 1000.0, 80.0, step=5.0)

    st.header("View")
    view = st.radio("Plot type",
                    ["Lock transient",
                     "DTC cancellation",
                     "Phase noise",
                     "Fractional spurs",
                     "LMS calibration"],
                    index=2)

    if view == "Lock transient":
        df_init_mhz = st.slider("Initial DCO offset [MHz]",
                                -10.0, 10.0, 2.0, step=0.1)
    else:
        df_init_mhz = 0.0

    if view == "Phase noise":
        f_lo_int = st.number_input("Integration f_lo [kHz]",
                                   0.1, 10000.0, 1.0, step=0.5)
        f_hi_int = st.number_input("Integration f_hi [MHz]",
                                   0.1, 100.0, 20.0, step=1.0)
    else:
        f_lo_int = 1.0
        f_hi_int = 20.0


# -----------------------------------------------------------------------------
# Build parameters
# -----------------------------------------------------------------------------
f_ref = f_ref_mhz * 1e6
f_out = f_out_ghz * 1e9


def make_params(override_f_dco: float = None) -> PLLParams:
    p = PLLParams(
        f_ref=f_ref,
        f_out_target=f_out,
        f_dco_nominal=override_f_dco if override_f_dco is not None else f_out,
        K_dco=K_dco_khz * 1e3,
        dsm_order=int(dsm_order),
        bbpd_meta_noise_rms_s=bbpd_meta_ps * 1e-12,
        dtc_gain_err=float(dtc_gain_err),
        dtc_quant_lsb_s=dtc_lsb_ps * 1e-12,
        dtc_inl_amp_s=dtc_inl_amp_ps * 1e-12,
        dtc_inl_periods=int(dtc_inl_periods),
        Kp=float(Kp),
        Ki=float(Ki),
        ref_jitter_rms_s=ref_jit_fs * 1e-15,
        n_cycles=int(n_cycles),
        rng_seed=int(rng_seed),
        lms_mu=float(lms_mu),
    )
    return p


# Hashable signature so cache invalidates only when relevant inputs change
def _sig(p: PLLParams,
         enable_dtc: bool, enable_dco_pn: bool, enable_ref_noise: bool,
         enable_lms: bool, df_init_hz: float):
    return (p.f_ref, p.f_out_target, p.f_dco_nominal, p.K_dco,
            p.dsm_order, p.dsm_quant_levels,
            p.bbpd_meta_noise_rms_s,
            p.dtc_gain_err, p.dtc_offset_s, p.dtc_quant_lsb_s,
            p.dtc_inl_amp_s, p.dtc_inl_periods,
            p.Kp, p.Ki, p.u_init,
            p.ref_jitter_rms_s, p.n_cycles, p.rng_seed,
            p.lms_mu, p.lms_g_hat_init,
            tuple(p.dco_pn_freqs_hz), tuple(p.dco_pn_levels_dbchz),
            enable_dtc, enable_dco_pn, enable_ref_noise,
            enable_lms, df_init_hz)


@st.cache_data(show_spinner="Running closed-loop simulation...")
def cached_run(sig, _params: PLLParams,
               enable_dtc: bool, enable_dco_pn: bool,
               enable_ref_noise: bool, enable_lms: bool,
               df_init_hz: float):
    p = _params
    if df_init_hz != 0.0:
        p.f_dco_nominal = p.f_out_target - df_init_hz
    return run_simulation(p,
                          enable_dtc=enable_dtc,
                          enable_dco_pn=enable_dco_pn,
                          enable_ref_noise=enable_ref_noise,
                          enable_lms=enable_lms)


def _stamp(ax):
    ax.text(0.01, 0.02, "Behavioral approximation — not a silicon measurement",
            transform=ax.transAxes, fontsize=8, color="gray",
            alpha=0.85, va="bottom", ha="left")


# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------
def render_lock_transient():
    df_hz = df_init_mhz * 1e6
    p = make_params()
    res = cached_run(_sig(p, True, enable_dco_pn, enable_ref_noise,
                          enable_lms, df_hz),
                     p, True, enable_dco_pn, enable_ref_noise,
                     enable_lms, df_hz)
    t_us = np.arange(len(res.u)) * p.T_ref * 1e6
    df_dco = res.f_dco - p.f_out_target

    fig, axes = plt.subplots(3, 1, figsize=(9, 7.5), sharex=True)
    axes[0].plot(t_us, df_dco * 1e-3, lw=0.7)
    axes[0].set_ylabel("f_DCO − f_target [kHz]")
    axes[0].axhline(0, color="k", lw=0.4, ls="--")
    axes[0].grid(True, alpha=0.4)
    axes[0].set_title("Lock transient")

    axes[1].plot(t_us, res.u, lw=0.7)
    axes[1].set_ylabel("DCO tuning u [LSB]")
    axes[1].grid(True, alpha=0.4)

    axes[2].plot(t_us, res.e_bbpd * 1e12, lw=0.4)
    axes[2].set_ylabel("BBPD err [ps]")
    axes[2].set_xlabel("Time [us]")
    axes[2].grid(True, alpha=0.4)
    _stamp(axes[2])
    fig.tight_layout()
    st.pyplot(fig)

    tail = slice(int(0.8 * len(res.u)), None)
    cols = st.columns(3)
    cols[0].metric("Final df_DCO [kHz]",
                   f"{df_dco[tail].mean()*1e-3:+.2f}")
    cols[1].metric("Tail BBPD RMS [ps]",
                   f"{res.e_bbpd[tail].std()*1e12:.2f}")
    cols[2].metric("Final u [LSB]", f"{res.u[tail].mean():.1f}")


def render_dtc_cancellation():
    p = make_params()
    sig_on = _sig(p, True, enable_dco_pn, enable_ref_noise,
                  enable_lms, 0.0)
    sig_off = _sig(p, False, enable_dco_pn, enable_ref_noise,
                   enable_lms, 0.0)
    res_on = cached_run(sig_on, make_params(), True,
                        enable_dco_pn, enable_ref_noise,
                        enable_lms, 0.0)
    res_off = cached_run(sig_off, make_params(), False,
                         enable_dco_pn, enable_ref_noise,
                         enable_lms, 0.0)

    n = p.n_cycles
    trim = n // 2
    e_off = res_off.e_bbpd[trim:]
    e_on = res_on.e_bbpd[trim:]
    phi_off = 2 * np.pi * p.f_dco_nominal * (e_off - e_off.mean())
    phi_on = 2 * np.pi * p.f_dco_nominal * (e_on - e_on.mean())
    f_off, L_off = estimate_psd(phi_off, fs=p.f_ref)
    f_on, L_on = estimate_psd(phi_on, fs=p.f_ref)

    fig, axes = plt.subplots(3, 1, figsize=(9, 8))
    n_show = min(2000, len(e_off))
    t_us = np.arange(n_show) * p.T_ref * 1e6
    axes[0].plot(t_us, e_off[:n_show] * 1e12, lw=0.6, color="C3")
    axes[0].set_ylabel("BBPD err [ps]\n(DTC OFF)")
    axes[0].set_title("DTC cancellation of DSM-induced time error")
    axes[0].grid(True, alpha=0.4)
    axes[1].plot(t_us, e_on[:n_show] * 1e12, lw=0.6, color="C0")
    axes[1].set_ylabel("BBPD err [ps]\n(DTC ON)")
    axes[1].set_xlabel("Time [us]")
    axes[1].grid(True, alpha=0.4)

    mb = f_off > p.f_ref / len(phi_off)
    mg = f_on > p.f_ref / len(phi_on)
    axes[2].semilogx(f_off[mb], L_off[mb], lw=0.8, color="C3", label="DTC OFF")
    axes[2].semilogx(f_on[mg], L_on[mg], lw=0.8, color="C0", label="DTC ON")
    axes[2].set_xlabel("Offset frequency [Hz]")
    axes[2].set_ylabel("L(f) [dBc/Hz]")
    axes[2].grid(True, which="both", alpha=0.4)
    axes[2].legend()
    _stamp(axes[2])
    fig.tight_layout()
    st.pyplot(fig)

    cols = st.columns(2)
    cols[0].metric("BBPD RMS, DTC OFF", f"{e_off.std()*1e12:.1f} ps")
    cols[1].metric("BBPD RMS, DTC ON", f"{e_on.std()*1e12:.2f} ps")


def render_phase_noise():
    p = make_params()
    res = cached_run(_sig(p, True, enable_dco_pn, enable_ref_noise,
                          enable_lms, 0.0),
                     p, True, enable_dco_pn, enable_ref_noise,
                     enable_lms, 0.0)
    phi = excess_phase_at_dco(res, trim_settling=0.3)
    f, L = estimate_psd(phi, fs=p.f_ref,
                        nperseg=min(len(phi), 1 << 15))
    f_lo = f_lo_int * 1e3
    f_hi = f_hi_int * 1e6
    rms = integrated_rms_jitter_s(f, L, f_lo, f_hi, p.f_out_target)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    mask = f > p.f_ref / len(phi)
    ax.semilogx(f[mask], L[mask], lw=0.8, label="Closed-loop L(f)")
    L_open = np.interp(np.log10(np.clip(f, 1, None)),
                       np.log10(p.dco_pn_freqs_hz), p.dco_pn_levels_dbchz)
    ax.semilogx(f[mask], L_open[mask], "--", lw=0.7, color="gray",
                label="DCO open-loop template")
    ax.set_xlabel("Offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title("Closed-loop phase noise (behavioral approximation)")
    ax.grid(True, which="both", alpha=0.4)
    ax.legend()
    _stamp(ax)
    fig.tight_layout()
    st.pyplot(fig)

    cols = st.columns(3)
    cols[0].metric("Integrated jitter",
                   f"{rms*1e15:.0f} fs RMS")
    cols[1].metric("Band",
                   f"{f_lo_int:.1f} kHz .. {f_hi_int:.0f} MHz")
    cols[2].metric("Carrier", f"{p.f_out_target/1e9:.4f} GHz")


def render_fractional_spurs():
    p = make_params()
    res = cached_run(_sig(p, True, enable_dco_pn, enable_ref_noise,
                          enable_lms, 0.0),
                     p, True, enable_dco_pn, enable_ref_noise,
                     enable_lms, 0.0)
    phi = excess_phase_at_dco(res, trim_settling=0.3)
    f, L = estimate_psd(phi, fs=p.f_ref,
                        nperseg=min(len(phi), 1 << 15))
    spurs = detect_spurs(f, L, p.alpha, p.f_ref, n_harmonics=10)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    mask = f > p.f_ref / len(phi)
    ax.semilogx(f[mask], L[mask], lw=0.8)
    for s in spurs[:6]:
        ax.axvline(s["f_target"], color="C3", ls=":", lw=0.5, alpha=0.6)
        ax.annotate(f"k={s['k']}", xy=(s["f_peak"], s["L_dbchz"]),
                    fontsize=8, color="C3",
                    xytext=(0, 6), textcoords="offset points", ha="center")
    ax.set_xlabel("Offset frequency [Hz]")
    ax.set_ylabel("L(f) [dBc/Hz]")
    ax.set_title(f"Fractional spurs at alpha={p.alpha:.4f} "
                 f"(behavioral approximation)")
    ax.grid(True, which="both", alpha=0.4)
    _stamp(ax)
    fig.tight_layout()
    st.pyplot(fig)

    if spurs:
        import pandas as pd
        rows = [{"k": s["k"],
                 "f_target [kHz]": f"{s['f_target']/1e3:.2f}",
                 "f_peak [kHz]": f"{s['f_peak']/1e3:.2f}",
                 "L_dbchz": f"{s['L_dbchz']:.1f}"} for s in spurs]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="content")
    else:
        st.info("No spurs found — alpha is integer or out of band.")


def render_lms_calibration():
    p_on = make_params()
    p_off = make_params()
    sig_on = _sig(p_on, True, enable_dco_pn, enable_ref_noise, True, 0.0)
    sig_off = _sig(p_off, True, enable_dco_pn, enable_ref_noise, False, 0.0)
    res_on = cached_run(sig_on, make_params(), True,
                        enable_dco_pn, enable_ref_noise, True, 0.0)
    res_off = cached_run(sig_off, make_params(), True,
                         enable_dco_pn, enable_ref_noise, False, 0.0)

    n = p_on.n_cycles
    t_us = np.arange(n) * p_on.T_ref * 1e6
    target_g = 1.0 / (1.0 + p_on.dtc_gain_err) if (1 + p_on.dtc_gain_err) != 0 else 1.0

    phi_on = excess_phase_at_dco(res_on, trim_settling=0.7)
    phi_off = excess_phase_at_dco(res_off, trim_settling=0.5)
    f_on, L_on = estimate_psd(phi_on, fs=p_on.f_ref)
    f_off, L_off = estimate_psd(phi_off, fs=p_off.f_ref)

    fig, axes = plt.subplots(3, 1, figsize=(9, 9))
    axes[0].plot(t_us, res_on.g_hat, lw=0.8, label="LMS on")
    axes[0].plot(t_us, res_off.g_hat, lw=0.8, color="gray",
                 alpha=0.7, label="LMS off")
    axes[0].axhline(target_g, color="C2", ls="--", lw=0.8,
                    label=f"target 1/(1+gerr)={target_g:.3f}")
    axes[0].set_title("LMS DTC-gain calibration "
                      "(behavioral approximation)")
    axes[0].set_ylabel("g_hat")
    axes[0].set_xlabel("Time [us]")
    axes[0].grid(True, alpha=0.4)
    axes[0].legend(loc="best", fontsize=9)

    win = max(200, n // 200)
    import pandas as pd
    e_off_rms = pd.Series(res_off.e_bbpd ** 2).rolling(
        win, min_periods=win).mean().pow(0.5)
    e_on_rms = pd.Series(res_on.e_bbpd ** 2).rolling(
        win, min_periods=win).mean().pow(0.5)
    axes[1].semilogy(t_us, e_off_rms * 1e12, lw=0.8, color="C3", label="LMS off")
    axes[1].semilogy(t_us, e_on_rms * 1e12, lw=0.8, color="C0", label="LMS on")
    axes[1].set_ylabel("Rolling BBPD RMS [ps]")
    axes[1].set_xlabel("Time [us]")
    axes[1].grid(True, which="both", alpha=0.4)
    axes[1].legend()

    mo = f_off > p_off.f_ref / len(phi_off)
    mn = f_on > p_on.f_ref / len(phi_on)
    axes[2].semilogx(f_off[mo], L_off[mo], lw=0.8, color="C3",
                     label="Steady state, LMS off")
    axes[2].semilogx(f_on[mn], L_on[mn], lw=0.8, color="C0",
                     label="Steady state, LMS on")
    axes[2].set_xlabel("Offset frequency [Hz]")
    axes[2].set_ylabel("L(f) [dBc/Hz]")
    axes[2].grid(True, which="both", alpha=0.4)
    axes[2].legend()
    _stamp(axes[2])
    fig.tight_layout()
    st.pyplot(fig)

    cols = st.columns(4)
    cols[0].metric("Target g_hat", f"{target_g:.4f}")
    cols[1].metric("Final g_hat (LMS on)",
                   f"{res_on.g_hat[int(0.9*n):].mean():.4f}")
    cols[2].metric("BBPD RMS LMS off",
                   f"{res_off.e_bbpd[-10000:].std()*1e12:.1f} ps")
    cols[3].metric("BBPD RMS LMS on",
                   f"{res_on.e_bbpd[-10000:].std()*1e12:.2f} ps")
    if abs(p_on.dtc_gain_err) < 1e-6:
        st.info("DTC gain error is 0 — there is nothing for LMS to correct. "
                "Set a non-zero DTC gain error in the sidebar to see "
                "convergence.")


# -----------------------------------------------------------------------------
# Dispatch
# -----------------------------------------------------------------------------
view_fn = {
    "Lock transient": render_lock_transient,
    "DTC cancellation": render_dtc_cancellation,
    "Phase noise": render_phase_noise,
    "Fractional spurs": render_fractional_spurs,
    "LMS calibration": render_lms_calibration,
}[view]
view_fn()

st.divider()
with st.expander("Notes & limitations", expanded=False):
    st.markdown(
        "- All time errors in **seconds**; positive `e_bbpd` = feedback edge "
        "LATE relative to reference.\n"
        "- DCO phase-noise template values are **ESTIMATED** — the closed-loop "
        "spectrum here is illustrative.\n"
        "- LMS adaptive DTC gain calibration is implemented as a sign-sign "
        "update `g_hat -= mu * s_bbpd * e_dsm`; it converges to "
        "`1/(1+gain_err)`. Toggle in the sidebar and use the LMS view to see.\n"
        "- Simulator runs at one sample per reference cycle. Aliasing above "
        "`f_ref/2` is a fundamental limit of this behavioral model.")
