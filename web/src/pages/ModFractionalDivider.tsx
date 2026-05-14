import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import CodeBlock from "../components/CodeBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("mod-fractional-divider")!;

export default function ModFractionalDivider() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Purpose</h2>
        <p>
          Behavioral models of a multi-modulus divider can be one line:
          &quot;count <code>D_k = N_int + m[k]</code> DCO cycles, then
          emit an edge.&quot; In a time-stepped simulator, that
          counting is replaced by an analytic calculation of when the
          next edge happens. So this whole file is a thin wrapper —
          intentionally.
        </p>
      </section>

      <section>
        <h2>The whole file</h2>
        <CodeBlock
          language="python"
          filename="sim/fractional_divider.py"
          lineRange="1-15"
          startLine={1}
          code={`"""Thin wrapper that turns a DSM output into a per-cycle divider modulus.

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
        return self.N_int + int(m_k)`}
        />
      </section>

      <section>
        <h2>Why have this file at all, then?</h2>
        <p>
          Three reasons, in order of importance:
        </p>
        <ul className="ml-6 list-disc space-y-2 text-slate-700">
          <li>
            <strong>Naming.</strong> The main simulation loop reads as
            &quot;ask the divider for the cycle count, then advance the
            DCO accordingly&quot; — that maps directly onto the hardware
            block diagram. Inlining the addition would lose the
            named-block correspondence.
          </li>
          <li>
            <strong>Extension point.</strong> When we eventually model
            divider-modulus randomization or duty-cycle distortion,
            those live here without touching <code>pll_model.py</code>.
          </li>
          <li>
            <strong>Unit testability.</strong> One-method classes are
            trivial to test, and that&apos;s how I caught an early bug
            where <code>m_k</code> was floating-point.
          </li>
        </ul>
      </section>

      <AssumptionBox kind="limit">
        Real multi-modulus dividers can introduce period-dependent jitter
        and duty-cycle distortion. None of that is modeled here. The
        divider in our sim has zero internal noise.
      </AssumptionBox>
    </PageLayout>
  );
}
