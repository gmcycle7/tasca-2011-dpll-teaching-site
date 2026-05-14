import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("mod-dsm")!;

export default function ModDsm() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Purpose</h2>
        <p>
          The DSM hands the divider an integer sequence whose long-term
          mean equals the fractional ratio <Inline tex="\alpha" />, while
          shaping the resulting noise away from low offsets. Critically,
          the same module also reports the <em>cumulative residue</em>
          <Inline tex="\,e_{dsm}[k]\," /> that the DTC needs to cancel — so
          the DTC never has to reach inside the DSM and reverse-engineer
          its state.
        </p>
      </section>

      <section>
        <h2>Sign convention exposed at the top</h2>
        <CodeBlock
          language="python"
          filename="sim/dsm.py"
          lineRange="1-18"
          startLine={1}
          code={`"""Delta-sigma modulator for fractional-N divider control.

Supports order = 1, 2, or 3 (MASH 1-1-1). The modulator takes a
normalized fractional input alpha in [0, 1) and emits an integer dither
sequence m[k]. We also report the cumulative residue

    e_dsm[k] = (alpha-sum over k steps) - sum_{j<=k} m[j]            (cycles)

which is exactly the displacement (in DCO periods) of the k-th divider
edge from where an ideal fractional divider would have emitted it.
The DTC is programmed to cancel this displacement.

Sign convention: if e_dsm > 0, the integer divider has emitted FEWER
DCO cycles than the ideal fractional divider would, so the divider
edge is EARLIER than ideal by e_dsm * T_dco. The DTC delays the
divider edge by tau_dtc = e_dsm * T_dco_nominal (positive delay) to
align with the reference.
"""`}
        />
        <p>
          The DSM is the single place where the &quot;divider edge is
          early by e_dsm * T_DCO&quot; relationship is established, so the
          docstring carries that derivation. Every other file just trusts
          it.
        </p>
      </section>

      <section>
        <h2>State and initialization</h2>
        <CodeBlock
          language="python"
          filename="sim/dsm.py"
          lineRange="22-39"
          startLine={22}
          code={`class MASH:
    """Cascaded first-order accumulators (1, 2, or 3 stages)."""

    def __init__(self, order: int, quant_levels: int, seed: int = 0):
        if order not in (1, 2, 3):
            raise ValueError("MASH order must be 1, 2, or 3")
        self.order = order
        self.M = int(quant_levels)
        self.acc1 = 0
        self.acc2 = 0
        self.acc3 = 0
        # History for error-cancellation network
        self.y2_prev = 0
        self.y3_prev = 0
        self.y3_prev2 = 0
        self.rng = np.random.default_rng(seed)
        self._alpha_accum = 0.0
        self._cum_y = 0`}
        />
        <p>
          Three stages of integer accumulators (one per MASH order), plus
          the small history register needed by the
          <em> error-cancellation network</em>. Using Python integers (not
          floats) for the accumulators is deliberate — it models a real
          hardware accumulator with finite width
          <Inline tex="\,M=2^{24}\," /> and avoids the floating-point
          rounding that would create a spurious −300 dB noise floor in
          simulation.
        </p>
      </section>

      <section>
        <h2>One step</h2>
        <CodeBlock
          language="python"
          filename="sim/dsm.py"
          lineRange="41-79"
          startLine={41}
          code={`    def step(self, alpha: float):
        """Advance one cycle. Returns (m_k, e_dsm_after_k_steps)."""
        x = int(round(alpha * self.M))

        # Stage 1
        self.acc1 += x
        y1 = self.acc1 // self.M
        self.acc1 -= y1 * self.M  # residue in [0, M)

        if self.order == 1:
            y_out = y1
        else:
            # Stage 2 input: stage-1 residue
            self.acc2 += self.acc1
            y2 = self.acc2 // self.M
            self.acc2 -= y2 * self.M

            if self.order == 2:
                # Error-cancel: y = y1 + (1-z^-1) y2
                y_out = y1 + (y2 - self.y2_prev)
                self.y2_prev = y2
            else:
                # Stage 3 input: stage-2 residue
                self.acc3 += self.acc2
                y3 = self.acc3 // self.M
                self.acc3 -= y3 * self.M
                # Error-cancel: y = y1 + (1-z^-1) y2 + (1-z^-1)^2 y3
                y_out = (y1
                         + (y2 - self.y2_prev)
                         + (y3 - 2 * self.y3_prev + self.y3_prev2))
                self.y3_prev2 = self.y3_prev
                self.y3_prev = y3
                self.y2_prev = y2

        # Cumulative residue using running mean (robust to alpha changes)
        self._alpha_accum += alpha
        self._cum_y += y_out
        e_dsm = self._alpha_accum - self._cum_y
        return int(y_out), float(e_dsm)`}
        />
      </section>

      <section>
        <h2>Why the error-cancellation network looks like that</h2>
        <p>
          A single 1st-order modulator gives quantization noise shaped as
          <Inline tex="\,(1-z^{-1})\,Q\,." /> Cascading
          <em> three</em> 1st-order stages, with the next stage taking the
          previous stage&apos;s residue as input, gives:
        </p>
        <EquationBlock
          tex={String.raw`
            Y(z) \;=\; \alpha + (1-z^{-1})^3\,Q_3(z)
          `}
          caption="3rd-order high-pass shaping at the output. Pushes quantization energy above the loop BW."
        />
        <p>
          The clever bit is the <em>cancellation network</em>: by
          subtracting differenced copies of <Inline tex="y_2" /> and
          <Inline tex="y_3" /> from <Inline tex="y_1" />, the residues of
          stages 1 and 2 cancel, leaving only the (heavily shaped)
          residue of stage 3. That is the only thing you ever see at the
          output.
        </p>
      </section>

      <section>
        <h2>The single most important line</h2>
        <CodeBlock
          language="python"
          filename="sim/dsm.py"
          lineRange="75-79"
          startLine={75}
          code={`        # Cumulative residue using running mean (robust to alpha changes)
        self._alpha_accum += alpha
        self._cum_y += y_out
        e_dsm = self._alpha_accum - self._cum_y
        return int(y_out), float(e_dsm)`}
        />
        <p>
          <strong>Why track <Inline tex="e_{dsm}" /> separately instead of
          reading <code>acc1</code> directly?</strong> For 1st-order DSMs
          the stage-1 accumulator IS the residue, but for MASH the
          residue is a more complex function of all three stages.
          Cumulative running sums are the same formula for every MASH
          order, and stay correct if a caller dynamically changes
          <code> alpha </code> mid-simulation (frequency hopping).
        </p>
      </section>

      <AssumptionBox kind="info" title="Connection to other pages">
        The <Inline tex="\,e_{dsm}[k]\," /> emitted here is exactly the
        signal the DTC&apos;s <code>tau_target</code> consumes (see
        <code> sim/pll_model.py </code>) and also the LMS regressor for
        adaptive DTC-gain calibration (see the LMS page).
      </AssumptionBox>
    </PageLayout>
  );
}
