import { figureIndex } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import EquationBlock, { Inline } from "../components/EquationBlock";
import PlotViewer from "../components/PlotViewer";
import ParameterTable, { ParameterRow } from "../components/ParameterTable";
import AssumptionBox from "../components/AssumptionBox";
import CodeBlock from "../components/CodeBlock";

const meta = figureIndex.find((f) => f.slug === "fig-lock-transient")!;

const rows: ParameterRow[] = [
  { symbol: "Kp",    description: "Proportional gain",  value: "8.0",      source: "ESTIMATED", notes: "Picked empirically; not paper-stated" },
  { symbol: "Ki",    description: "Integral gain",      value: "0.5",      source: "ESTIMATED", notes: "Faster pull-in than the small-signal calc suggests" },
  { symbol: "K_dco", description: "DCO LSB",            value: "10 kHz",   source: "ESTIMATED", notes: "Real chip's 70 Hz step is much finer" },
  { symbol: "Δf₀",   description: "Initial offset",     value: "2 MHz",    source: "ESTIMATED", notes: "Test stimulus" },
];

export default function FigLockTransient() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">What we&apos;re testing</h2>
        <p>
          We start the DCO 2 MHz away from the target carrier and let the
          digital PI loop pull it in. Because the loop is Type-II
          (integrator in the filter), the steady-state phase error is
          zero, and the steady-state frequency offset is also zero — the
          integrator holds the right DCO code indefinitely.
        </p>
      </section>

      <section>
        <h2>Continuous-time small-signal model</h2>
        <p>
          Linearizing the BBPD (see the BBPD page) and the divider, the
          loop gain at low frequency reduces to
        </p>
        <EquationBlock
          tex={String.raw`
            L(s) \;\approx\; K_{bb}\;\frac{K_p\,s + K_i/T_{ref}}{s^2}\;
                  \frac{K_{DCO}}{f_{DCO,nom}}
          `}
          caption="Two integrators (filter's I path + DCO's frequency→phase integration) ⇒ Type-II."
        />
        <p>
          The unity-gain crossover and the zero from the PI filter
          determine bandwidth and phase margin. With our defaults the
          ringdown is ~150 µs, visible in the plot below.
        </p>
      </section>

      <section>
        <h2>Simulation</h2>
        <PlotViewer
          src="/figures/core_lock_test.png"
          alt="DCO frequency error, tuning word, and BBPD-input error vs. time for a 2 MHz initial offset."
          caption="Top: f_DCO − target. Middle: u settles at ≈200 LSB ↔ +2 MHz pulled. Bottom: BBPD error decays into ps-scale hunting."
        />
      </section>

      <section>
        <h2>Numbers we used</h2>
        <ParameterTable rows={rows} />
      </section>

      <section>
        <h2>Inside the code — the PI loop filter</h2>
        <p>
          The full implementation of the discrete-time PI controller is
          ten executable lines:
        </p>
        <CodeBlock
          language="python"
          filename="sim/loop_filter.py"
          lineRange="10-24"
          startLine={10}
          code={`class DigitalPI:
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
        <p>
          The integrator updates <em>before</em> the output line so that
          the value used at cycle <Inline tex="k" /> already includes
          <Inline tex="\,s[k]\," />. This matches the textbook
          <Inline tex="\;K_i/(1-z^{-1})\;" /> exactly — no surprise unit
          delay.
        </p>
      </section>

      <section>
        <h2>How the lock test sets up the initial frequency error</h2>
        <CodeBlock
          language="python"
          filename="scripts/run_core_lock_test.py"
          lineRange="29-35"
          startLine={29}
          code={`p = PLLParams(n_cycles=args.n_cycles)
# Force an initial frequency error by shifting f_dco_nominal so the
# zero-tuning DCO sits args.df_init_hz away from the desired carrier.
p.f_dco_nominal = p.f_out_target - args.df_init_hz
# Disable DCO and reference phase noise to make the lock transient easy
# to read; DSM dither and DTC cancellation are on.
res = run_simulation(p, enable_dtc=True,
                     enable_dco_pn=False, enable_ref_noise=False)`}
        />
        <p>
          We perturb <code>f_dco_nominal</code> rather than
          <code> u_init </code> so that the BBPD&apos;s first non-zero
          decision happens organically: with <code>u_init = 0</code> the
          DCO sits at its nominal, which is now 2 MHz below target, the
          divider edges accumulate lag, BBPD reports +1, and the PI
          integrator winds up from there.
        </p>
      </section>

      <AssumptionBox kind="info">
        We use Kp=8, Ki=0.5 to keep the transient short for the demo.
        Lowering Ki to ≈0.02 (closer to the small-signal-optimum for
        steady-state hunting) gives smaller tail RMS but much slower
        pull-in.
      </AssumptionBox>

      <AssumptionBox kind="limit">
        We do not yet model the coarse capacitor bank that would normally
        do a discrete frequency hop into the right sub-range before the
        fine loop takes over.
      </AssumptionBox>
    </PageLayout>
  );
}
