import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("mod-loop-filter")!;

export default function ModLoopFilter() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Purpose</h2>
        <p>
          Convert the BBPD&apos;s ±1 sequence into a DCO tuning word with
          a discrete-time proportional-integral law. PI is the textbook
          choice for Type-II loop response: infinite DC gain (zero
          steady-state phase error) plus a high-frequency zero for phase
          margin.
        </p>
      </section>

      <section>
        <h2>The whole file</h2>
        <CodeBlock
          language="python"
          filename="sim/loop_filter.py"
          lineRange="1-24"
          startLine={1}
          code={`"""Digital PI loop filter.

Input  : BBPD output s[k] in {-1, +1} (or any small integer).
Output : DCO tuning word u[k] = u_init + Kp*s[k] + Ki*sum(s).

The integral accumulator is updated before the output, so the filter
is causal and has unity-delay-free path from input to output.
"""

class DigitalPI:
    def __init__(self, Kp: float, Ki: float, u_init: float = 0.0):
        self.Kp = float(Kp)
        self.Ki = float(Ki)
        self.u_init = float(u_init)
        self.integ = 0.0

    def reset(self, u_init: float = None):
        self.integ = 0.0
        if u_init is not None:
            self.u_init = float(u_init)

    def step(self, s_k: float) -> float:
        self.integ += s_k
        return self.u_init + self.Kp * s_k + self.Ki * self.integ`}
        />
      </section>

      <section>
        <h2>Transfer function</h2>
        <EquationBlock
          tex={String.raw`
            H_{LF}(z) \;=\; K_p \;+\; \frac{K_i}{1 - z^{-1}}
          `}
          caption="The integrator gives Type-II behavior; Kp adds a zero for phase margin."
        />
        <p>
          The zero from the PI sits at
          <Inline tex="\,\omega_z = K_i/(K_p T_{ref})\," />, normally
          placed ~one decade below the unity-gain crossover. With our
          defaults <Inline tex="K_p=8, K_i=0.5" /> and
          <Inline tex="T_{ref}=25\,\mathrm{ns}" />, that&apos;s
          <Inline tex="\,\omega_z/(2\pi)\approx 400\,\mathrm{kHz}\," />.
        </p>
      </section>

      <section>
        <h2>Why <code>integ += s_k</code> runs <em>before</em> the output line</h2>
        <p>
          If we updated the integrator <em>after</em> producing
          <code> u[k] </code>, the integral path would have an extra
          one-sample delay. That delay isn&apos;t fatal but it changes
          the loop&apos;s phase margin in a non-obvious way. The
          early-update form gives the cleanest mapping to the
          <Inline tex="K_i/(1-z^{-1})" /> transfer function above — what
          you derive on paper is what the code computes.
        </p>
      </section>

      <section>
        <h2>Why <code>reset()</code> exists</h2>
        <p>
          The Streamlit GUI re-runs the simulator on every parameter
          change, but caches a single <code>DigitalPI</code> object via
          <code> @st.cache_data</code>. <code>reset()</code> lets the
          cached object start fresh without re-instantiation, which keeps
          the cache key stable.
        </p>
      </section>

      <AssumptionBox kind="info">
        See the Lock-transient page for empirical tuning of Kp/Ki; the
        analytic NTF page derives how these gains shape the closed-loop
        noise response.
      </AssumptionBox>
    </PageLayout>
  );
}
