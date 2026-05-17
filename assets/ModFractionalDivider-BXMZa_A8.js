import{j as e}from"./vendor-react-DP5dBkVy.js";import{A as i,g as t}from"./index-ooedyYhF.js";import{P as n}from"./PageLayout-D4DbgBvP.js";import{C as o}from"./CodeBlock-BWBDLxNG.js";import"./vendor-react-dom-D4HI9nvn.js";import"./vendor-router-XjnuBimX.js";import"./vendor-syntax-C8xOikxa.js";const s=t("mod-fractional-divider");function u(){return e.jsxs(n,{meta:s,children:[e.jsxs("section",{children:[e.jsx("h2",{className:"!mt-0",children:"Purpose"}),e.jsxs("p",{children:['Behavioral models of a multi-modulus divider can be one line: "count ',e.jsx("code",{children:"D_k = N_int + m[k]"}),' DCO cycles, then emit an edge." In a time-stepped simulator, that counting is replaced by an analytic calculation of when the next edge happens. So this whole file is a thin wrapper — intentionally.']})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"The whole file"}),e.jsx(o,{language:"python",filename:"sim/fractional_divider.py",lineRange:"1-15",startLine:1,code:`"""Thin wrapper that turns a DSM output into a per-cycle divider modulus.

The divider counts D[k] = N_int + m[k] DCO cycles before emitting an
edge. Where the simulator needs the (modulus, residue) pair, it reads
them directly from the DSM. This file is kept for diagrammatic clarity
and to be the natural extension point for adding modulus randomization,
duty-cycle effects, etc.
"""

class FractionalDivider:
    def __init__(self, N_int: int):
        self.N_int = int(N_int)

    def cycles(self, m_k: int) -> int:
        return self.N_int + int(m_k)`})]}),e.jsxs("section",{children:[e.jsx("h2",{children:"Why have this file at all, then?"}),e.jsx("p",{children:"Three reasons, in order of importance:"}),e.jsxs("ul",{className:"ml-6 list-disc space-y-2 text-slate-700",children:[e.jsxs("li",{children:[e.jsx("strong",{children:"Naming."}),' The main simulation loop reads as "ask the divider for the cycle count, then advance the DCO accordingly" — that maps directly onto the hardware block diagram. Inlining the addition would lose the named-block correspondence.']}),e.jsxs("li",{children:[e.jsx("strong",{children:"Extension point."})," When we eventually model divider-modulus randomization or duty-cycle distortion, those live here without touching ",e.jsx("code",{children:"pll_model.py"}),"."]}),e.jsxs("li",{children:[e.jsx("strong",{children:"Unit testability."})," One-method classes are trivial to test, and that's how I caught an early bug where ",e.jsx("code",{children:"m_k"})," was floating-point."]})]})]}),e.jsx(i,{kind:"limit",children:"Real multi-modulus dividers can introduce period-dependent jitter and duty-cycle distortion. None of that is modeled here. The divider in our sim has zero internal noise."})]})}export{u as default};
//# sourceMappingURL=ModFractionalDivider-BXMZa_A8.js.map
