import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("mod-jitter-spurs")!;

export default function ModJitterSpurs() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Two small files, one job each</h2>
        <p>
          <code>sim/jitter.py</code> integrates
          <Inline tex="\,\mathcal{L}(f)\," /> into RMS time jitter.
          <code> sim/spurs.py </code> locates the predicted fractional-spur
          comb in a measured PSD. Each is short enough to read whole.
        </p>
      </section>

      <section>
        <h2>jitter.py — band-limited integration</h2>
        <CodeBlock
          language="python"
          filename="sim/jitter.py"
          lineRange="9-26"
          startLine={9}
          code={`def integrated_phase_variance(f, L_dbchz, f_lo, f_hi) -> float:
    f = np.asarray(f, float)
    L_dbchz = np.asarray(L_dbchz, float)
    m = (f >= f_lo) & (f <= f_hi) & np.isfinite(L_dbchz)
    if m.sum() < 2:
        return float("nan")
    L_lin = 10.0 ** (L_dbchz[m] / 10.0)
    # numpy>=2.0 renamed trapz -> trapezoid
    trapezoid = getattr(np, "trapezoid", None) or np.trapz
    return float(2.0 * trapezoid(L_lin, f[m]))

def integrated_rms_jitter_s(f, L_dbchz, f_lo, f_hi, f_carrier) -> float:
    var_phi = integrated_phase_variance(f, L_dbchz, f_lo, f_hi)
    if not np.isfinite(var_phi) or var_phi < 0:
        return float("nan")
    return float(np.sqrt(var_phi) / (2.0 * np.pi * f_carrier))`}
        />
        <p>
          <strong>The two-step structure (variance, then jitter) is on
          purpose.</strong> &quot;Total integrated phase variance over a
          band&quot; is itself a useful quantity (used for SNR
          calculations), so we expose it. The jitter-in-seconds is just
          the variance divided by the carrier&apos;s rad-to-second
          conversion.
        </p>
        <EquationBlock
          tex={String.raw`
            \sigma_t \;=\; \frac{\sqrt{\,2\!\int_{f_{lo}}^{f_{hi}}\!\mathcal{L}(f)\,df\,}}{2\pi\,f_{out}}
          `}
        />
        <p>
          The factor of 2 inside the square root is the &quot;both
          sidebands&quot; correction — phase noise integrates over both
          positive and negative offset frequencies, and
          <Inline tex="\,\mathcal{L}(f)\," /> is single-sideband.
        </p>
      </section>

      <section>
        <h2>spurs.py — predicting + locating</h2>
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
        <CodeBlock
          language="python"
          filename="sim/spurs.py"
          lineRange="25-47"
          startLine={25}
          code={`def detect_spurs(f, L_dbchz, alpha, f_ref,
                 n_harmonics=12, search_window_bins=4):
    """Return list of dicts {k, f_target, f_peak, L_dbchz}."""
    f = np.asarray(f)
    L = np.asarray(L_dbchz)
    results = []
    for k, f_target in predicted_spur_offsets(alpha, f_ref, n_harmonics):
        if f_target >= f[-1] or f_target <= f[0]:
            continue
        i0 = int(np.argmin(np.abs(f - f_target)))
        lo = max(i0 - search_window_bins, 0)
        hi = min(i0 + search_window_bins, len(f) - 1)
        i_peak = lo + int(np.argmax(L[lo:hi + 1]))
        results.append({
            "k": k,
            "f_target": float(f_target),
            "f_peak": float(f[i_peak]),
            "L_dbchz": float(L[i_peak]),
        })
    return results`}
        />
      </section>

      <section>
        <h2>Why predict first, then search around the prediction</h2>
        <p>
          A naive &quot;find peaks&quot; pass on a noisy PSD returns
          dozens of false positives. By predicting where fractional
          spurs <em>must</em> be (at multiples of
          <Inline tex="\,\alpha f_{ref}\," /> mod
          <Inline tex="\,f_{ref}\," />) and then searching a few bins
          around each prediction, we get a structured table that maps
          1-to-1 with the physical comb. The Welch resolution bandwidth
          can place the actual peak in a neighboring bin, so we widen
          the search to <code>search_window_bins=4</code>.
        </p>
      </section>

      <AssumptionBox kind="info">
        The local-max windowing means we always return <em>something</em>
        at every predicted offset. When the comb is hidden in noise, the
        reported &quot;spur level&quot; is just the noise floor at that
        offset — which is the right answer, just not a real spur.
      </AssumptionBox>
    </PageLayout>
  );
}
