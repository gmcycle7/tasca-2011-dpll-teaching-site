import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import CodeBlock from "../components/CodeBlock";
import { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("mod-dco")!;

export default function ModDco() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Purpose</h2>
        <p>
          Convert a digital tuning word <Inline tex="u" /> into a DCO
          frequency. We model the tuning law as linear; the phase-noise
          contribution is generated separately and added in at the top
          level so this module stays a pure function.
        </p>
      </section>

      <section>
        <h2>The whole file</h2>
        <CodeBlock
          language="python"
          filename="sim/dco.py"
          lineRange="1-19"
          startLine={1}
          code={`"""Digitally controlled oscillator (linearized).

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
        return 1.0 / self.frequency(u)`}
        />
      </section>

      <section>
        <h2>Why linear is good enough here</h2>
        <p>
          The real DCO is anything but linear: a switched-capacitor bank
          for coarse tuning, a varactor + dithered fine bank for the high
          resolution. But near lock the loop only sees the small-signal
          gain at the current operating point, and that&apos;s what
          <Inline tex="K_{DCO}" /> represents. Modeling the full non-linear
          C-V curve adds complexity without changing closed-loop noise
          shaping at the level we care about.
        </p>
      </section>

      <section>
        <h2>Why no phase-noise injection inside DCO?</h2>
        <p>
          <code>DCO.frequency(u)</code> is a pure function with no
          stochastic state. Phase noise is generated once per simulation
          run as a pre-shaped time sequence in
          <code> sim/phase_noise.py </code> and added to the divider edge
          time in <code>pll_model.py</code>. Keeping random state out of
          this class means it&apos;s trivially unit-testable and
          inspectable.
        </p>
      </section>

      <AssumptionBox kind="info">
        See the closed-loop simulator and the phase-noise module for how
        the colored phase-noise sequence is generated and injected.
      </AssumptionBox>
    </PageLayout>
  );
}
