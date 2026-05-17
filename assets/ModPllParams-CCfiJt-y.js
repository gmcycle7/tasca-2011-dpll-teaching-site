import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as i,g as a}from"./index-ooedyYhF.js";import{P as s}from"./PageLayout-D4DbgBvP.js";import{C as t}from"./CodeBlock-BWBDLxNG.js";import{I as n}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const r=a("mod-pll-params");function g(){return e.jsxs(s,{meta:r,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Purpose"}),e.jsxs("p",{children:["One file, one dataclass, every knob the simulator exposes plus a handful of derived properties. Everything else in",e.jsx("code",{children:" sim/ "})," reads from a ",e.jsx("code",{children:"PLLParams"})," instance, which makes alternative configurations a one-liner."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Header and convention"}),e.jsx(t,{language:"python",filename:"sim/pll_params.py",lineRange:"1-13",startLine:1,code:`"""Top-level PLLParams dataclass holding every behavioral parameter.

Convention (used consistently across the simulator):
    * Time error is in SECONDS.
    * Positive time error = feedback (DTC-delayed divider) edge LATE
      relative to the reference edge.
    * BBPD output is +1 when feedback is late, -1 when feedback is early.
    * DCO tuning word \`u\` is dimensionless; f_DCO = f_dco_nominal + K_dco*u.
"""
from dataclasses import dataclass`}),e.jsxs("p",{children:[e.jsx("strong",{children:"Why a docstring this opinionated?"})," The single most common bug in a PLL simulator is a sign-convention flip — the loop pulls in the wrong direction and saturates silently. By writing the convention at the top of the parameter file we give every later file a single source of truth to point at."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"The dataclass body"}),e.jsx(t,{language:"python",filename:"sim/pll_params.py",lineRange:"16-47",startLine:16,code:`@dataclass
class PLLParams:
    # ----- Reference clock -----
    f_ref: float = 40e6                  # Hz; PAPER (to confirm in PDF)
    ref_jitter_rms_s: float = 80e-15     # ESTIMATED crystal-class

    # ----- Output carrier / DCO nominal -----
    # Default chosen fractional so alpha != 0 exercises the DSM/DTC path.
    f_out_target: float = 3.605e9        # within 2.9-4.0 GHz; PAPER range
    f_dco_nominal: float = 3.605e9       # initial nominal frequency
    K_dco: float = 10e3                  # Hz / LSB; ESTIMATED

    # ----- DSM (MASH 1-1-1) -----
    dsm_order: int = 3                   # 1, 2, or 3
    dsm_quant_levels: int = 1 << 24      # ESTIMATED 24-bit accumulator

    # ----- BBPD -----
    bbpd_meta_noise_rms_s: float = 0.0   # s; optional decision noise

    # ----- DTC -----
    dtc_gain_err: float = 0.0            # relative; 0 = ideal
    dtc_offset_s: float = 0.0            # s
    dtc_quant_lsb_s: float = 1e-12       # s; ESTIMATED 1 ps LSB
    dtc_inl_amp_s: float = 0.0           # s; sinusoidal-INL amplitude
    dtc_inl_periods: int = 4             # ripple periods over full scale

    # ----- Digital loop filter (PI) -----
    Kp: float = 8.0
    Ki: float = 0.5
    u_init: float = 0.0                  # initial DCO tuning word`}),e.jsx("p",{children:"Three design decisions worth flagging:"}),e.jsxs("ul",{className:"ml-6 list-disc space-y-2 text-slate-700",children:[e.jsxs("li",{children:[e.jsx("strong",{children:"Default fractional carrier 3.605 GHz."})," 3.6 GHz would divide 40 MHz exactly into 90 — α = 0, the DSM emits a constant, the DTC has nothing to cancel. 3.605 gives α = 0.125 so every fractional-N path is exercised by default."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"K_dco = 10 kHz/LSB is intentionally coarser than the paper's 70 Hz."})," The real chip combines a coarse capacitor bank with a high-resolution dithered fine branch to land on 70 Hz; modeling that mix is a separate piece of work. 10 kHz/LSB keeps the integer tuning word",e.jsx(n,{tex:"\\,u\\,"})," small while exercising loop dynamics faithfully."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"BBPD metastability noise defaults to 0."})," Real flip-flops add Gaussian dither in their setup/hold window; we leave it off so the default sim is deterministic, and turn it on via the slider in the GUI when teaching BBPD K_bb behavior."]})]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"LMS calibration knobs"}),e.jsx(t,{language:"python",filename:"sim/pll_params.py",lineRange:"49-56",startLine:49,code:`    # ----- LMS adaptive DTC gain calibration -----
    # When enabled in run_simulation, the digital-side DTC drive is scaled
    # by an adaptive coefficient g_hat updated as
    #   g_hat[k+1] = g_hat[k] - mu * s_bbpd[k] * e_dsm[k]
    # which drives g_hat toward 1/(1 + dtc_gain_err) to null the residual
    # correlation between BBPD output and DSM residue.
    lms_mu: float = 1e-4                 # ESTIMATED; demo-friendly step
    lms_g_hat_init: float = 1.0          # start from "I think the gain is right"`}),e.jsxs("p",{children:["The comment block documents the convergence target so future readers don't have to derive it again. ",e.jsx("code",{children:"μ = 1e-4"}),"gives full convergence inside ~50 µs with a 10% gain error — fast enough for a demo, slow enough that steady-state misadjustment is invisible in the PSD."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Derived properties"}),e.jsx(t,{language:"python",filename:"sim/pll_params.py",lineRange:"66-86",startLine:66,code:`    @property
    def T_ref(self) -> float:
        return 1.0 / self.f_ref

    @property
    def T_dco_nominal(self) -> float:
        return 1.0 / self.f_dco_nominal

    @property
    def N_frac(self) -> float:
        return self.f_out_target / self.f_ref

    @property
    def alpha(self) -> float:
        n = self.N_frac
        return n - int(n)

    @property
    def N_int(self) -> int:
        return int(self.N_frac)`}),e.jsxs("p",{children:[e.jsxs("strong",{children:["Why ",e.jsx("code",{children:"@property"})," instead of pre-computed attributes?"]})," A common bug pattern is to set",e.jsx("code",{children:"self.alpha"})," at ",e.jsx("code",{children:"__init__"})," and then forget to recompute it when the caller mutates ",e.jsx("code",{children:"f_out_target"}),"mid-script. Properties guarantee consistency at zero performance cost — Python caches dataclass fields anyway, and these properties are evaluated only when a caller asks."]})]}),e.jsxs(i,{kind:"info",children:["Every ",e.jsx("code",{children:"ESTIMATED"})," field is documented row-by-row in",e.jsx("code",{children:" docs/assumptions.md "}),". If you find a paper-stated number that differs from a default here, update both at once."]})]})}export{g as default};
//# sourceMappingURL=ModPllParams-CCfiJt-y.js.map
