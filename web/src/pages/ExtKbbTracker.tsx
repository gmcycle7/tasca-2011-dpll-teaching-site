import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import PlotViewer from "../components/PlotViewer";
import EquationBlock, { Inline } from "../components/EquationBlock";
import CodeBlock from "../components/CodeBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("ext-kbb-tracker")!;

export default function ExtKbbTracker() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Why K_bb tracking matters</h2>
        <p>
          The BBPD&apos;s linearised gain
          <Inline tex="\,K_{bb}=\sqrt{2/\pi}/\sigma\," /> is set by the
          dither the comparator sees, which itself depends on PVT
          drift, supply, temperature. As <Inline tex="\sigma" /> moves,
          loop bandwidth moves with it. A real chip wants a separate
          slow loop that <em>tracks</em> <Inline tex="\sigma" /> and
          adjusts Kp/Ki so the closed-loop dynamics stay on spec.
        </p>
      </section>

      <section>
        <h2>Two on-chip estimators</h2>
        <EquationBlock
          tex={String.raw`
            \hat{\sigma}[k] \;=\; \mathrm{stdev}\!\bigl(e_{bbpd}[k-W..k]\bigr)
            \quad\Rightarrow\quad
            \hat{K}_{bb}[k] \;=\; \frac{\sqrt{2/\pi}}{\hat{\sigma}[k]}
          `}
          caption="Method 1 — measure σ in a rolling window of W cycles."
        />
        <EquationBlock
          tex={String.raw`
            \rho_{flip}[k] \;=\; \frac{1}{W}\sum_{j=k-W}^{k-1}\mathbb{1}\bigl[s[j]\neq s[j-1]\bigr]
          `}
          caption="Method 2 — switching density: a fully-1-bit estimator that the comparator output already gives you for free."
        />
        <p>
          Method 1 needs analog access to the comparator input.
          Method 2 works entirely from the ±1 BBPD output, so it&apos;s
          what real implementations actually use (Bertulessi et
          al., 2020). Both proxy <Inline tex="\sigma" /> and let a
          slow LMS scale the gain accordingly.
        </p>
      </section>

      <section>
        <h2>Inside the post-processing</h2>
        <CodeBlock
          language="python"
          filename="scripts/run_kbb_tracker.py"
          lineRange="42-58"
          startLine={42}
          code={`window = 2000   # cycles
sigma_t = np.empty(n); sigma_t.fill(np.nan)
for k in range(window, n):
    tail = res.e_bbpd[k - window:k]
    sigma_t[k] = float(np.std(tail - tail.mean()))
K_bb_t = np.sqrt(2.0 / np.pi) / np.maximum(sigma_t, 1e-15)

# Switching-density proxy: fraction of sign flips per window
s_arr = np.sign(res.e_bbpd).astype(int)
flips = (s_arr[1:] != s_arr[:-1]).astype(int)
flip_density = np.empty(n - 1); flip_density.fill(np.nan)
for k in range(window, n - 1):
    flip_density[k] = flips[k - window:k].mean()`}
        />
      </section>

      <section>
        <h2>Result</h2>
        <PlotViewer
          src="/figures/kbb_tracker.png"
          alt="Top: rolling σ and K_bb. Bottom: sign-flip density."
          caption="Steady-state σ ≈ 0.51 ps, K_bb ≈ 1.6e12 s⁻¹. Both estimators track each other; the switching-density proxy needs no analog access."
        />
      </section>

      <AssumptionBox kind="info">
        This page is a post-processing demo: we read σ off a recorded
        BBPD-input trace. A production tracker would run online,
        keeping a single-pole IIR estimate of σ from the switching
        density and feeding it to a slow LMS that adjusts Kp/Ki.
        Hooking that into <code>sim/pll_model.py</code> is a natural
        next step.
      </AssumptionBox>

      <AssumptionBox kind="limit">
        We do not yet close the second loop — Kp/Ki are static. So
        the present demo shows the σ → K_bb measurement, not the loop
        that uses it.
      </AssumptionBox>
    </PageLayout>
  );
}
