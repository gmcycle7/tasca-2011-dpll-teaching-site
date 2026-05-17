import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as r,g as a}from"./index-ooedyYhF.js";import{P as s}from"./PageLayout-D4DbgBvP.js";import{C as i}from"./CodeBlock-BWBDLxNG.js";import{I as t,E as n}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const o=a("mod-jitter-spurs");function g(){return e.jsxs(s,{meta:o,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Two small files, one job each"}),e.jsxs("p",{children:[e.jsx("code",{children:"sim/jitter.py"})," integrates",e.jsx(t,{tex:"\\,\\mathcal{L}(f)\\,"})," into RMS time jitter.",e.jsx("code",{children:" sim/spurs.py "})," locates the predicted fractional-spur comb in a measured PSD. Each is short enough to read whole."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"jitter.py — band-limited integration"}),e.jsx(i,{language:"python",filename:"sim/jitter.py",lineRange:"9-26",startLine:9,code:`def integrated_phase_variance(f, L_dbchz, f_lo, f_hi) -> float:
    f = np.asarray(f, float)
    L_dbchz = np.asarray(L_dbchz, float)
    m = (f >= f_lo) & (f <= f_hi) & np.isfinite(L_dbchz)
    if m.sum() < 2:
        return float("nan")
    L_lin = 10.0 ** (L_dbchz[m] / 10.0)
    # numpy>=2.0 renamed trapz -> trapezoid
    trapezoid = getattr(np, "trapezoid", None) or np.trapz
    return float(2.0 * trapezoid(L_lin, f[m]))

def integrated_rms_jitter_s(f, L_dbchz, f_lo, f_hi, f_carrier) -> float:
    var_phi = integrated_phase_variance(f, L_dbchz, f_lo, f_hi)
    if not np.isfinite(var_phi) or var_phi < 0:
        return float("nan")
    return float(np.sqrt(var_phi) / (2.0 * np.pi * f_carrier))`}),e.jsxs("p",{children:[e.jsx("strong",{children:"The two-step structure (variance, then jitter) is on purpose."}),` "Total integrated phase variance over a band" is itself a useful quantity (used for SNR calculations), so we expose it. The jitter-in-seconds is just the variance divided by the carrier's rad-to-second conversion.`]}),e.jsx(n,{tex:String.raw`
            \sigma_t \;=\; \frac{\sqrt{\,2\!\int_{f_{lo}}^{f_{hi}}\!\mathcal{L}(f)\,df\,}}{2\pi\,f_{out}}
          `}),e.jsxs("p",{children:['The factor of 2 inside the square root is the "both sidebands" correction — phase noise integrates over both positive and negative offset frequencies, and',e.jsx(t,{tex:"\\,\\mathcal{L}(f)\\,"})," is single-sideband."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"spurs.py — predicting + locating"}),e.jsx(i,{language:"python",filename:"sim/spurs.py",lineRange:"15-22",startLine:15,code:`def predicted_spur_offsets(alpha, f_ref, n_harmonics=12):
    out = []
    for k in range(1, n_harmonics + 1):
        f = ((k * alpha) % 1.0) * f_ref
        if f > 0:
            out.append((k, f))
    return out`}),e.jsx(i,{language:"python",filename:"sim/spurs.py",lineRange:"25-47",startLine:25,code:`def detect_spurs(f, L_dbchz, alpha, f_ref,
                 n_harmonics=12, search_window_bins=4):
    """Return list of dicts {k, f_target, f_peak, L_dbchz}."""
    f = np.asarray(f)
    L = np.asarray(L_dbchz)
    results = []
    for k, f_target in predicted_spur_offsets(alpha, f_ref, n_harmonics):
        if f_target >= f[-1] or f_target <= f[0]:
            continue
        i0 = int(np.argmin(np.abs(f - f_target)))
        lo = max(i0 - search_window_bins, 0)
        hi = min(i0 + search_window_bins, len(f) - 1)
        i_peak = lo + int(np.argmax(L[lo:hi + 1]))
        results.append({
            "k": k,
            "f_target": float(f_target),
            "f_peak": float(f[i_peak]),
            "L_dbchz": float(L[i_peak]),
        })
    return results`})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Why predict first, then search around the prediction"}),e.jsxs("p",{children:['A naive "find peaks" pass on a noisy PSD returns dozens of false positives. By predicting where fractional spurs ',e.jsx("em",{children:"must"})," be (at multiples of",e.jsx(t,{tex:"\\,\\alpha f_{ref}\\,"})," mod",e.jsx(t,{tex:"\\,f_{ref}\\,"}),") and then searching a few bins around each prediction, we get a structured table that maps 1-to-1 with the physical comb. The Welch resolution bandwidth can place the actual peak in a neighboring bin, so we widen the search to ",e.jsx("code",{children:"search_window_bins=4"}),"."]})]}),e.jsxs(r,{kind:"info",children:["The local-max windowing means we always return ",e.jsx("em",{children:"something"}),'at every predicted offset. When the comb is hidden in noise, the reported "spur level" is just the noise floor at that offset — which is the right answer, just not a real spur.']})]})}export{g as default};
//# sourceMappingURL=ModJitterSpurs-DKv251lW.js.map
