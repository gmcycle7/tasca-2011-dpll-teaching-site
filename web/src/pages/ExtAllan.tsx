import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import PlotViewer from "../components/PlotViewer";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("ext-allan")!;

export default function ExtAllan() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Allan deviation — what does it tell you?</h2>
        <p>
          L(f) reports the carrier&apos;s spectrum; Allan deviation
          <Inline tex="\,\sigma_y(\tau)\," /> reports its stability over
          time. The same closed-loop output, plotted two different
          ways. ADEV is what oscillator data sheets, OCXO suppliers
          and GNSS designers actually quote, because the slope of
          <Inline tex="\,\sigma_y(\tau)\," /> directly identifies the
          dominant noise mechanism at each averaging time τ.
        </p>
      </section>

      <section>
        <h2>Overlapping ADEV from divider-edge timestamps</h2>
        <EquationBlock
          tex={String.raw`
            \sigma_y^2(\tau) \;=\; \frac{1}{2(N{-}2m)\,\tau^2}\,
              \sum_{i=0}^{N-2m-1}\bigl(x_{i+2m} - 2 x_{i+m} + x_i\bigr)^2
          `}
          caption="x[k] is the cumulative phase; τ = m·τ₀ with τ₀ = T_ref."
        />
        <p>
          The simulator already emits <code>t_div_eff[k]</code> for
          every reference cycle, so the natural input to
          <Inline tex="\,\sigma_y(\tau)\," /> is just{" "}
          <code>np.diff(t_div_eff) / T_ref</code> — fractional
          frequency per cycle.
        </p>
      </section>

      <section>
        <h2>Inside the code</h2>
        <CodeBlock
          language="python"
          filename="sim/allan.py"
          lineRange="22-52"
          startLine={22}
          code={`def fractional_frequency_from_edges(t_edges_s, t_nominal_s):
    t = np.asarray(t_edges_s, dtype=float)
    T = np.diff(t)
    return (T - t_nominal_s) / t_nominal_s


def overlapping_adev(y, tau0_s, m_values=None):
    N = y.size
    x = np.concatenate(([0.0], np.cumsum(y) * tau0_s))   # phase samples
    if m_values is None:
        m_values = np.unique(np.round(
            np.geomspace(1, max(2, N // 4), 30)).astype(int))
    tau_arr, adev_arr = [], []
    for m in m_values:
        if m < 1 or 2 * m >= N: continue
        d = x[2 * m:] - 2 * x[m:-m] + x[: -2 * m]
        var = np.mean(d ** 2) / (2.0 * (m * tau0_s) ** 2)
        tau_arr.append(m * tau0_s)
        adev_arr.append(float(np.sqrt(var)))
    return np.asarray(tau_arr), np.asarray(adev_arr)`}
        />
        <p>
          Why <em>overlapping</em> ADEV instead of non-overlapping?
          For the same data length you get many more samples per τ,
          so the estimate has tighter confidence — exactly what we
          want for short simulator runs.
        </p>
      </section>

      <section>
        <h2>Reading the slope</h2>
        <p>The classical noise-type slopes:</p>
        <ul className="ml-6 list-disc space-y-1 text-slate-700 dark:text-slate-300">
          <li>
            White phase modulation (PM)  ⇒ <Inline tex="\,\sigma_y \propto \tau^{-1}\,." />
          </li>
          <li>
            White frequency modulation (FM)  ⇒ <Inline tex="\,\sigma_y \propto \tau^{-1/2}\,." />
          </li>
          <li>
            Flicker FM  ⇒ <Inline tex="\,\sigma_y \propto \tau^{0}\,." />
          </li>
          <li>
            Random-walk FM  ⇒ <Inline tex="\,\sigma_y \propto \tau^{+1/2}\,." />
          </li>
        </ul>
        <p>
          The plot below overlays these slope guides so you can read
          off the noise type that dominates at each τ.
        </p>
      </section>

      <section>
        <h2>Result</h2>
        <PlotViewer
          src="/figures/allan.png"
          alt="Three panels: ADEV, ADEV with slope guides, and ADEV for three loop bandwidths."
          caption="Minimum ADEV ~ 8e-10 around τ ≈ 1 ms in our default setup. Larger loop BW pushes the white-FM region farther right (loop attenuates the DCO PN earlier in τ)."
        />
      </section>

      <AssumptionBox kind="info">
        Allan deviation lives in the time domain — it&apos;s the
        natural complement to L(f). If you ever need to compare with
        an oscillator data sheet or with a GNSS-time-transfer paper,
        this is the metric they will quote.
      </AssumptionBox>
    </PageLayout>
  );
}
