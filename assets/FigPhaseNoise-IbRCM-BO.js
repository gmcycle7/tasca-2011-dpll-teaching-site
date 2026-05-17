import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as s,f as a}from"./index-ooedyYhF.js";import{P as o}from"./PageLayout-D4DbgBvP.js";import{E as t,I as i}from"./EquationBlock-DRbDSHwX.js";import{P as d}from"./PlotViewer-C2lcD2nR.js";import{C as r}from"./CodeBlock-BWBDLxNG.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const h=a.find(n=>n.slug==="fig-phase-noise");function v(){return e.jsxs(o,{meta:h,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"From time error to L(f)"}),e.jsx("p",{children:"The simulator works in the time-error domain. At every reference cycle we record the post-DTC divider edge time relative to its ideal grid position:"}),e.jsx(t,{tex:String.raw`
            \delta[k] \;=\; t_{div,eff}[k] \;-\; (k+1)\,T_{ref}
          `,caption:"Sampled at f_ref; we trim the lock transient and zero-mean."}),e.jsx("p",{children:"Time jitter at the divider output equals time jitter at the DCO output (the divider does not change time jitter), so the DCO-referred excess phase is"}),e.jsx(t,{tex:String.raw`
            \phi_n[k] \;=\; 2\pi\,f_{DCO,nom}\,\delta[k]
          `}),e.jsx("p",{children:"and the single-sideband phase-noise spectrum follows from Welch's PSD estimate of that sequence, with the IEEE Std 1139 factor:"}),e.jsx(t,{tex:String.raw`
            \mathcal{L}(f) \;=\; \tfrac{1}{2}\,S_{\phi}^{(1\text{-sided})}(f)
            \;\;\Big[\,\frac{\mathrm{rad}^2}{\mathrm{Hz}}\,\Big]
            \;\to\;\mathrm{dBc/Hz}.
          `})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Integrating RMS jitter"}),e.jsxs("p",{children:["Once ",e.jsx(i,{tex:"\\mathcal{L}(f)"})," is in hand, integrated phase variance and time jitter are"]}),e.jsx(t,{tex:String.raw`
            \sigma_\phi^2 \;=\; 2\int_{f_{lo}}^{f_{hi}}\!\mathcal{L}(f)\,df,
            \qquad
            \sigma_t \;=\; \frac{\sigma_\phi}{2\pi\,f_{out}}.
          `}),e.jsxs("p",{children:["The paper integrates from 3 kHz to 30 MHz. Our simulator only gives us PSD up to ",e.jsx(i,{tex:"f_{ref}/2 = 20\\,\\mathrm{MHz}"}),", so the strict comparison is 3 kHz – 20 MHz."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Closed-loop spectrum"}),e.jsx(d,{src:"/figures/phase_noise.png",alt:"Closed-loop L(f) and the DCO open-loop template, log-log.",caption:"Inside the loop bandwidth, ref + BBPD noise dominate; outside, the DCO template takes over."}),e.jsx("p",{children:'The dashed line is the "open-loop" DCO PN template we assumed; the solid line is what the simulator produces after closing the loop. They agree at high offsets (loop has no authority) and diverge below the loop bandwidth (loop suppresses DCO PN, replaces it with ref + BBPD noise).'})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Where the integrated number lands"}),e.jsxs("p",{children:["With our default DCO PN template, the integrator returns ≈ 500 fs RMS over 3 kHz – 20 MHz. The paper reports 560 fs RMS over 3 kHz – 30 MHz. Treat the agreement as a sanity check that our PSD and integration pipelines are wired correctly; it is ",e.jsx("strong",{children:"not"}),"evidence that the model matches the chip."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Inside the code — PSD pipeline in three calls"}),e.jsxs("p",{children:["Step 1: turn the simulator's time-domain divider edges into an excess-phase sequence sampled at ",e.jsx(i,{tex:"f_{ref}"}),"."]}),e.jsx(r,{language:"python",filename:"sim/pll_model.py",lineRange:"61-78",startLine:61,code:`def excess_phase_at_dco(res, trim_settling=0.5):
    """Return DCO-equivalent excess phase (rad) sampled at f_ref.

    delta[k]            = t_div_eff[k] - (k+1)*T_ref
    phi_dco_excess[k]   = 2*pi * f_dco_nominal * delta[k]
    """
    p = res.params
    n = len(res.t_div_eff)
    delta = res.t_div_eff - (np.arange(n) + 1) * p.T_ref
    i0 = int(trim_settling * n)
    delta = delta[i0:]
    delta = delta - np.mean(delta)
    return 2.0 * np.pi * p.f_dco_nominal * delta`}),e.jsx("p",{children:"Step 2: Welch PSD, then convert to single-sideband phase noise in dBc/Hz with the IEEE 1139 factor."}),e.jsx(r,{language:"python",filename:"sim/phase_noise.py",lineRange:"42-55",startLine:42,code:`def estimate_psd(phi_excess_rad, fs, nperseg=None, window="hann"):
    n = len(phi_excess_rad)
    if nperseg is None:
        nperseg = min(n, 1 << 14)
    f, Pxx = signal.welch(phi_excess_rad, fs=fs, nperseg=nperseg,
                          window=window, scaling="density",
                          return_onesided=True, detrend="constant")
    # Pxx is the one-sided PSD in rad^2/Hz; L(f) = S_phi_onesided / 2.
    with np.errstate(divide="ignore"):
        L = 10.0 * np.log10(np.maximum(Pxx / 2.0, 1e-300))
    return f, L`}),e.jsxs("p",{children:["Step 3: integrate ",e.jsx(i,{tex:"\\mathcal{L}(f)"})," over the required band and convert to RMS time jitter."]}),e.jsx(r,{language:"python",filename:"sim/jitter.py",lineRange:"10-26",startLine:10,code:`def integrated_phase_variance(f, L_dbchz, f_lo, f_hi) -> float:
    m = (f >= f_lo) & (f <= f_hi) & np.isfinite(L_dbchz)
    if m.sum() < 2:
        return float("nan")
    L_lin = 10.0 ** (L_dbchz[m] / 10.0)
    trapezoid = getattr(np, "trapezoid", None) or np.trapz
    return float(2.0 * trapezoid(L_lin, f[m]))

def integrated_rms_jitter_s(f, L_dbchz, f_lo, f_hi, f_carrier) -> float:
    var_phi = integrated_phase_variance(f, L_dbchz, f_lo, f_hi)
    if not np.isfinite(var_phi) or var_phi < 0:
        return float("nan")
    return float(np.sqrt(var_phi) / (2.0 * np.pi * f_carrier))`}),e.jsxs("p",{children:["The ",e.jsx("code",{children:"* 2.0"}),' in line 17 is the "two sidebands" correction; the ',e.jsx("code",{children:"/ (2π·f_carrier)"}),"in the final line converts radians-squared into seconds."]})]}),e.jsxs(s,{kind:"warn",children:["The DCO phase-noise template values (corner-point dBc/Hz numbers in",e.jsx("code",{children:" sim/pll_params.py "}),") are all ",e.jsx("strong",{children:"ESTIMATED"}),"— picked to give a credible LC-DCO shape at this carrier and power. They are not extracted from the paper."]})]})}export{v as default};
//# sourceMappingURL=FigPhaseNoise-IbRCM-BO.js.map
