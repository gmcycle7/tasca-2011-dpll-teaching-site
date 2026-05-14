import { figureIndex } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import EquationBlock, { Inline } from "../components/EquationBlock";
import PlotViewer from "../components/PlotViewer";
import AssumptionBox from "../components/AssumptionBox";
import CodeBlock from "../components/CodeBlock";

const meta = figureIndex.find((f) => f.slug === "fig-phase-noise")!;

export default function FigPhaseNoise() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">From time error to L(f)</h2>
        <p>
          The simulator works in the time-error domain. At every reference
          cycle we record the post-DTC divider edge time relative to its
          ideal grid position:
        </p>
        <EquationBlock
          tex={String.raw`
            \delta[k] \;=\; t_{div,eff}[k] \;-\; (k+1)\,T_{ref}
          `}
          caption="Sampled at f_ref; we trim the lock transient and zero-mean."
        />
        <p>
          Time jitter at the divider output equals time jitter at the DCO
          output (the divider does not change time jitter), so the
          DCO-referred excess phase is
        </p>
        <EquationBlock
          tex={String.raw`
            \phi_n[k] \;=\; 2\pi\,f_{DCO,nom}\,\delta[k]
          `}
        />
        <p>
          and the single-sideband phase-noise spectrum follows from
          Welch&apos;s PSD estimate of that sequence, with the IEEE Std 1139
          factor:
        </p>
        <EquationBlock
          tex={String.raw`
            \mathcal{L}(f) \;=\; \tfrac{1}{2}\,S_{\phi}^{(1\text{-sided})}(f)
            \;\;\Big[\,\frac{\mathrm{rad}^2}{\mathrm{Hz}}\,\Big]
            \;\to\;\mathrm{dBc/Hz}.
          `}
        />
      </section>

      <section>
        <h2>Integrating RMS jitter</h2>
        <p>
          Once <Inline tex="\mathcal{L}(f)" /> is in hand, integrated phase
          variance and time jitter are
        </p>
        <EquationBlock
          tex={String.raw`
            \sigma_\phi^2 \;=\; 2\int_{f_{lo}}^{f_{hi}}\!\mathcal{L}(f)\,df,
            \qquad
            \sigma_t \;=\; \frac{\sigma_\phi}{2\pi\,f_{out}}.
          `}
        />
        <p>
          The paper integrates from 3 kHz to 30 MHz. Our simulator only
          gives us PSD up to <Inline tex="f_{ref}/2 = 20\,\mathrm{MHz}" />,
          so the strict comparison is 3 kHz – 20 MHz.
        </p>
      </section>

      <section>
        <h2>Closed-loop spectrum</h2>
        <PlotViewer
          src="/figures/phase_noise.png"
          alt="Closed-loop L(f) and the DCO open-loop template, log-log."
          caption="Inside the loop bandwidth, ref + BBPD noise dominate; outside, the DCO template takes over."
        />
        <p>
          The dashed line is the &quot;open-loop&quot; DCO PN template we
          assumed; the solid line is what the simulator produces after
          closing the loop. They agree at high offsets (loop has no
          authority) and diverge below the loop bandwidth (loop suppresses
          DCO PN, replaces it with ref + BBPD noise).
        </p>
      </section>

      <section>
        <h2>Where the integrated number lands</h2>
        <p>
          With our default DCO PN template, the integrator returns ≈ 500 fs
          RMS over 3 kHz – 20 MHz. The paper reports 560 fs RMS over 3 kHz –
          30 MHz. Treat the agreement as a sanity check that our PSD and
          integration pipelines are wired correctly; it is <strong>not</strong>
          evidence that the model matches the chip.
        </p>
      </section>

      <section>
        <h2>Inside the code — PSD pipeline in three calls</h2>
        <p>
          Step 1: turn the simulator&apos;s time-domain divider edges
          into an excess-phase sequence sampled at <Inline tex="f_{ref}" />.
        </p>
        <CodeBlock
          language="python"
          filename="sim/pll_model.py"
          lineRange="61-78"
          startLine={61}
          code={`def excess_phase_at_dco(res, trim_settling=0.5):
    """Return DCO-equivalent excess phase (rad) sampled at f_ref.

    delta[k]            = t_div_eff[k] - (k+1)*T_ref
    phi_dco_excess[k]   = 2*pi * f_dco_nominal * delta[k]
    """
    p = res.params
    n = len(res.t_div_eff)
    delta = res.t_div_eff - (np.arange(n) + 1) * p.T_ref
    i0 = int(trim_settling * n)
    delta = delta[i0:]
    delta = delta - np.mean(delta)
    return 2.0 * np.pi * p.f_dco_nominal * delta`}
        />
        <p>
          Step 2: Welch PSD, then convert to single-sideband phase noise
          in dBc/Hz with the IEEE 1139 factor.
        </p>
        <CodeBlock
          language="python"
          filename="sim/phase_noise.py"
          lineRange="42-55"
          startLine={42}
          code={`def estimate_psd(phi_excess_rad, fs, nperseg=None, window="hann"):
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
          Step 3: integrate <Inline tex="\mathcal{L}(f)" /> over the
          required band and convert to RMS time jitter.
        </p>
        <CodeBlock
          language="python"
          filename="sim/jitter.py"
          lineRange="10-26"
          startLine={10}
          code={`def integrated_phase_variance(f, L_dbchz, f_lo, f_hi) -> float:
    m = (f >= f_lo) & (f <= f_hi) & np.isfinite(L_dbchz)
    if m.sum() < 2:
        return float("nan")
    L_lin = 10.0 ** (L_dbchz[m] / 10.0)
    trapezoid = getattr(np, "trapezoid", None) or np.trapz
    return float(2.0 * trapezoid(L_lin, f[m]))

def integrated_rms_jitter_s(f, L_dbchz, f_lo, f_hi, f_carrier) -> float:
    var_phi = integrated_phase_variance(f, L_dbchz, f_lo, f_hi)
    if not np.isfinite(var_phi) or var_phi < 0:
        return float("nan")
    return float(np.sqrt(var_phi) / (2.0 * np.pi * f_carrier))`}
        />
        <p>
          The <code>* 2.0</code> in line 17 is the &quot;two
          sidebands&quot; correction; the <code>/ (2π·f_carrier)</code>
          in the final line converts radians-squared into seconds.
        </p>
      </section>

      <AssumptionBox kind="warn">
        The DCO phase-noise template values (corner-point dBc/Hz numbers in
        <code> sim/pll_params.py </code>) are all <strong>ESTIMATED</strong>
        — picked to give a credible LC-DCO shape at this carrier and
        power. They are not extracted from the paper.
      </AssumptionBox>
    </PageLayout>
  );
}
