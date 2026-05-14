import { figureIndex } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import ModelBlockDiagram from "../components/ModelBlockDiagram";
import EquationBlock, { Inline } from "../components/EquationBlock";
import ParameterTable, { ParameterRow } from "../components/ParameterTable";
import AssumptionBox from "../components/AssumptionBox";
import CodeBlock from "../components/CodeBlock";

const meta = figureIndex.find((f) => f.slug === "fig-architecture")!;

const rows: ParameterRow[] = [
  { symbol: "f_ref",        description: "Reference clock",                     value: "40 MHz",       source: "ESTIMATED", notes: "Paper-stated value not in abstract" },
  { symbol: "f_out",        description: "Output carrier range",                value: "2.92–4.05 GHz", source: "PAPER" },
  { symbol: "N_frac",       description: "f_out / f_ref",                       value: "≈ 73 – 101",    source: "DERIVED" },
  { symbol: "process",      description: "Technology",                          value: "65 nm CMOS",   source: "PAPER" },
  { symbol: "DCO step",     description: "Frequency resolution",                value: "70 Hz",        source: "PAPER", notes: "Implies coarse-bank + fine dithered DCO" },
  { symbol: "P",            description: "Total power",                         value: "4.5 mW",       source: "PAPER" },
];

export default function FigArchitecture() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">What this page is about</h2>
        <p>
          The architecture takes a low-resolution phase detector (a single
          flip-flop) and uses a digital-to-time converter on the feedback
          edge to make the detector see (nearly) zero phase error at lock.
          Without the DTC, the integer divider modulus jumps every cycle
          under the delta-sigma modulator&apos;s control, generating a
          large pseudo-random time error that a 1-bit detector cannot
          resolve. With the DTC, that time error is cancelled in the
          digital domain before the comparator looks at it.
        </p>
      </section>

      <section>
        <h2>Block diagram</h2>
        <ModelBlockDiagram />
      </section>

      <section>
        <h2>What each block does</h2>
        <ul className="ml-6 list-disc space-y-2 text-slate-700">
          <li>
            <strong>Reference</strong> — a low-jitter crystal at <Inline tex="f_{ref}" />.
            Modeled as a deterministic edge schedule plus white jitter.
          </li>
          <li>
            <strong>MMD (multi-modulus divider)</strong> — divides the DCO
            by <Inline tex="N_{int} + m[k]" />, where <Inline tex="m[k]" />
            is an integer dither sequence whose long-term mean equals the
            fractional part <Inline tex="\alpha" />.
          </li>
          <li>
            <strong>DSM</strong> — MASH-1-1-1 (3rd-order), generates
            <Inline tex="\,m[k]" /> and exposes the cumulative residue
            <Inline tex="\;e_{dsm}[k]" /> in fractional DCO cycles.
          </li>
          <li>
            <strong>DTC</strong> — applies a programmable delay
            <Inline tex="\;\tau_{DTC}=\hat{g}\cdot e_{dsm}[k]\cdot T_{DCO}\;" />
            to the feedback edge so the BBPD sees only the residual.
          </li>
          <li>
            <strong>BBPD</strong> — outputs <Inline tex="\pm 1" /> per
            reference cycle based on edge order.
          </li>
          <li>
            <strong>Digital loop filter</strong> — discrete PI; sets loop
            BW and phase margin.
          </li>
          <li>
            <strong>DCO</strong> — linearised: <Inline tex="f_{DCO}=f_0 + K_{DCO}\cdot u" />.
          </li>
        </ul>
      </section>

      <section>
        <h2>Sign-convention summary</h2>
        <EquationBlock
          tex={String.raw`
            e_{bbpd}[k] \;=\; t_{div,eff}[k] \;-\; t_{ref}[k]
            \quad\text{(seconds, +ve = feedback late)}
          `}
          caption="Convention used everywhere in sim/ and on this site."
        />
        <p>
          With this convention, a positive <Inline tex="e_{bbpd}" /> tells
          the loop the DCO is too slow, which raises <Inline tex="u" />
          and speeds the DCO up.
        </p>
      </section>

      <section>
        <h2>Known parameters (this page)</h2>
        <ParameterTable rows={rows} />
      </section>

      <section>
        <h2>Inside the code — top-level loop</h2>
        <p>
          The architecture in the diagram corresponds 1-to-1 with the body
          of <code>run_simulation()</code> in <code>sim/pll_model.py</code>.
          Each numbered comment maps onto one block in the diagram.
        </p>
        <CodeBlock
          language="python"
          filename="sim/pll_model.py"
          lineRange="147-186"
          startLine={147}
          code={`for k in range(n):
    # 1) Reference edge
    t_ref_k = (k + 1) * T_ref + ref_jitter[k]

    # 2) DSM step (modulus + cumulative residue for DTC)
    m_k, e_dsm_k = dsm.step(alpha)
    D_k = fdiv.cycles(m_k)

    # 3) DCO advance; add phase noise (radians -> seconds)
    f_dco_k = dco.frequency(u)
    dt_pn = phi_dco_excess[k] * inv_2pi_f_dco_nom
    t_div_k = t_div_prev + D_k / f_dco_k + dt_pn

    # 4) DTC delay (cancels DSM residue; g_hat is the LMS coef)
    tau_target = g_hat * e_dsm_k * params.T_dco_nominal if enable_dtc else 0.0
    tau_dtc_k = float(dtc.apply(tau_target))
    t_div_eff_k = t_div_k + tau_dtc_k

    # 5) BBPD
    e_k = t_div_eff_k - t_ref_k
    s_k = bbpd.decide(e_k)

    # 6) LMS update (optional)
    if enable_lms:
        g_hat = g_hat - lms_mu * s_k * e_dsm_k

    # 7) Loop filter
    u = lpf.step(s_k)`}
        />
        <p>
          <strong>Why one sample per <Inline tex="T_{ref}" />?</strong>
          Every digital event in the hardware happens at the reference
          edge: BBPD samples, loop filter updates, DSM emits, DTC
          re-programs. Sampling at <Inline tex="f_{ref}" /> captures
          everything the loop reacts to and avoids ns-resolution
          oscillator simulation (which would need ~10⁹ samples for the
          same noise band).
        </p>
        <p>
          <strong>Why <code>(k + 1) * T_ref</code> on line 1?</strong> The
          divider and the reference start aligned at <Inline tex="t = 0" />,
          so the <em>first</em> divider edge falls near
          <Inline tex="\,T_{ref}\," />, not at zero. Indexing from
          <Inline tex="\,k+1\," /> removes a constant 25 ns bias that
          would otherwise saturate the BBPD and prevent lock.
        </p>
      </section>

      <AssumptionBox kind="info">
        We do not yet read <Inline tex="f_{ref}" /> from the paper — 40 MHz
        is a likely choice for that era of crystal-based references.
      </AssumptionBox>

      <AssumptionBox kind="limit">
        The DCO is modeled as a continuous frequency-controlled phase
        accumulator with linear K_DCO. The real chip splits its tuning
        into a coarse capacitor bank plus a high-resolution dithered fine
        branch to reach the stated 70 Hz step, which we do not model.
      </AssumptionBox>
    </PageLayout>
  );
}
