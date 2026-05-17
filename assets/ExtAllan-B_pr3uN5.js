import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as a,g as s}from"./index-ooedyYhF.js";import{P as i}from"./PageLayout-D4DbgBvP.js";import{P as r}from"./PlotViewer-C2lcD2nR.js";import{C as n}from"./CodeBlock-BWBDLxNG.js";import{I as t,E as o}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const l=s("ext-allan");function g(){return e.jsxs(i,{meta:l,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Allan deviation — what does it tell you?"}),e.jsxs("p",{children:["L(f) reports the carrier's spectrum; Allan deviation",e.jsx(t,{tex:"\\,\\sigma_y(\\tau)\\,"})," reports its stability over time. The same closed-loop output, plotted two different ways. ADEV is what oscillator data sheets, OCXO suppliers and GNSS designers actually quote, because the slope of",e.jsx(t,{tex:"\\,\\sigma_y(\\tau)\\,"})," directly identifies the dominant noise mechanism at each averaging time τ."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Overlapping ADEV from divider-edge timestamps"}),e.jsx(o,{tex:String.raw`
            \sigma_y^2(\tau) \;=\; \frac{1}{2(N{-}2m)\,\tau^2}\,
              \sum_{i=0}^{N-2m-1}\bigl(x_{i+2m} - 2 x_{i+m} + x_i\bigr)^2
          `,caption:"x[k] is the cumulative phase; τ = m·τ₀ with τ₀ = T_ref."}),e.jsxs("p",{children:["The simulator already emits ",e.jsx("code",{children:"t_div_eff[k]"})," for every reference cycle, so the natural input to",e.jsx(t,{tex:"\\,\\sigma_y(\\tau)\\,"})," is just"," ",e.jsx("code",{children:"np.diff(t_div_eff) / T_ref"})," — fractional frequency per cycle."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Inside the code"}),e.jsx(n,{language:"python",filename:"sim/allan.py",lineRange:"22-52",startLine:22,code:`def fractional_frequency_from_edges(t_edges_s, t_nominal_s):
    t = np.asarray(t_edges_s, dtype=float)
    T = np.diff(t)
    return (T - t_nominal_s) / t_nominal_s


def overlapping_adev(y, tau0_s, m_values=None):
    N = y.size
    x = np.concatenate(([0.0], np.cumsum(y) * tau0_s))   # phase samples
    if m_values is None:
        m_values = np.unique(np.round(
            np.geomspace(1, max(2, N // 4), 30)).astype(int))
    tau_arr, adev_arr = [], []
    for m in m_values:
        if m < 1 or 2 * m >= N: continue
        d = x[2 * m:] - 2 * x[m:-m] + x[: -2 * m]
        var = np.mean(d ** 2) / (2.0 * (m * tau0_s) ** 2)
        tau_arr.append(m * tau0_s)
        adev_arr.append(float(np.sqrt(var)))
    return np.asarray(tau_arr), np.asarray(adev_arr)`}),e.jsxs("p",{children:["Why ",e.jsx("em",{children:"overlapping"})," ADEV instead of non-overlapping? For the same data length you get many more samples per τ, so the estimate has tighter confidence — exactly what we want for short simulator runs."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Reading the slope"}),e.jsx("p",{children:"The classical noise-type slopes:"}),e.jsxs("ul",{className:"ml-6 list-disc space-y-1 text-slate-700 dark:text-slate-300",children:[e.jsxs("li",{children:["White phase modulation (PM)  ⇒ ",e.jsx(t,{tex:"\\,\\sigma_y \\propto \\tau^{-1}\\,."})]}),e.jsxs("li",{children:["White frequency modulation (FM)  ⇒ ",e.jsx(t,{tex:"\\,\\sigma_y \\propto \\tau^{-1/2}\\,."})]}),e.jsxs("li",{children:["Flicker FM  ⇒ ",e.jsx(t,{tex:"\\,\\sigma_y \\propto \\tau^{0}\\,."})]}),e.jsxs("li",{children:["Random-walk FM  ⇒ ",e.jsx(t,{tex:"\\,\\sigma_y \\propto \\tau^{+1/2}\\,."})]})]}),e.jsx("p",{children:"The plot below overlays these slope guides so you can read off the noise type that dominates at each τ."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Result"}),e.jsx(r,{src:"/figures/allan.png",alt:"Three panels: ADEV, ADEV with slope guides, and ADEV for three loop bandwidths.",caption:"Minimum ADEV ~ 8e-10 around τ ≈ 1 ms in our default setup. Larger loop BW pushes the white-FM region farther right (loop attenuates the DCO PN earlier in τ)."})]}),e.jsx(a,{kind:"info",children:"Allan deviation lives in the time domain — it's the natural complement to L(f). If you ever need to compare with an oscillator data sheet or with a GNSS-time-transfer paper, this is the metric they will quote."})]})}export{g as default};
//# sourceMappingURL=ExtAllan-B_pr3uN5.js.map
