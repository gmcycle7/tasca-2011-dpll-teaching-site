import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as i,g as r}from"./index-ooedyYhF.js";import{P as t}from"./PageLayout-D4DbgBvP.js";import{C as n}from"./CodeBlock-BWBDLxNG.js";import{I as s,E as a}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const o=r("mod-phase-noise");function u(){return e.jsxs(t,{meta:o,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Purpose"}),e.jsxs("p",{children:["Two responsibilities, both around the IEEE Std 1139 definition of ",e.jsx(s,{tex:"\\mathcal{L}(f)"}),":"]}),e.jsxs("ul",{className:"ml-6 list-disc text-slate-700",children:[e.jsxs("li",{children:[e.jsx("strong",{children:"Generate"})," a colored phase-noise sequence whose PSD matches a target template specified at corner frequencies."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"Estimate"})," ",e.jsx(s,{tex:"\\mathcal{L}(f)"})," from a sampled excess-phase sequence via Welch."]})]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Generation: from L(f) corners to a time-domain sequence"}),e.jsx(n,{language:"python",filename:"sim/phase_noise.py",lineRange:"18-39",startLine:18,code:`def generate_pn_sequence(n_samples, fs, freqs_hz, levels_dbchz, rng=None):
    """Generate phi_n[k] in rad with the target L(f) at sample rate fs."""
    if rng is None:
        rng = np.random.default_rng(0)
    freqs = np.asarray(freqs_hz, dtype=float)
    levels = np.asarray(levels_dbchz, dtype=float)

    f = np.fft.rfftfreq(n_samples, d=1.0 / fs)
    log_f = np.log10(np.clip(f, 1.0, None))
    L_db = np.interp(log_f, np.log10(freqs), levels,
                     left=levels[0], right=levels[-1])
    # S_phi (one-sided) = 2 * 10^(L/10)  [rad^2/Hz]
    S_phi = 2.0 * 10.0 ** (L_db / 10.0)
    S_phi[0] = 0.0

    # IRFFT amplitudes for a real signal with PSD S_phi
    amps = np.sqrt(S_phi * n_samples * fs / 2.0)
    phases = rng.uniform(0.0, 2.0 * np.pi, len(f))
    X = amps * np.exp(1j * phases)
    X[0] = 0.0
    if n_samples % 2 == 0:
        X[-1] = X[-1].real
    return np.fft.irfft(X, n=n_samples)`})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Why frequency-domain synthesis (and not filtered white noise)"}),e.jsx("p",{children:"Three reasons in order of importance:"}),e.jsxs("ul",{className:"ml-6 list-disc space-y-2 text-slate-700",children:[e.jsxs("li",{children:[e.jsx("strong",{children:"You specify L(f) directly."})," No FIR/IIR design step, no filter-order vs. accuracy trade-off, no filter transient settling. The corner-point list is exactly the shape you get."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"One pass, reproducible."})," Same seed → same sequence. Useful for regression testing."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"Trivial Parseval check."})," Integrating",e.jsx(s,{tex:"\\,\\mathcal{L}(f)\\,"})," of the generated sequence gives back the user-specified phase variance to within sampling precision."]})]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"The amplitude formula in one line"}),e.jsx(a,{tex:String.raw`
            |X[k]| \;=\; \sqrt{S_\phi^{(1)}(f_k)\,\frac{N\,f_s}{2}}
          `,caption:"Each rfft bin's magnitude that gives the right Parseval power."}),e.jsxs("p",{children:["For a real signal of length ",e.jsx(s,{tex:"N"})," with sample rate",e.jsx(s,{tex:"f_s"})," and target one-sided PSD",e.jsx(s,{tex:"S_\\phi^{(1)}(f)"}),", this is what each rfft bin must hold. Drop the factor 2 and you're off by 3 dB everywhere."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Estimation: Welch back into L(f)"}),e.jsx(n,{language:"python",filename:"sim/phase_noise.py",lineRange:"42-57",startLine:42,code:`def estimate_psd(phi_excess_rad, fs, nperseg=None, window="hann"):
    """Return (f, L_dbchz) using Welch on the excess-phase sequence."""
    n = len(phi_excess_rad)
    if nperseg is None:
        nperseg = min(n, 1 << 14)
    f, Pxx = signal.welch(phi_excess_rad, fs=fs, nperseg=nperseg,
                          window=window, scaling="density",
                          return_onesided=True, detrend="constant")
    # Pxx is the one-sided PSD in rad^2/Hz; L(f) = S_phi_onesided / 2.
    with np.errstate(divide="ignore"):
        L = 10.0 * np.log10(np.maximum(Pxx / 2.0, 1e-300))
    return f, L`}),e.jsxs("p",{children:[e.jsxs("strong",{children:["Why ",e.jsx("code",{children:"Pxx / 2"}),"?"]})," ",e.jsx("code",{children:"scipy.signal.welch"}),"with ",e.jsx("code",{children:"return_onesided=True"})," already returns the one-sided PSD. The IEEE 1139 convention is",e.jsx(s,{tex:"\\;\\mathcal{L}(f)=S_\\phi^{(1)}(f)/2\\;"}),', so dividing by 2 converts "total phase noise per Hz" into "single-sideband phase noise per Hz". This conversion is the most common 3-dB error in PLL simulators; we centralize it here so it only happens once.']})]}),e.jsxs(i,{kind:"warn",children:["The DCO PN corner-point template used by default is",e.jsx("strong",{children:" ESTIMATED"}),", not extracted from the paper. The integrated jitter our sim reports is a sanity check on the pipeline, not a chip-matched number."]})]})}export{u as default};
//# sourceMappingURL=ModPhaseNoise-BhtyLfEV.js.map
