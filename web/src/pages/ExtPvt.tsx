import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import PlotViewer from "../components/PlotViewer";
import CodeBlock from "../components/CodeBlock";
import AssumptionBox from "../components/AssumptionBox";
import { Inline } from "../components/EquationBlock";

const meta = getPageBySlug("ext-pvt-monte-carlo")!;

export default function ExtPvt() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">What this page is</h2>
        <p>
          A single nominal simulation tells you how the chip will
          perform once. PVT (process / voltage / temperature) Monte
          Carlo tells you how the same chip will perform across the
          whole population of dice and operating points. Yield numbers
          come from this kind of sweep.
        </p>
      </section>

      <section>
        <h2>What we perturb</h2>
        <p>
          Each of <Inline tex="N=30" /> trials applies an independent
          Gaussian perturbation to the impairment knobs, with the
          three-sigma values listed below:
        </p>
        <CodeBlock
          language="python"
          filename="scripts/run_pvt_monte_carlo.py"
          lineRange="33-52"
          startLine={33}
          code={`def perturb(base, rng):
    """Apply a one-sigma perturbation to each impairment knob."""
    K_dco = base.K_dco * (1.0 + rng.normal(0, 0.20 / 3))       # ±20% 3-sigma
    pn_shift_db = rng.normal(0, 5.0 / 3)                       # ±5 dB 3-sigma
    pn_levels = tuple(float(L + pn_shift_db) for L in base.dco_pn_levels_dbchz)
    g_err = rng.normal(0, 0.10 / 3)                            # ±10% DTC gain error
    offset_s = rng.normal(0, 5e-12 / 3)                        # ±5 ps DTC offset
    meta_s = abs(rng.normal(0, 1e-12 / 3))                     # 1 ps BBPD metastability
    Kp = base.Kp * (1.0 + rng.normal(0, 0.05 / 3))
    Ki = base.Ki * (1.0 + rng.normal(0, 0.05 / 3))
    return dataclasses.replace(base, K_dco=K_dco, ...)`}
        />
        <p>
          The DTC gain error term dominates the envelope: that&apos;s
          why the median jitter inflates to <strong>~5 ps</strong>
          rather than the ~500 fs of the nominal run. With LMS gain
          calibration enabled, the same Monte Carlo would compress the
          envelope dramatically (try toggling{" "}
          <code>enable_lms=True</code> at the bottom of the script).
        </p>
      </section>

      <section>
        <h2>Result</h2>
        <PlotViewer
          src="/figures/pvt_monte_carlo.png"
          alt="Four-panel PVT Monte Carlo: jitter histogram, spur histogram, scatter, yield curves."
          caption="N=30 trials, no LMS calibration. Median ≈ 5 ps RMS / −65 dBc/Hz; P90 ≈ 10 ps / −58 dBc/Hz."
        />
      </section>

      <section>
        <h2>How to read it</h2>
        <ul className="ml-6 list-disc space-y-2 text-slate-700 dark:text-slate-300">
          <li>
            <strong>Jitter histogram (top-left).</strong> Median ~ 5 ps
            RMS — a 10× inflation over the nominal sim. Almost
            entirely from the ±10% DTC gain-error term, confirming the
            sensitivity-sweep page&apos;s finding.
          </li>
          <li>
            <strong>Spur histogram (top-right).</strong> Worst spur is
            tightly distributed around −65 dBc/Hz because all
            impairments contribute, not just one.
          </li>
          <li>
            <strong>Scatter (bottom-left).</strong> The two metrics are
            mildly correlated. Trials with the worst jitter usually
            also have the worst spurs, because both react to the same
            DTC mismatch.
          </li>
          <li>
            <strong>Yield curves (bottom-right).</strong> Direct
            engineering output: pick a spec, read off the percentage
            of chips that meet it. With a 7 ps RMS spec, ~70% of the
            population passes; with 3 ps, ~25%. LMS calibration
            shifts both curves dramatically to the left.
          </li>
        </ul>
      </section>

      <AssumptionBox kind="info">
        Real PVT analysis sweeps process corners systematically (TT /
        SS / FF / SF / FS) and includes temperature + supply
        cross-products. Gaussian Monte Carlo on a few knobs is the
        cheap behavioral analogue.
      </AssumptionBox>

      <AssumptionBox kind="limit">
        We do not yet sweep DCO PN spectrum shape (only its overall
        level). A more rigorous PVT analysis would let the 1/f^3 and
        1/f^2 corners drift independently. Easy follow-up.
      </AssumptionBox>
    </PageLayout>
  );
}
