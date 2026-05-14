import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import CodeBlock from "../components/CodeBlock";
import EquationBlock, { Inline } from "../components/EquationBlock";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("mod-phase-noise")!;

export default function ModPhaseNoise() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Purpose</h2>
        <p>
          Two responsibilities, both around the IEEE Std 1139 definition
          of <Inline tex="\mathcal{L}(f)" />:
        </p>
        <ul className="ml-6 list-disc text-slate-700">
          <li>
            <strong>Generate</strong> a colored phase-noise sequence whose
            PSD matches a target template specified at corner frequencies.
          </li>
          <li>
            <strong>Estimate</strong> <Inline tex="\mathcal{L}(f)" /> from
            a sampled excess-phase sequence via Welch.
          </li>
        </ul>
      </section>

      <section>
        <h2>Generation: from L(f) corners to a time-domain sequence</h2>
        <CodeBlock
          language="python"
          filename="sim/phase_noise.py"
          lineRange="18-39"
          startLine={18}
          code={`def generate_pn_sequence(n_samples, fs, freqs_hz, levels_dbchz, rng=None):
    """Generate phi_n[k] in rad with the target L(f) at sample rate fs."""
    if rng is None:
        rng = np.random.default_rng(0)
    freqs = np.asarray(freqs_hz, dtype=float)
    levels = np.asarray(levels_dbchz, dtype=float)

    f = np.fft.rfftfreq(n_samples, d=1.0 / fs)
    log_f = np.log10(np.clip(f, 1.0, None))
    L_db = np.interp(log_f, np.log10(freqs), levels,
                     left=levels[0], right=levels[-1])
    # S_phi (one-sided) = 2 * 10^(L/10)  [rad^2/Hz]
    S_phi = 2.0 * 10.0 ** (L_db / 10.0)
    S_phi[0] = 0.0

    # IRFFT amplitudes for a real signal with PSD S_phi
    amps = np.sqrt(S_phi * n_samples * fs / 2.0)
    phases = rng.uniform(0.0, 2.0 * np.pi, len(f))
    X = amps * np.exp(1j * phases)
    X[0] = 0.0
    if n_samples % 2 == 0:
        X[-1] = X[-1].real
    return np.fft.irfft(X, n=n_samples)`}
        />
      </section>

      <section>
        <h2>Why frequency-domain synthesis (and not filtered white noise)</h2>
        <p>Three reasons in order of importance:</p>
        <ul className="ml-6 list-disc space-y-2 text-slate-700">
          <li>
            <strong>You specify L(f) directly.</strong> No FIR/IIR design
            step, no filter-order vs. accuracy trade-off, no filter
            transient settling. The corner-point list is exactly the
            shape you get.
          </li>
          <li>
            <strong>One pass, reproducible.</strong> Same seed → same
            sequence. Useful for regression testing.
          </li>
          <li>
            <strong>Trivial Parseval check.</strong> Integrating
            <Inline tex="\,\mathcal{L}(f)\," /> of the generated sequence
            gives back the user-specified phase variance to within
            sampling precision.
          </li>
        </ul>
      </section>

      <section>
        <h2>The amplitude formula in one line</h2>
        <EquationBlock
          tex={String.raw`
            |X[k]| \;=\; \sqrt{S_\phi^{(1)}(f_k)\,\frac{N\,f_s}{2}}
          `}
          caption="Each rfft bin's magnitude that gives the right Parseval power."
        />
        <p>
          For a real signal of length <Inline tex="N" /> with sample rate
          <Inline tex="f_s" /> and target one-sided PSD
          <Inline tex="S_\phi^{(1)}(f)" />, this is what each rfft bin
          must hold. Drop the factor 2 and you&apos;re off by 3 dB
          everywhere.
        </p>
      </section>

      <section>
        <h2>Estimation: Welch back into L(f)</h2>
        <CodeBlock
          language="python"
          filename="sim/phase_noise.py"
          lineRange="42-57"
          startLine={42}
          code={`def estimate_psd(phi_excess_rad, fs, nperseg=None, window="hann"):
    """Return (f, L_dbchz) using Welch on the excess-phase sequence."""
    n = len(phi_excess_rad)
    if nperseg is None:
        nperseg = min(n, 1 << 14)
    f, Pxx = signal.welch(phi_excess_rad, fs=fs, nperseg=nperseg,
                          window=window, scaling="density",
                          return_onesided=True, detrend="constant")
    # Pxx is the one-sided PSD in rad^2/Hz; L(f) = S_phi_onesided / 2.
    with np.errstate(divide="ignore"):
        L = 10.0 * np.log10(np.maximum(Pxx / 2.0, 1e-300))
    return f, L`}
        />
        <p>
          <strong>Why <code>Pxx / 2</code>?</strong> <code>scipy.signal.welch</code>
          with <code>return_onesided=True</code> already returns the
          one-sided PSD. The IEEE 1139 convention is
          <Inline tex="\;\mathcal{L}(f)=S_\phi^{(1)}(f)/2\;" />, so dividing
          by 2 converts &quot;total phase noise per Hz&quot; into
          &quot;single-sideband phase noise per Hz&quot;. This conversion
          is the most common 3-dB error in PLL simulators; we centralize
          it here so it only happens once.
        </p>
      </section>

      <AssumptionBox kind="warn">
        The DCO PN corner-point template used by default is
        <strong> ESTIMATED</strong>, not extracted from the paper. The
        integrated jitter our sim reports is a sanity check on the
        pipeline, not a chip-matched number.
      </AssumptionBox>
    </PageLayout>
  );
}
