import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as s,g as n}from"./index-ooedyYhF.js";import{P as a}from"./PageLayout-D4DbgBvP.js";import{P as r}from"./PlotViewer-C2lcD2nR.js";import{C as i}from"./CodeBlock-BWBDLxNG.js";import{E as o,I as t}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const l=n("ext-ntf");function g(){return e.jsxs(a,{meta:l,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Why this page exists"}),e.jsx("p",{children:"A behavioral simulator is only trustworthy if its output can be explained by a closed-form model. We derive the small-signal noise-transfer functions for each injected noise source, evaluate them on the same frequency grid as the simulated PSD, and overlay. Agreement validates the model; disagreement flags either a derivation slip, a coding bug, or — in this case — a noise source the closed-form doesn't include."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Linearized model"}),e.jsx(o,{tex:String.raw`
            L(s) \;=\; \frac{K_{bb}\,K_{DCO}}{s\,f_{DCO,nom}}\,H_{LF}(s),
            \qquad
            H_{LF}(s) \;=\; K_p \;+\; \frac{K_i}{s\,T_{ref}}
          `,caption:"Open-loop gain in time-error domain, continuous-time approximation."}),e.jsxs("p",{children:["The BBPD's small-signal gain",e.jsx(t,{tex:"\\,K_{bb}=\\sqrt{2/\\pi}/\\sigma\\,"})," depends on the dither ",e.jsx(t,{tex:"\\sigma"})," at its input — itself a function of the closed-loop noise we're trying to model. The script measures ",e.jsx(t,{tex:"\\sigma"})," from the simulator trace and plugs it in, so the analytic prediction uses the right operating point."]}),e.jsx(o,{tex:String.raw`
            H_{ref}(s) = \frac{L(s)}{1+L(s)},\quad
            H_{dco}(s) = \frac{1}{1+L(s)},\quad
            H_{dtc}(s) = \frac{L(s)}{1+L(s)}
          `,caption:"Low-pass for any noise source entering at the comparator; high-pass for DCO intrinsic PN."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Inside the code — three contributions"}),e.jsxs("p",{children:["The whole calculation is plain complex-number arithmetic in",e.jsx("code",{children:" sim/noise_tf.py"}),". First, the open-loop gain and two basic NTFs:"]}),e.jsx(i,{language:"python",filename:"sim/noise_tf.py",lineRange:"28-48",startLine:28,code:`def open_loop_gain(f, K_bb, params):
    """L(s) at frequencies f (Hz). Returns complex array."""
    f = np.asarray(f, dtype=float)
    s = 2j * np.pi * np.maximum(f, 1e-9)
    H_LF = params.Kp + params.Ki / (s * params.T_ref)
    return K_bb * params.K_dco * H_LF / (s * params.f_dco_nominal)


def ntf_ref(f, K_bb, params):
    L = open_loop_gain(f, K_bb, params)
    return L / (1.0 + L)


def ntf_dco_pn(f, K_bb, params):
    L = open_loop_gain(f, K_bb, params)
    return 1.0 / (1.0 + L)`}),e.jsxs("p",{children:["Then three noise contributions added together: DCO open-loop PN through ",e.jsx(t,{tex:"|H_{dco}|^2"})," (high-pass), reference jitter through ",e.jsx(t,{tex:"|H_{ref}|^2"})," (low-pass), and the BBPD-folded quantization noise — also low-pass shaped:"]}),e.jsx(i,{language:"python",filename:"sim/noise_tf.py",lineRange:"86-99",startLine:86,code:`# BBPD-folded quantization noise. The detector output has variance
# ~1 (it's ±1 with E[s] = K_bb*e ≈ 0 at lock), spread over the
# one-sided sampling bandwidth f_ref/2. Input-referred PSD in
# seconds^2/Hz is therefore (2 / f_ref) / K_bb^2.
if include_bbpd_noise and K_bb > 0 and np.isfinite(K_bb):
    S_t_bbpd_one = 2.0 / (K_bb ** 2 * f_ref)
    S_phi_bbpd_in = ((2.0 * np.pi * params.f_dco_nominal) ** 2
                     * S_t_bbpd_one)
    S_phi_closed_bbpd = np.abs(H_ref) ** 2 * S_phi_bbpd_in
else:
    S_phi_closed_bbpd = np.zeros_like(f)

S_phi_total = S_phi_closed_dco + S_phi_closed_ref + S_phi_closed_bbpd`}),e.jsxs("p",{children:["The BBPD term is the one that closes the gap with the simulated PSD. Without it, the analytic prediction sits well below the actual noise floor — because in a real BBPD-DPLL the in-band floor is dominated by the comparator's 1-bit quantization, not by DCO or reference noise. The standard model treats the ±1 output as having unit variance spread over the sampling bandwidth, divided by ",e.jsx(t,{tex:"K_{bb}^2"}),"to refer it to the input."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Comparison plot"}),e.jsx(r,{src:"/figures/noise_tf.png",alt:"Top: simulated L(f) vs. analytic closed-loop prediction with BBPD noise included. Bottom: |H_ref| (low-pass) and |H_dco_pn| (high-pass) magnitudes.",caption:"With the BBPD noise term added, the analytic prediction tracks the simulated floor across the band."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"How to read the comparison"}),e.jsx("p",{children:"Three things to look for:"}),e.jsxs("ul",{className:"ml-6 list-disc space-y-2 text-slate-700",children:[e.jsxs("li",{children:[e.jsx("strong",{children:"The crossover."})," The green dotted line marks",e.jsx(t,{tex:"\\,|L(j\\omega)|=1\\,"}),". Below it, the loop has authority — DCO PN is suppressed, reference jitter passes. Above it, the loop has no authority — DCO PN reaches the output unchanged, reference jitter is rejected."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"The high-pass / low-pass roll-offs in the bottom panel."})," Slopes around the crossover are set by the zero of the PI filter, not by ",e.jsx(t,{tex:"K_{bb}"}),". Drop Kp and the slope stays the same; only the crossover moves."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"In-band floor."})," The flat in-band level is set by the BBPD term. Increasing",e.jsx(t,{tex:"\\,K_{bb}\\,"})," (smaller in-loop dither) pulls the floor down by 20 dB per decade of ",e.jsx(t,{tex:"K_{bb}"}),", so anything that reduces the dither — better DCO, better ref clock, tighter DTC calibration — directly improves the in-band PN."]})]})]}),e.jsxs(s,{kind:"info",title:"What this confirms",children:["Three independent quantities (DCO PN, reference jitter, BBPD quantization variance) sum to within a few dB of the simulated PSD across the whole band. The crossover and slopes are set only by the loop filter and ",e.jsx(t,{tex:"K_{bb}"}),". The simulator's loop dynamics are wired correctly."]}),e.jsxs(s,{kind:"limit",title:"What the analytic model still misses",children:["Continuous-time approximation breaks down near",e.jsx(t,{tex:"\\,f_{ref}/2\\,"}),": aliased contributions, DSM residue leakage past imperfect DTC cancellation, and any non-stationary effects during the lock transient are still outside this closed-form prediction. The remaining ~2 dB at very high offsets is consistent with the first of these."]})]})}export{g as default};
//# sourceMappingURL=ExtNtf-Bfv_HROY.js.map
