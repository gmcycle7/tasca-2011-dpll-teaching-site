import { figureIndex } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";
import CodeBlock from "../components/CodeBlock";

const meta = figureIndex.find((f) => f.slug === "fig-bbpd-linearize")!;

export default function FigBBPDLinearize() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Why a 1-bit detector even works</h2>
        <p>
          A bang-bang phase detector outputs only ±1: it tells you which
          edge came first, never by how much. On its own that looks
          useless for a high-resolution loop. The trick is that, in the
          presence of noise, the <em>average</em> of those ±1 votes is a
          smooth function of the input time error.
        </p>
      </section>

      <section>
        <h2>Small-signal gain derivation</h2>
        <p>
          Let the time error at the BBPD input be
          <Inline tex="\,e+n" />, where <Inline tex="e" /> is the
          small-signal we want to measure and <Inline tex="n" /> is
          zero-mean Gaussian noise with standard deviation
          <Inline tex="\,\sigma" />. The expected output is
        </p>
        <EquationBlock
          tex={String.raw`
            \mathbb{E}[\,\mathrm{sgn}(e+n)\,]
              = \mathrm{erf}\!\left(\frac{e}{\sigma\sqrt{2}}\right)
              \approx \frac{2}{\sqrt{2\pi}\,\sigma}\,e
              \quad\text{for } |e|\ll\sigma.
          `}
        />
        <p>
          So for small <Inline tex="e" />, the BBPD behaves like a linear
          gain block with
        </p>
        <EquationBlock
          tex={String.raw`K_{bb} \;=\; \sqrt{\frac{2}{\pi}}\,\frac{1}{\sigma}\;\;\;\big[\,\mathrm{s}^{-1}\big]`}
          caption="The classical Da Dalt result for a sign-detector with Gaussian-noise dither."
        />
        <p>
          The detector is implemented as bare <code>sign()</code> in the
          simulator and this <Inline tex="K_{bb}" /> appears only as a
          helper for hand calculations of loop bandwidth and stability.
        </p>
      </section>

      <section>
        <h2>What sets the dither σ?</h2>
        <p>
          At lock the BBPD input is the sum of every &quot;non-cancelled&quot;
          jitter source: DCO phase noise sampled at the reference rate,
          reference jitter, DTC quantization noise, and any residual DSM
          term after DTC cancellation. In our default setup that adds up
          to a few hundred fs RMS, which keeps the small-signal
          approximation comfortably valid.
        </p>
        <p>
          Increasing σ — for example by deliberately impairing the DTC —
          reduces <Inline tex="K_{bb}" /> and therefore the loop bandwidth.
          This is the well-known &quot;bang-bang gain depends on its own
          input noise&quot; coupling that motivates the LMS bandwidth
          tracker in later work from the same group.
        </p>
      </section>

      <section>
        <h2>Inside the code</h2>
        <CodeBlock
          language="python"
          filename="sim/bbpd.py"
          lineRange="19-33"
          startLine={19}
          code={`def decide(self, time_error_s: float) -> int:
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
          caption="Two methods, one ±1 detector + one helper for hand calculations."
        />
        <p>
          The optional <code>meta_noise_rms_s</code> models comparator
          metastability — a real D-flip-flop can flip the wrong way
          when its setup/hold window is violated, and that random
          behavior is equivalent to extra dither at the input. The
          random tie-break in the <code>else</code> branch prevents the
          loop from getting stuck at the (measure-zero in hardware,
          easily hit in simulation) <Inline tex="e=0" /> point.
        </p>
        <p>
          <code>linearized_gain</code> is a <code>@staticmethod</code>:
          the simulator never calls it (the loop uses real
          <code> sign() </code>), but every analytic derivation that
          needs <Inline tex="K_{bb}" /> can call
          <code> BBPD.linearized_gain(sigma) </code> and stay in sync
          with whatever convention <code>decide()</code> implements.
        </p>
      </section>

      <AssumptionBox kind="info">
        <Inline tex="K_{bb}" /> is only meaningful when the input PDF is
        approximately Gaussian and zero-mean. During lock pull-in or when
        the loop is bumped, the input is highly skewed and the linearized
        gain underestimates the actual response — which is why our PI
        coefficients are tuned empirically rather than from the
        small-signal formula alone.
      </AssumptionBox>
    </PageLayout>
  );
}
