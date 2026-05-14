import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import PlotViewer from "../components/PlotViewer";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("ext-ntf")!;

export default function ExtNtf() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Why this page exists</h2>
        <p>
          A behavioral simulator is only trustworthy if its output can be
          explained by a closed-form model. We derive the small-signal
          noise-transfer functions for each injected noise source,
          evaluate them on the same frequency grid as the simulated PSD,
          and overlay. Agreement validates the model; disagreement
          flags either a derivation slip, a coding bug, or — in this
          case — a noise source the closed-form doesn&apos;t include.
        </p>
      </section>

      <section>
        <h2>Linearized model</h2>
        <EquationBlock
          tex={String.raw`
            L(s) \;=\; \frac{K_{bb}\,K_{DCO}}{s\,f_{DCO,nom}}\,H_{LF}(s),
            \qquad
            H_{LF}(s) \;=\; K_p \;+\; \frac{K_i}{s\,T_{ref}}
          `}
          caption="Open-loop gain in time-error domain, continuous-time approximation."
        />
        <p>
          The BBPD&apos;s small-signal gain
          <Inline tex="\,K_{bb}=\sqrt{2/\pi}/\sigma\," /> depends on the
          dither <Inline tex="\sigma" /> at its input — itself a function
          of the closed-loop noise we&apos;re trying to model. The
          script measures <Inline tex="\sigma" /> from the simulator
          trace and plugs it in, so the analytic prediction uses the
          right operating point.
        </p>
        <EquationBlock
          tex={String.raw`
            H_{ref}(s) = \frac{L(s)}{1+L(s)},\quad
            H_{dco}(s) = \frac{1}{1+L(s)},\quad
            H_{dtc}(s) = \frac{L(s)}{1+L(s)}
          `}
          caption="Low-pass for any noise source entering at the comparator; high-pass for DCO intrinsic PN."
        />
      </section>

      <section>
        <h2>Inside the code — three contributions</h2>
        <p>
          The whole calculation is plain complex-number arithmetic in
          <code> sim/noise_tf.py</code>. First, the open-loop gain and
          two basic NTFs:
        </p>
        <CodeBlock
          language="python"
          filename="sim/noise_tf.py"
          lineRange="28-48"
          startLine={28}
          code={`def open_loop_gain(f, K_bb, params):
    """L(s) at frequencies f (Hz). Returns complex array."""
    f = np.asarray(f, dtype=float)
    s = 2j * np.pi * np.maximum(f, 1e-9)
    H_LF = params.Kp + params.Ki / (s * params.T_ref)
    return K_bb * params.K_dco * H_LF / (s * params.f_dco_nominal)


def ntf_ref(f, K_bb, params):
    L = open_loop_gain(f, K_bb, params)
    return L / (1.0 + L)


def ntf_dco_pn(f, K_bb, params):
    L = open_loop_gain(f, K_bb, params)
    return 1.0 / (1.0 + L)`}
        />
        <p>
          Then three noise contributions added together: DCO open-loop
          PN through <Inline tex="|H_{dco}|^2" /> (high-pass), reference
          jitter through <Inline tex="|H_{ref}|^2" /> (low-pass), and
          the BBPD-folded quantization noise — also low-pass shaped:
        </p>
        <CodeBlock
          language="python"
          filename="sim/noise_tf.py"
          lineRange="86-99"
          startLine={86}
          code={`# BBPD-folded quantization noise. The detector output has variance
# ~1 (it's ±1 with E[s] = K_bb*e ≈ 0 at lock), spread over the
# one-sided sampling bandwidth f_ref/2. Input-referred PSD in
# seconds^2/Hz is therefore (2 / f_ref) / K_bb^2.
if include_bbpd_noise and K_bb > 0 and np.isfinite(K_bb):
    S_t_bbpd_one = 2.0 / (K_bb ** 2 * f_ref)
    S_phi_bbpd_in = ((2.0 * np.pi * params.f_dco_nominal) ** 2
                     * S_t_bbpd_one)
    S_phi_closed_bbpd = np.abs(H_ref) ** 2 * S_phi_bbpd_in
else:
    S_phi_closed_bbpd = np.zeros_like(f)

S_phi_total = S_phi_closed_dco + S_phi_closed_ref + S_phi_closed_bbpd`}
        />
        <p>
          The BBPD term is the one that closes the gap with the
          simulated PSD. Without it, the analytic prediction sits well
          below the actual noise floor — because in a real BBPD-DPLL
          the in-band floor is dominated by the comparator&apos;s 1-bit
          quantization, not by DCO or reference noise. The standard
          model treats the ±1 output as having unit variance spread over
          the sampling bandwidth, divided by <Inline tex="K_{bb}^2" />
          to refer it to the input.
        </p>
      </section>

      <section>
        <h2>Comparison plot</h2>
        <PlotViewer
          src="/figures/noise_tf.png"
          alt="Top: simulated L(f) vs. analytic closed-loop prediction with BBPD noise included. Bottom: |H_ref| (low-pass) and |H_dco_pn| (high-pass) magnitudes."
          caption="With the BBPD noise term added, the analytic prediction tracks the simulated floor across the band."
        />
      </section>

      <section>
        <h2>How to read the comparison</h2>
        <p>Three things to look for:</p>
        <ul className="ml-6 list-disc space-y-2 text-slate-700">
          <li>
            <strong>The crossover.</strong> The green dotted line marks
            <Inline tex="\,|L(j\omega)|=1\," />. Below it, the loop has
            authority — DCO PN is suppressed, reference jitter passes.
            Above it, the loop has no authority — DCO PN reaches the
            output unchanged, reference jitter is rejected.
          </li>
          <li>
            <strong>The high-pass / low-pass roll-offs in the bottom
            panel.</strong> Slopes around the crossover are set by the
            zero of the PI filter, not by <Inline tex="K_{bb}" />. Drop
            Kp and the slope stays the same; only the crossover moves.
          </li>
          <li>
            <strong>In-band floor.</strong> The flat in-band level is
            set by the BBPD term. Increasing
            <Inline tex="\,K_{bb}\," /> (smaller in-loop dither) pulls
            the floor down by 20 dB per decade of <Inline tex="K_{bb}" />,
            so anything that reduces the dither — better DCO, better
            ref clock, tighter DTC calibration — directly improves the
            in-band PN.
          </li>
        </ul>
      </section>

      <AssumptionBox kind="info" title="What this confirms">
        Three independent quantities (DCO PN, reference jitter, BBPD
        quantization variance) sum to within a few dB of the simulated
        PSD across the whole band. The crossover and slopes are set
        only by the loop filter and <Inline tex="K_{bb}" />. The
        simulator&apos;s loop dynamics are wired correctly.
      </AssumptionBox>

      <AssumptionBox kind="limit" title="What the analytic model still misses">
        Continuous-time approximation breaks down near
        <Inline tex="\,f_{ref}/2\," />: aliased contributions, DSM
        residue leakage past imperfect DTC cancellation, and any
        non-stationary effects during the lock transient are still
        outside this closed-form prediction. The remaining ~2 dB at
        very high offsets is consistent with the first of these.
      </AssumptionBox>
    </PageLayout>
  );
}
