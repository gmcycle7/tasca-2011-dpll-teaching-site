import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import PlotViewer from "../components/PlotViewer";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("ext-multibit-tdc")!;

export default function ExtMultibitTdc() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">The architectural question</h2>
        <p>
          A high-resolution multi-bit TDC measures phase error directly.
          Why bother with a 1-bit detector + a feedback DTC? This page
          runs four closed-loop simulations on the same DCO, DSM, and
          loop bandwidth, swapping only the detector and the
          cancellation block, so the architectural trade-off becomes
          visible.
        </p>
      </section>

      <section>
        <h2>The four cases</h2>
        <ol className="ml-6 list-decimal space-y-2 text-slate-700">
          <li>
            <strong>BBPD + ideal DTC</strong> (the paper). 1-bit
            detector; DTC pre-cancels the DSM residue in the time
            domain so the comparator sees sub-ps jitter.
          </li>
          <li>
            <strong>8-bit TDC, no cancellation.</strong> TDC sees the
            full hundreds-of-ps DSM dither.
          </li>
          <li>
            <strong>8-bit TDC + digital DSM cancellation.</strong>{" "}
            Subtract <Inline tex="\,e_{dsm}[k]\!\cdot\!T_{DCO}\," /> from
            the TDC output before the loop filter. This is what the DTC
            does — just moved into the digital domain.
          </li>
          <li>
            <strong>12-bit TDC + digital DSM cancellation.</strong> Same
            architecture as 3, finer LSB.
          </li>
        </ol>
      </section>

      <section>
        <h2>Inside the code — the digital cancellation</h2>
        <p>
          Adding cancellation to the TDC simulator is two lines: read
          the DSM residue, subtract it from the TDC output before the
          loop filter sees it.
        </p>
        <CodeBlock
          language="python"
          filename="sim/multibit_tdc.py"
          lineRange="143-148"
          startLine={143}
          code={`# Digital DSM cancellation: subtract predicted residue
if enable_dsm_cancel:
    e_ac = e_q - cancel_gain * e_dsm_k * params.T_dco_nominal
else:
    e_ac = e_q

u = lpf.step(e_ac / sigma_ref_s)`}
        />
        <p>
          <strong>Why <code>/ sigma_ref_s</code>?</strong> The TDC
          outputs a time error in seconds; the BBPD outputs ±1
          dimensionless. To keep the loop bandwidth roughly the same
          across architectures, we normalize the TDC output by a
          reference jitter scale (default ≈ 0.35 ps), which is the
          range where the BBPD&apos;s linearized gain matches the TDC&apos;s
          unit gain.
        </p>
      </section>

      <section>
        <h2>Result</h2>
        <PlotViewer
          src="/figures/multibit_tdc.png"
          alt="Closed-loop L(f): BBPD+DTC, 8-bit TDC (no cancel), 8-bit TDC+cancel, 12-bit TDC+cancel."
          caption="BBPD+DTC: −117 dBc/Hz floor. 12-bit TDC + cancel: −113 dBc/Hz floor — they meet. 8-bit TDC: ≈ −95 dBc/Hz floor; cancellation doesn't help because TDC LSB quantization itself becomes the limiter."
        />
      </section>

      <section>
        <h2>What the four traces tell us</h2>
        <ul className="ml-6 list-disc space-y-2 text-slate-700">
          <li>
            <strong>BBPD + DTC and 12-bit TDC + cancel meet within ~4 dB.</strong>{" "}
            The architectures are noise-equivalent once both implement
            DSM-residue cancellation. The 12-bit TDC has a tiny
            quantization advantage at high offsets; the BBPD path has a
            slight in-band advantage. Negligible difference.
          </li>
          <li>
            <strong>8-bit TDC without cancellation is ~20 dB worse
            in-band.</strong> The DSM dither passes straight through the
            TDC and modulates the DCO. This is the trace that motivates
            the whole DTC idea.
          </li>
          <li>
            <strong>8-bit TDC + cancel does not match BBPD+DTC.</strong>{" "}
            Even with ideal digital cancellation, the LSB quantization
            of the TDC sets a floor at
          </li>
        </ul>
        <EquationBlock
          tex={String.raw`
            \mathcal{L}_{TDC,floor}(f)\;\approx\;\frac{(\Delta_{LSB})^2}{12\cdot f_{ref}/2}\,(2\pi f_{out})^2\,|H_{ref}|^2 / 2
          `}
          caption="Uniform quantization noise PSD passed through the closed loop."
        />
        <p>
          For <Inline tex="\Delta_{LSB}\approx 4\,\mathrm{ps}" /> and our
          loop, this lands near −107 dBc/Hz, consistent with what we
          measure. Get the LSB down by 4 bits → floor drops by 24 dB,
          which is what the 12-bit case shows.
        </p>
      </section>

      <section>
        <h2>The bottom line</h2>
        <p>
          A multi-bit TDC <em>can</em> match BBPD + DTC — provided you
          pair it with digital DSM cancellation (the digital twin of the
          DTC) <strong>and</strong> spend enough bits (≥ 12 in our
          sweep) to push TDC quantization below the DCO PN floor. Both
          architectures then face the same fundamental noise sources;
          the choice becomes one of analog vs. digital implementation
          cost. The paper picked BBPD + analog DTC because a 1-bit
          detector and a delay-line DTC are dramatically cheaper to
          build at sub-ps resolution than a 12+ bit TDC with the
          required noise floor.
        </p>
      </section>

      <AssumptionBox kind="info">
        Both cancellation methods are perfect here (cancel gain = 1, no
        analog DTC gain error). Real chips need calibration in both
        cases — LMS for the DTC gain (see the LMS page) or the digital
        cancellation coefficient. The calibration problem is the same
        either way, which is one more reason the choice between
        architectures becomes a cost-per-bit question rather than a
        noise question.
      </AssumptionBox>
    </PageLayout>
  );
}
