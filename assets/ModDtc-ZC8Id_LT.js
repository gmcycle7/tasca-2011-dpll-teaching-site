import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as s,g as a}from"./index-ooedyYhF.js";import{P as t}from"./PageLayout-D4DbgBvP.js";import{C as i}from"./CodeBlock-BWBDLxNG.js";import{E as n}from"./EquationBlock-DRbDSHwX.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";import"./vendor-math-BD26Pj5n.js";const l=a("mod-dtc");function m(){return e.jsxs(t,{meta:l,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Purpose"}),e.jsxs("p",{children:["Take an ",e.jsx("em",{children:"intended"})," delay (in seconds) and produce an",e.jsx("em",{children:" actual"})," delay after applying four impairment knobs. Defaults are all zero, so the DTC is ideal unless you say otherwise."]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"The whole file"}),e.jsx(i,{language:"python",filename:"sim/dtc.py",lineRange:"1-39",startLine:1,code:`"""Digital-to-time converter model.

The DTC accepts an *intended* delay (seconds) and produces an *actual*
delay after applying:
    * relative gain error      tau' = (1 + g) * tau_target
    * static offset            tau' += offset
    * uniform quantization     tau' = round(tau'/lsb) * lsb
    * static INL ripple        tau' += A * sin(2*pi*N_periods*tau_target/T_FS)

All optional; with defaults the DTC is ideal.
"""
import numpy as np


class DTC:
    def __init__(self, gain_err=0.0, offset_s=0.0,
                 quant_lsb_s=0.0,
                 inl_amp_s=0.0, inl_periods=0,
                 full_scale_s=25e-9):
        self.gain_err = float(gain_err)
        self.offset_s = float(offset_s)
        self.quant_lsb_s = float(quant_lsb_s)
        self.inl_amp_s = float(inl_amp_s)
        self.inl_periods = int(inl_periods)
        self.full_scale_s = float(full_scale_s)

    def apply(self, tau_target_s):
        tau = (1.0 + self.gain_err) * np.asarray(tau_target_s) + self.offset_s
        if self.inl_amp_s > 0 and self.inl_periods > 0:
            phase = 2.0 * np.pi * self.inl_periods * (
                np.asarray(tau_target_s) / max(self.full_scale_s, 1e-30))
            tau = tau + self.inl_amp_s * np.sin(phase)
        if self.quant_lsb_s > 0:
            tau = np.round(tau / self.quant_lsb_s) * self.quant_lsb_s
        return tau`})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Why these four knobs?"}),e.jsxs("ul",{className:"ml-6 list-disc space-y-2 text-slate-700",children:[e.jsxs("li",{children:[e.jsx("strong",{children:"Gain error."})," The dominant cause of incomplete cancellation. A 10% gain error leaves residual proportional to the DSM residue, which is what the LMS calibrator learns out."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"Static offset."})," Absorbed by the Type-II loop integrator at lock, but it eats DCO tuning range. Modeled so we can show that absorption in the Lock-transient page."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"INL ripple."})," Code-dependent residual delay; in our model a single-frequency sinusoid in code. Real INL has multiple spatial frequencies but a single-tone captures the spur-generating quasi-periodicity."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"Quantization."})," Sets a hard floor; default 1 ps LSB."]})]})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Why the ordering gain → INL → quant matters"}),e.jsx(n,{tex:String.raw`
            \tau_{out}
              = \mathrm{quant}\!\Bigl(
                  (1+g)\,\tau_{in} + \mathit{off}
                  + A\sin\!\bigl(2\pi N_p\,\tfrac{\tau_{in}}{T_{FS}}\bigr)
                \Bigr)
          `,caption:"Analog impairments first; quantization is the final stage, as in real hardware."}),e.jsx("p",{children:"Quantizing first would let later analog stages re-introduce sub-LSB values, which a real hardware DTC cannot do. The order we use mirrors a typical CMOS implementation: ideal-decoded code → analog delay element → discrete output."})]}),e.jsx(s,{kind:"limit",children:"Real INL has multiple spatial frequencies, drifts with supply and temperature, and depends on PVT-correlated mismatch. We model none of that — but the page on extensions discusses how to swap the sin() for a lookup table."})]})}export{m as default};
//# sourceMappingURL=ModDtc-ZC8Id_LT.js.map
