import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as i,f as o}from"./index-ooedyYhF.js";import{P as r}from"./PageLayout-D4DbgBvP.js";import{E as a,I as t}from"./EquationBlock-DRbDSHwX.js";import{P as l}from"./PlotViewer-C2lcD2nR.js";import{P as c}from"./ParameterTable-CgYLVfjc.js";import{C as s}from"./CodeBlock-BWBDLxNG.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const h=o.find(n=>n.slug==="fig-lock-transient"),d=[{symbol:"Kp",description:"Proportional gain",value:"8.0",source:"ESTIMATED",notes:"Picked empirically; not paper-stated"},{symbol:"Ki",description:"Integral gain",value:"0.5",source:"ESTIMATED",notes:"Faster pull-in than the small-signal calc suggests"},{symbol:"K_dco",description:"DCO LSB",value:"10 kHz",source:"ESTIMATED",notes:"Real chip's 70 Hz step is much finer"},{symbol:"Δf₀",description:"Initial offset",value:"2 MHz",source:"ESTIMATED",notes:"Test stimulus"}];function k(){return e.jsxs(r,{meta:h,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"What we're testing"}),e.jsx("p",{children:"We start the DCO 2 MHz away from the target carrier and let the digital PI loop pull it in. Because the loop is Type-II (integrator in the filter), the steady-state phase error is zero, and the steady-state frequency offset is also zero — the integrator holds the right DCO code indefinitely."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Continuous-time small-signal model"}),e.jsx("p",{children:"Linearizing the BBPD (see the BBPD page) and the divider, the loop gain at low frequency reduces to"}),e.jsx(a,{tex:String.raw`
            L(s) \;\approx\; K_{bb}\;\frac{K_p\,s + K_i/T_{ref}}{s^2}\;
                  \frac{K_{DCO}}{f_{DCO,nom}}
          `,caption:"Two integrators (filter's I path + DCO's frequency→phase integration) ⇒ Type-II."}),e.jsx("p",{children:"The unity-gain crossover and the zero from the PI filter determine bandwidth and phase margin. With our defaults the ringdown is ~150 µs, visible in the plot below."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Simulation"}),e.jsx(l,{src:"/figures/core_lock_test.png",alt:"DCO frequency error, tuning word, and BBPD-input error vs. time for a 2 MHz initial offset.",caption:"Top: f_DCO − target. Middle: u settles at ≈200 LSB ↔ +2 MHz pulled. Bottom: BBPD error decays into ps-scale hunting."})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Numbers we used"}),e.jsx(c,{rows:d})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Inside the code — the PI loop filter"}),e.jsx("p",{children:"The full implementation of the discrete-time PI controller is ten executable lines:"}),e.jsx(s,{language:"python",filename:"sim/loop_filter.py",lineRange:"10-24",startLine:10,code:`class DigitalPI:
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
        return self.u_init + self.Kp * s_k + self.Ki * self.integ`}),e.jsxs("p",{children:["The integrator updates ",e.jsx("em",{children:"before"})," the output line so that the value used at cycle ",e.jsx(t,{tex:"k"})," already includes",e.jsx(t,{tex:"\\,s[k]\\,"}),". This matches the textbook",e.jsx(t,{tex:"\\;K_i/(1-z^{-1})\\;"})," exactly — no surprise unit delay."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"How the lock test sets up the initial frequency error"}),e.jsx(s,{language:"python",filename:"scripts/run_core_lock_test.py",lineRange:"29-35",startLine:29,code:`p = PLLParams(n_cycles=args.n_cycles)
# Force an initial frequency error by shifting f_dco_nominal so the
# zero-tuning DCO sits args.df_init_hz away from the desired carrier.
p.f_dco_nominal = p.f_out_target - args.df_init_hz
# Disable DCO and reference phase noise to make the lock transient easy
# to read; DSM dither and DTC cancellation are on.
res = run_simulation(p, enable_dtc=True,
                     enable_dco_pn=False, enable_ref_noise=False)`}),e.jsxs("p",{children:["We perturb ",e.jsx("code",{children:"f_dco_nominal"})," rather than",e.jsx("code",{children:" u_init "})," so that the BBPD's first non-zero decision happens organically: with ",e.jsx("code",{children:"u_init = 0"})," the DCO sits at its nominal, which is now 2 MHz below target, the divider edges accumulate lag, BBPD reports +1, and the PI integrator winds up from there."]})]}),e.jsx(i,{kind:"info",children:"We use Kp=8, Ki=0.5 to keep the transient short for the demo. Lowering Ki to ≈0.02 (closer to the small-signal-optimum for steady-state hunting) gives smaller tail RMS but much slower pull-in."}),e.jsx(i,{kind:"limit",children:"We do not yet model the coarse capacitor bank that would normally do a discrete frequency hop into the right sub-range before the fine loop takes over."})]})}export{k as default};
//# sourceMappingURL=FigLockTransient-YufRSAgR.js.map
