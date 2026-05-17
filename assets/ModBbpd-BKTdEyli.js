import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as t,g as s}from"./index-ooedyYhF.js";import{P as n}from"./PageLayout-D4DbgBvP.js";import{C as o}from"./CodeBlock-BWBDLxNG.js";import{I as i,E as r}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const a=s("mod-bbpd");function g(){return e.jsxs(n,{meta:a,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Purpose"}),e.jsxs("p",{children:["A single flip-flop, behaviorally. Two methods only: the actual",e.jsx("code",{children:" decide() "})," that emits ±1, and a static helper that returns the linearized small-signal gain for hand calculation."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"The whole file"}),e.jsx(o,{language:"python",filename:"sim/bbpd.py",lineRange:"1-33",startLine:1,code:`"""Bang-bang phase detector / single-bit TDC.

Output: sign(time_error + decision_noise).
Convention: positive time error => output +1.
"""
import numpy as np


class BBPD:
    def __init__(self, meta_noise_rms_s=0.0, rng=None):
        self.meta_noise_rms_s = float(meta_noise_rms_s)
        self.rng = rng if rng is not None else np.random.default_rng(0)

    def decide(self, time_error_s: float) -> int:
        if self.meta_noise_rms_s > 0:
            time_error_s = time_error_s + self.rng.normal(
                0.0, self.meta_noise_rms_s)
        if time_error_s > 0.0:
            return 1
        if time_error_s < 0.0:
            return -1
        return int(self.rng.choice([-1, 1]))

    @staticmethod
    def linearized_gain(sigma_in_s: float) -> float:
        if sigma_in_s <= 0:
            return float("inf")
        return float(np.sqrt(2.0 / np.pi) / sigma_in_s)`})]}),e.jsxs("section",{children:[e.jsxs("h2",{children:["Why ",e.jsx("code",{children:"decide()"})," handles the tie case explicitly"]}),e.jsxs("p",{children:["A real flip-flop has measure-zero probability of seeing exactly zero phase error, but a behavioral simulation can. Without the explicit tie-break, a brand-new run starting from",e.jsx(i,{tex:"\\,t_{div}=t_{ref}\\,"})," at cycle 0 would return",e.jsx("code",{children:" 0 "})," on the first sample, the loop filter would add zero, the DCO would never move, and the loop would (incorrectly) appear locked forever. The randomized tie-break makes that pathological start indistinguishable from any other."]})]}),e.jsxs("section",{children:[e.jsxs("h2",{children:["Why expose ",e.jsx("code",{children:"linearized_gain"})," at all"]}),e.jsx(r,{tex:String.raw`K_{bb} \;=\; \sqrt{\frac{2}{\pi}}\,\frac{1}{\sigma_{in}}\quad[\mathrm{s}^{-1}]`,caption:"Equivalent small-signal gain of a sign() detector with Gaussian input of std σ."}),e.jsxs("p",{children:["The simulator ",e.jsx("em",{children:"does not"})," use this number anywhere. It is a static method on the class purely so that derivations elsewhere in the codebase (notebooks, the future",e.jsx("code",{children:" sim/noise_tf.py "}),", and this teaching site) can call ",e.jsx("code",{children:"BBPD.linearized_gain(sigma)"})," and stay in sync with whatever convention the detector itself uses. If someone ever changes ",e.jsx("code",{children:"decide()"})," to a non-sign() detector, the same file owns both definitions and they can't drift."]})]}),e.jsxs("section",{children:[e.jsxs("h2",{children:["The ",e.jsx("code",{children:"meta_noise_rms_s"})," knob"]}),e.jsxs("p",{children:["Real D-flip-flops have a setup/hold window in which the output becomes a random variable. We model that by adding Gaussian dither to the input ",e.jsx("em",{children:"before"})," the sign(). Default is 0 (so the simulator is deterministic in BBPD), turn it on via the GUI when teaching BBPD ",e.jsx(i,{tex:"K_{bb}"})," dependence on input dither."]})]}),e.jsx(t,{kind:"info",title:"Connection",children:"The BBPD page derives the linearized gain expression in detail; the LMS page shows how this 1-bit output is enough to drive a full adaptive calibration loop."})]})}export{g as default};
//# sourceMappingURL=ModBbpd-BKTdEyli.js.map
