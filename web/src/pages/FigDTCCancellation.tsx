import { figureIndex } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import EquationBlock, { Inline } from "../components/EquationBlock";
import PlotViewer from "../components/PlotViewer";
import AssumptionBox from "../components/AssumptionBox";
import CodeBlock from "../components/CodeBlock";

const meta = figureIndex.find((f) => f.slug === "fig-dtc-cancellation")!;

export default function FigDTCCancellation() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">The problem the DTC solves</h2>
        <p>
          A fractional-N divider can only divide by integers each cycle,
          but the desired ratio
          <Inline tex="\;N_{frac}=N_{int}+\alpha\;" /> is non-integer. The
          delta-sigma modulator hides the fraction by dithering the
          modulus, so the long-term ratio is correct but each individual
          divider edge is displaced from the &quot;ideal&quot; fractional
          position. That displacement is exactly large enough to saturate
          a single-bit phase detector.
        </p>
      </section>

      <section>
        <h2>Quantifying the displacement</h2>
        <p>
          After <Inline tex="k" /> divider edges, the integer divider has
          emitted
        </p>
        <EquationBlock
          tex={String.raw`S_D[k] \;=\; \sum_{j=0}^{k-1}\bigl(N_{int} + m[j]\bigr)`}
        />
        <p>
          DCO cycles, against the &quot;ideal&quot; fractional count of
          <Inline tex="\;k\cdot N_{frac}" />. The accumulated mismatch in
          fractional cycles is
        </p>
        <EquationBlock
          tex={String.raw`e_{dsm}[k] \;=\; k\,\alpha \;-\; \sum_{j=0}^{k-1} m[j]`}
          caption="Tracked explicitly in sim/dsm.py via running sums of α and m."
        />
        <p>
          which translates into a time-domain displacement of the
          <Inline tex="\,k" />-th divider edge of
          <Inline tex="\;-e_{dsm}[k]\cdot T_{DCO}" /> (negative meaning
          earlier than ideal).
        </p>
      </section>

      <section>
        <h2>The cancellation</h2>
        <p>
          We program the DTC to delay the divider edge by exactly that
          amount, so the feedback edge lands where an ideal fractional
          divider would have placed it:
        </p>
        <EquationBlock
          tex={String.raw`
            \tau_{DTC}[k] \;=\; \hat{g}\cdot e_{dsm}[k]\cdot T_{DCO,nom}
          `}
          caption="With ĝ = 1 and matched T_DCO, residue ≈ 0."
        />
        <p>
          When <Inline tex="\hat{g}=1" /> and the DTC is otherwise ideal,
          the BBPD sees only the residual jitter (DCO phase noise,
          reference jitter, DTC quantization), not the multi-hundred-ps
          DSM dither.
        </p>
      </section>

      <section>
        <h2>Inside the code — three pieces</h2>
        <p>
          The cancellation lives in three files. First, the DSM exposes
          the running residue:
        </p>
        <CodeBlock
          language="python"
          filename="sim/dsm.py"
          lineRange="75-79"
          startLine={75}
          code={`# Cumulative residue using running mean (robust to alpha changes)
self._alpha_accum += alpha
self._cum_y += y_out
e_dsm = self._alpha_accum - self._cum_y
return int(y_out), float(e_dsm)`}
        />
        <p>
          Then the top-level loop programs the DTC with that residue,
          scaled by the LMS coefficient <Inline tex="\hat{g}" /> and the
          nominal DCO period:
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
          The DTC itself applies the impairments to that target delay:
        </p>
        <CodeBlock
          language="python"
          filename="sim/dtc.py"
          lineRange="31-39"
          startLine={31}
          code={`def apply(self, tau_target_s):
    tau = (1.0 + self.gain_err) * np.asarray(tau_target_s) + self.offset_s
    if self.inl_amp_s > 0 and self.inl_periods > 0:
        phase = 2.0 * np.pi * self.inl_periods * (
            np.asarray(tau_target_s) / max(self.full_scale_s, 1e-30))
        tau = tau + self.inl_amp_s * np.sin(phase)
        if self.quant_lsb_s > 0:
            tau = np.round(tau / self.quant_lsb_s) * self.quant_lsb_s
        return tau`}
        />
        <p>
          With <code>gain_err = 0</code>, <code>inl_amp_s = 0</code>, and a
          fine <code>quant_lsb_s</code>, <code>tau_dtc</code> equals
          <code> tau_target</code> exactly, and the BBPD sees only the
          residual jitter — sub-picosecond in our default sim.
        </p>
      </section>

      <section>
        <h2>Simulation evidence</h2>
        <PlotViewer
          src="/figures/dtc_cancellation.png"
          alt="Top: BBPD-input error with DTC off (ns scale). Middle: with DTC on (ps scale). Bottom: equivalent DCO phase-noise PSD with vs. without DTC."
          caption="DTC OFF: ~190 ps RMS. DTC ON: ~0.4 ps RMS. ~500× reduction."
        />
      </section>

      <AssumptionBox kind="info">
        The DSM in our model is MASH-1-1-1 (third order). Its output
        residue is bounded in <Inline tex="\pm 2\,T_{DCO}" />, which is
        what the DTC needs to span (plus some margin).
      </AssumptionBox>

      <AssumptionBox kind="limit" title="Where this is a simplification">
        Our DTC has gain error, offset, sinusoidal INL, and uniform
        quantization. Real implementations have INL profiles with multiple
        spatial frequencies, supply-dependent gain drift, and code-skip
        non-monotonicity. None of those are modeled here.
      </AssumptionBox>
    </PageLayout>
  );
}
