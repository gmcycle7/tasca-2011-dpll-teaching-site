import { figureIndex } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import EquationBlock, { Inline } from "../components/EquationBlock";
import PlotViewer from "../components/PlotViewer";
import AssumptionBox from "../components/AssumptionBox";
import CodeBlock from "../components/CodeBlock";

const meta = figureIndex.find((f) => f.slug === "fig-frac-spur")!;

export default function FigFracSpur() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Why fractional spurs exist</h2>
        <p>
          A fractional-N synthesizer with fractional part
          <Inline tex="\,\alpha\," /> has a residual time-domain pattern at
          the divider output that is quasi-periodic with period
          <Inline tex="\,1/\alpha\," /> reference cycles. Its Fourier
          content is a comb of tones at multiples of
          <Inline tex="\,\alpha\,f_{ref}\," />, folded back into the
          baseband:
        </p>
        <EquationBlock
          tex={String.raw`
            f_{spur,k} \;=\; \bigl((k\,\alpha)\bmod 1\bigr)\,f_{ref},
            \qquad k = 1, 2, 3, \dots
          `}
          caption="Predicted by sim/spurs.py and used to set our peak-picker windows."
        />
      </section>

      <section>
        <h2>Why the DTC normally hides them</h2>
        <p>
          When the DTC is ideal (<Inline tex="\hat{g}=1" />, no INL, no
          gain drift), the time-domain pattern is fully cancelled, and
          there is nothing left for the comb to act on — the spurs
          disappear into the noise floor.
        </p>
        <p>
          When the DTC has impairments, the cancellation residual is itself
          quasi-periodic with the same fundamental
          <Inline tex="\,\alpha\,f_{ref}\," />, and the comb reappears.
          Two common offenders:
        </p>
        <ul className="ml-6 list-disc space-y-2 text-slate-700">
          <li>
            <strong>Gain error.</strong> A residual of
            <Inline tex="\,(1 - (1+g_{err})\hat{g})\,e_{dsm}[k]\,T_{DCO}\;" />
            is left at the BBPD input, proportional to the DSM residue.
            The first-harmonic spur dominates.
          </li>
          <li>
            <strong>INL ripple.</strong> A periodic distortion in the
            code-to-delay map injects power at multiples of the INL
            spatial frequency mapped through the DSM residue, producing
            spurs at multiple <Inline tex="\,k\alpha f_{ref}\," /> with
            slow roll-off.
          </li>
        </ul>
      </section>

      <section>
        <h2>Inside the code — predict the comb, then search</h2>
        <p>
          The spur locations are pure arithmetic in
          <code> sim/spurs.py</code>:
        </p>
        <CodeBlock
          language="python"
          filename="sim/spurs.py"
          lineRange="15-22"
          startLine={15}
          code={`def predicted_spur_offsets(alpha, f_ref, n_harmonics=12):
    out = []
    for k in range(1, n_harmonics + 1):
        f = ((k * alpha) % 1.0) * f_ref
        if f > 0:
            out.append((k, f))
    return out`}
        />
        <p>
          And the impairments that bring them out are configured per
          DTC instance:
        </p>
        <CodeBlock
          language="python"
          filename="scripts/run_fractional_spur_demo.py"
          lineRange="39-43"
          startLine={39}
          code={`# Case A: imperfect DTC (gain error + INL) -> spurs prominent
p_bad = PLLParams(n_cycles=args.n_cycles, f_ref=f_ref, f_out_target=f_out,
                  f_dco_nominal=f_out,
                  dtc_gain_err=0.1, dtc_inl_amp_s=2e-12, dtc_inl_periods=8)`}
        />
        <p>
          The 10% gain error leaves residual proportional to
          <Inline tex="\;e_{dsm}[k]\;" /> at the BBPD input — periodic
          with the DSM sequence, so it appears as a comb. The 2 ps
          sinusoidal INL adds harmonics to that comb. With either knob
          set to zero the comb collapses into the noise floor.
        </p>
      </section>

      <section>
        <h2>Simulated comparison</h2>
        <PlotViewer
          src="/figures/fractional_spurs.png"
          alt="L(f) with impaired DTC vs. ideal DTC. Vertical guides at predicted k·α·f_ref offsets, with k labels."
          caption="α=0.01 → first spur at 400 kHz. With 10% gain error + 2 ps INL the spur comb is clearly visible; with ideal DTC it disappears into the noise floor."
        />
      </section>

      <section>
        <h2>Worst-case in-band number</h2>
        <p>
          The paper reports a worst-case in-band fractional spur of
          <strong> −42 dBc</strong>. Our simulator produces a comparable
          number only when we deliberately impair the DTC; with an ideal
          DTC the simulated comb falls below the noise floor and the
          peak-picker has nothing to grab.
        </p>
      </section>

      <AssumptionBox kind="info">
        The INL model is a single-frequency sinusoid. Real INL has multiple
        spatial frequencies and a code-dependent shape; that maps to a
        wider, more complex spur skirt that we do not reproduce.
      </AssumptionBox>

      <AssumptionBox kind="limit">
        Reference spurs (at <Inline tex="\,f_{ref}\," /> and its harmonics)
        are not separately modeled. In a real chip they leak through
        supply / substrate coupling, which is outside our behavioral scope.
      </AssumptionBox>
    </PageLayout>
  );
}
