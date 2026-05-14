import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import PlotViewer from "../components/PlotViewer";
import CodeBlock from "../components/CodeBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("ext-sensitivity")!;

export default function ExtSensitivity() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">What this page exists for</h2>
        <p>
          A single simulation tells you one operating point. To understand
          which knob actually matters for jitter or for spurs, you need to
          sweep. The script does five sweeps on the same default
          configuration, measuring integrated jitter (3 kHz – 20 MHz) and
          worst-comb spur at every point.
        </p>
      </section>

      <section>
        <h2>The five sweeps</h2>
        <CodeBlock
          language="python"
          filename="scripts/run_sensitivity_sweep.py"
          lineRange="46-65"
          startLine={46}
          code={`def sweep_dtc_gain_err(base):
    xs = np.linspace(-0.20, 0.20, 9)
    rows = []
    for x in xs:
        p = replace(base, dtc_gain_err=float(x))
        j, s = measure(p)
        rows.append((x, j, s))
    return np.array(rows)


def sweep_dtc_inl(base):
    xs = np.linspace(0.0, 6.0, 7)
    rows = []
    for x in xs:
        p = replace(base, dtc_inl_amp_s=float(x) * 1e-12)
        j, s = measure(p)
        rows.append((x, j, s))
    return np.array(rows)`}
        />
        <p>
          The other three (<code>dsm_order</code>, <code>Kp</code>, DCO
          PN floor offset) follow the same pattern. The
          <code> measure() </code> helper runs one closed-loop sim and
          returns the integrated jitter and worst spur level.
        </p>
      </section>

      <section>
        <h2>Result</h2>
        <PlotViewer
          src="/figures/sensitivity_sweep.png"
          alt="Ten-panel sensitivity sweep: jitter (left column) and worst spur (right column) for each of five swept knobs."
          caption="Behavioral approximation. Each row is one knob; numbers in the body of this page summarise the headline."
        />
      </section>

      <section>
        <h2>What we learned</h2>
        <ul className="ml-6 list-disc space-y-3 text-slate-700">
          <li>
            <strong>DTC gain error dominates the design.</strong> With
            no calibration, jitter scales almost linearly with
            <code> |gain_err| </code>: from ≈ 500 fs at ideal up to ≈ 37
            ps at ±20% mismatch. This is the single most important
            reason the paper&apos;s LMS calibrator exists.
          </li>
          <li>
            <strong>DTC INL matters, but less than gain.</strong> 2 ps
            sinusoidal INL costs ≈ 200 fs of jitter and raises the
            worst spur from −88 to −84 dBc/Hz. Linear in our model;
            real INL shape can be worse.
          </li>
          <li>
            <strong>MASH-1-1-1 (order 3) is the sweet spot.</strong>
            Orders 1 and 2 produce more in-band quantization energy and
            louder spurs; order 3 pushes the DSM noise high enough that
            the loop attenuates it well.
          </li>
          <li>
            <strong>Kp has an optimum near 4.</strong> Below it the
            loop is too slow to track BBPD-folded noise; above it the
            loop amplifies that same noise. Either side of the optimum
            adds a few hundred fs of jitter.
          </li>
          <li>
            <strong>DCO PN floor matters less than you&apos;d think.</strong>
            Inside the loop BW the loop suppresses it; outside, our
            integration band runs out at f_ref/2 anyway. A 10 dB
            template shift moves the floor noticeably; a 5 dB shift is
            barely visible.
          </li>
        </ul>
      </section>

      <section>
        <h2>The takeaway as a one-liner</h2>
        <p>
          For this architecture, <strong>calibrate the DTC</strong>
          (eliminates the dominant jitter contributor),{" "}
          <strong>use a high-order DSM</strong> (cheap), and{" "}
          <strong>tune the loop bandwidth</strong> (small Kp range
          matters). DCO phase-noise template is a coarse knob — useful
          for budgeting but not the place to spend optimization effort.
        </p>
      </section>

      <AssumptionBox kind="warn">
        Sweep results depend on the default DCO PN template, which is
        ESTIMATED. The qualitative trends (gain_err dominates,
        intermediate Kp is best) are robust; the absolute jitter
        numbers should not be quoted as paper values.
      </AssumptionBox>
    </PageLayout>
  );
}
