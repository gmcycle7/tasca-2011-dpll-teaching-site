import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("mod-bbpd")!;

export default function ModBbpd() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Purpose</h2>
        <p>
          A single flip-flop, behaviorally. Two methods only: the actual
          <code> decide() </code> that emits ±1, and a static helper that
          returns the linearized small-signal gain for hand calculation.
        </p>
      </section>

      <section>
        <h2>The whole file</h2>
        <CodeBlock
          language="python"
          filename="sim/bbpd.py"
          lineRange="1-33"
          startLine={1}
          code={`"""Bang-bang phase detector / single-bit TDC.

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
        return float(np.sqrt(2.0 / np.pi) / sigma_in_s)`}
        />
      </section>

      <section>
        <h2>Why <code>decide()</code> handles the tie case explicitly</h2>
        <p>
          A real flip-flop has measure-zero probability of seeing exactly
          zero phase error, but a behavioral simulation can. Without the
          explicit tie-break, a brand-new run starting from
          <Inline tex="\,t_{div}=t_{ref}\," /> at cycle 0 would return
          <code> 0 </code> on the first sample, the loop filter would
          add zero, the DCO would never move, and the loop would
          (incorrectly) appear locked forever. The randomized tie-break
          makes that pathological start indistinguishable from any other.
        </p>
      </section>

      <section>
        <h2>Why expose <code>linearized_gain</code> at all</h2>
        <EquationBlock
          tex={String.raw`K_{bb} \;=\; \sqrt{\frac{2}{\pi}}\,\frac{1}{\sigma_{in}}\quad[\mathrm{s}^{-1}]`}
          caption="Equivalent small-signal gain of a sign() detector with Gaussian input of std σ."
        />
        <p>
          The simulator <em>does not</em> use this number anywhere. It is
          a static method on the class purely so that derivations
          elsewhere in the codebase (notebooks, the future
          <code> sim/noise_tf.py </code>, and this teaching site) can
          call <code>BBPD.linearized_gain(sigma)</code> and stay in sync
          with whatever convention the detector itself uses. If someone
          ever changes <code>decide()</code> to a non-sign() detector,
          the same file owns both definitions and they can&apos;t drift.
        </p>
      </section>

      <section>
        <h2>The <code>meta_noise_rms_s</code> knob</h2>
        <p>
          Real D-flip-flops have a setup/hold window in which the output
          becomes a random variable. We model that by adding Gaussian
          dither to the input <em>before</em> the sign(). Default is 0
          (so the simulator is deterministic in BBPD), turn it on via the
          GUI when teaching BBPD <Inline tex="K_{bb}" /> dependence on
          input dither.
        </p>
      </section>

      <AssumptionBox kind="info" title="Connection">
        The BBPD page derives the linearized gain expression in detail; the
        LMS page shows how this 1-bit output is enough to drive a full
        adaptive calibration loop.
      </AssumptionBox>
    </PageLayout>
  );
}
