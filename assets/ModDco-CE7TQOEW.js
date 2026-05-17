import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as o,g as s}from"./index-ooedyYhF.js";import{P as i}from"./PageLayout-D4DbgBvP.js";import{C as t}from"./CodeBlock-BWBDLxNG.js";import{I as n}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const a=s("mod-dco");function g(){return e.jsxs(i,{meta:a,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Purpose"}),e.jsxs("p",{children:["Convert a digital tuning word ",e.jsx(n,{tex:"u"})," into a DCO frequency. We model the tuning law as linear; the phase-noise contribution is generated separately and added in at the top level so this module stays a pure function."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"The whole file"}),e.jsx(t,{language:"python",filename:"sim/dco.py",lineRange:"1-19",startLine:1,code:`"""Digitally controlled oscillator (linearized).

f_DCO(u) = f_dco_nominal + K_dco * u    (Hz)

The simulator samples DCO state once per reference cycle. Per-cycle DCO
phase noise is injected in \`pll_model.py\` from a pre-generated colored
sequence (see \`phase_noise.generate_pn_sequence\`).
"""

class DCO:
    def __init__(self, f_dco_nominal: float, K_dco: float):
        self.f_nominal = float(f_dco_nominal)
        self.K_dco = float(K_dco)

    def frequency(self, u: float) -> float:
        return self.f_nominal + self.K_dco * u

    def period(self, u: float) -> float:
        return 1.0 / self.frequency(u)`})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Why linear is good enough here"}),e.jsxs("p",{children:["The real DCO is anything but linear: a switched-capacitor bank for coarse tuning, a varactor + dithered fine bank for the high resolution. But near lock the loop only sees the small-signal gain at the current operating point, and that's what",e.jsx(n,{tex:"K_{DCO}"})," represents. Modeling the full non-linear C-V curve adds complexity without changing closed-loop noise shaping at the level we care about."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Why no phase-noise injection inside DCO?"}),e.jsxs("p",{children:[e.jsx("code",{children:"DCO.frequency(u)"})," is a pure function with no stochastic state. Phase noise is generated once per simulation run as a pre-shaped time sequence in",e.jsx("code",{children:" sim/phase_noise.py "})," and added to the divider edge time in ",e.jsx("code",{children:"pll_model.py"}),". Keeping random state out of this class means it's trivially unit-testable and inspectable."]})]}),e.jsx(o,{kind:"info",children:"See the closed-loop simulator and the phase-noise module for how the colored phase-noise sequence is generated and injected."})]})}export{g as default};
//# sourceMappingURL=ModDco-CE7TQOEW.js.map
