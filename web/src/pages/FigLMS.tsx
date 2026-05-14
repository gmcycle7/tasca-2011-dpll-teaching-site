import { figureIndex } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import EquationBlock, { Inline } from "../components/EquationBlock";
import PlotViewer from "../components/PlotViewer";
import AssumptionBox from "../components/AssumptionBox";
import CodeBlock from "../components/CodeBlock";

const meta = figureIndex.find((f) => f.slug === "fig-lms")!;

export default function FigLMS() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">The problem in one line</h2>
        <p>
          The DTC&apos;s physical delay-per-LSB is set by analog things
          (capacitor sizes, bias currents, supply, temperature) and so its
          actual gain drifts. If we drive the DTC with a digital code that
          assumes a fixed gain, cancellation goes incomplete and fractional
          spurs come back. The LMS loop fixes that without ever measuring
          the analog gain directly.
        </p>
      </section>

      <section>
        <h2>Where ĝ sits in the signal flow</h2>
        <p>
          We pre-scale the DSM residue by an adaptive coefficient
          <Inline tex="\,\hat{g}\," /> before sending it to the DTC. The
          analog DTC then applies its own (unknown, mismatched) gain
          <Inline tex="\,(1+g_{err})" />:
        </p>
        <EquationBlock
          tex={String.raw`
            \tau_{actual}
              \;=\; (1 + g_{err})\;\hat{g}\;e_{dsm}[k]\;T_{DCO,nom}.
          `}
        />
        <p>
          For perfect cancellation we need
          <Inline tex="\,(1+g_{err})\,\hat{g}=1" />, so
          <Inline tex="\,\hat{g}^* = 1/(1+g_{err})" />. The LMS loop has to
          find that value from BBPD output alone.
        </p>
      </section>

      <section>
        <h2>The update rule</h2>
        <EquationBlock
          tex={String.raw`
            \hat{g}[k+1] \;=\; \hat{g}[k]
              \;-\; \mu\;s_{bbpd}[k]\;e_{dsm}[k]
          `}
          caption="Sign-data LMS: BBPD gives the sign (only thing we have), DSM residue gives the magnitude (digital, known)."
        />
        <p>
          Why this works: when <Inline tex="\hat{g}" /> is too large, the
          DTC over-delays and a positive <Inline tex="e_{dsm}" /> generates
          a positive BBPD output, so the product
          <Inline tex="\,s\!\cdot\!e_{dsm}\," /> has a positive mean and
          the rule drives <Inline tex="\hat{g}" /> down. By symmetry it
          drives <Inline tex="\hat{g}" /> up when too small. At
          <Inline tex="\,\hat{g}=\hat{g}^*" /> the correlation between
          <Inline tex="\,s\," /> and <Inline tex="\,e_{dsm}\," /> vanishes
          and the adaptation halts (in expectation).
        </p>
      </section>

      <section>
        <h2>Why it doesn&apos;t fight the main loop</h2>
        <p>
          The main PLL drives <Inline tex="\,\mathbb{E}[s_{bbpd}]\!\to\!0" />.
          The LMS drives the correlation
          <Inline tex="\,\mathbb{E}[s_{bbpd}\!\cdot\!e_{dsm}]\!\to\!0" />.
          Because the DSM residue is itself zero-mean (it is shaped
          quantization noise), these two error metrics are orthogonal, so
          both loops can run simultaneously without coupling.
        </p>
      </section>

      <section>
        <h2>Simulation</h2>
        <PlotViewer
          src="/figures/lms_calibration.png"
          alt="Top: ĝ trajectory vs. time, with target 1/(1+gain_err)=0.909. Middle: rolling BBPD RMS error. Bottom: steady-state phase-noise PSD with LMS on vs. off."
          caption="With g_err=0.1, μ=1e-4: ĝ → 0.9092 (target 0.9091) in ~50 µs; BBPD tail RMS drops from ~20 ps to ~0.5 ps; the spur comb collapses."
        />
      </section>

      <section>
        <h2>Inside the code — three intersecting pieces</h2>
        <p>
          The calibration touches three layers of the simulator. First,
          the DTC drive uses <code>g_hat</code> as a multiplier:
        </p>
        <CodeBlock
          language="python"
          filename="sim/pll_model.py"
          lineRange="161-167"
          startLine={161}
          code={`# 4) DTC delay. The DSM residue is pre-scaled by the LMS-adapted
#    coefficient g_hat; in steady state g_hat -> 1/(1 + gain_err).
tau_target = g_hat * e_dsm_k * params.T_dco_nominal if enable_dtc else 0.0
tau_dtc_k = float(dtc.apply(tau_target))
t_div_eff_k = t_div_k + tau_dtc_k`}
        />
        <p>
          Second, after the BBPD decides but before the loop filter
          runs, <code>g_hat</code> updates with the BBPD output and the
          DSM residue that drove this cycle:
        </p>
        <CodeBlock
          language="python"
          filename="sim/pll_model.py"
          lineRange="170-182"
          startLine={170}
          code={`# 5) BBPD
e_k = t_div_eff_k - t_ref_k
s_k = bbpd.decide(e_k)

# 6) LMS update of DTC gain coefficient (before loop filter so
#    g_hat[k] is the value used at step k).
if enable_lms:
    g_hat = g_hat - lms_mu * s_k * e_dsm_k

# 7) Loop filter -> new DCO control word
u = lpf.step(s_k)`}
        />
        <p>
          Third, the defaults live in <code>PLLParams</code> alongside
          the convergence-target comment, so future readers don&apos;t
          have to re-derive it from the code:
        </p>
        <CodeBlock
          language="python"
          filename="sim/pll_params.py"
          lineRange="49-56"
          startLine={49}
          code={`# ----- LMS adaptive DTC gain calibration -----
# When enabled in run_simulation, the digital-side DTC drive is scaled
# by an adaptive coefficient g_hat updated as
#   g_hat[k+1] = g_hat[k] - mu * s_bbpd[k] * e_dsm[k]
# which drives g_hat toward 1/(1 + dtc_gain_err) to null the residual
# correlation between BBPD output and DSM residue.
lms_mu: float = 1e-4                 # ESTIMATED; demo-friendly step
lms_g_hat_init: float = 1.0          # start from "I think the gain is right"`}
        />
        <p>
          With <code>mu = 1e-4</code> and a 10% gain error, convergence
          takes about 50 µs of simulated time — fast enough to read off
          a single transient plot.
        </p>
      </section>

      <AssumptionBox kind="info">
        We use the full <Inline tex="\,e_{dsm}\," /> magnitude in the LMS
        product. A more hardware-realistic variant truncates it to a few
        MSBs to save a multiplier; that converges a bit more slowly and
        has slightly higher steady-state misadjustment, but the principle
        is identical.
      </AssumptionBox>

      <AssumptionBox kind="limit">
        Only the DTC <em>gain</em> is calibrated. Time-varying offset and
        INL drift would need a separate calibration loop with a different
        regressor. That is a natural extension but not yet implemented.
      </AssumptionBox>
    </PageLayout>
  );
}
