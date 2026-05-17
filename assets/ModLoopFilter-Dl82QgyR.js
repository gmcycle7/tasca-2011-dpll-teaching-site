import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as i,g as s}from"./index-ooedyYhF.js";import{P as o}from"./PageLayout-D4DbgBvP.js";import{C as a}from"./CodeBlock-BWBDLxNG.js";import{E as n,I as t}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const r=s("mod-loop-filter");function g(){return e.jsxs(o,{meta:r,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Purpose"}),e.jsx("p",{children:"Convert the BBPD's ±1 sequence into a DCO tuning word with a discrete-time proportional-integral law. PI is the textbook choice for Type-II loop response: infinite DC gain (zero steady-state phase error) plus a high-frequency zero for phase margin."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"The whole file"}),e.jsx(a,{language:"python",filename:"sim/loop_filter.py",lineRange:"1-24",startLine:1,code:`"""Digital PI loop filter.

Input  : BBPD output s[k] in {-1, +1} (or any small integer).
Output : DCO tuning word u[k] = u_init + Kp*s[k] + Ki*sum(s).

The integral accumulator is updated before the output, so the filter
is causal and has unity-delay-free path from input to output.
"""

class DigitalPI:
    def __init__(self, Kp: float, Ki: float, u_init: float = 0.0):
        self.Kp = float(Kp)
        self.Ki = float(Ki)
        self.u_init = float(u_init)
        self.integ = 0.0

    def reset(self, u_init: float = None):
        self.integ = 0.0
        if u_init is not None:
            self.u_init = float(u_init)

    def step(self, s_k: float) -> float:
        self.integ += s_k
        return self.u_init + self.Kp * s_k + self.Ki * self.integ`})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Transfer function"}),e.jsx(n,{tex:String.raw`
            H_{LF}(z) \;=\; K_p \;+\; \frac{K_i}{1 - z^{-1}}
          `,caption:"The integrator gives Type-II behavior; Kp adds a zero for phase margin."}),e.jsxs("p",{children:["The zero from the PI sits at",e.jsx(t,{tex:"\\,\\omega_z = K_i/(K_p T_{ref})\\,"}),", normally placed ~one decade below the unity-gain crossover. With our defaults ",e.jsx(t,{tex:"K_p=8, K_i=0.5"})," and",e.jsx(t,{tex:"T_{ref}=25\\,\\mathrm{ns}"}),", that's",e.jsx(t,{tex:"\\,\\omega_z/(2\\pi)\\approx 400\\,\\mathrm{kHz}\\,"}),"."]})]}),e.jsxs("section",{children:[e.jsxs("h2",{children:["Why ",e.jsx("code",{children:"integ += s_k"})," runs ",e.jsx("em",{children:"before"})," the output line"]}),e.jsxs("p",{children:["If we updated the integrator ",e.jsx("em",{children:"after"})," producing",e.jsx("code",{children:" u[k] "}),", the integral path would have an extra one-sample delay. That delay isn't fatal but it changes the loop's phase margin in a non-obvious way. The early-update form gives the cleanest mapping to the",e.jsx(t,{tex:"K_i/(1-z^{-1})"})," transfer function above — what you derive on paper is what the code computes."]})]}),e.jsxs("section",{children:[e.jsxs("h2",{children:["Why ",e.jsx("code",{children:"reset()"})," exists"]}),e.jsxs("p",{children:["The Streamlit GUI re-runs the simulator on every parameter change, but caches a single ",e.jsx("code",{children:"DigitalPI"})," object via",e.jsx("code",{children:" @st.cache_data"}),". ",e.jsx("code",{children:"reset()"})," lets the cached object start fresh without re-instantiation, which keeps the cache key stable."]})]}),e.jsx(i,{kind:"info",children:"See the Lock-transient page for empirical tuning of Kp/Ki; the analytic NTF page derives how these gains shape the closed-loop noise response."})]})}export{g as default};
//# sourceMappingURL=ModLoopFilter-Dl82QgyR.js.map
