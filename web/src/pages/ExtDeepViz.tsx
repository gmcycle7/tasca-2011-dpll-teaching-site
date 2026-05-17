import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import PlotViewer from "../components/PlotViewer";
import AssumptionBox from "../components/AssumptionBox";
import { Inline } from "../components/EquationBlock";

const meta = getPageBySlug("ext-deepviz")!;

type Section = {
  id: string;
  block: string;
  title: string;
  src: string;
  caption: string;
  takeaway: React.ReactNode;
  script: string;
};

const sections: Section[] = [
  {
    id: "dsm",
    block: "DSM",
    title: "Modulus dither + accumulated residue",
    src: "/figures/dsm_explorer.png",
    caption:
      "α = 0.125 fed to MASH 1 / 2 / 3. Top-left: m[k] integer sequence. Top-right: m[k] PSD with theoretical Lth-order shaping (dotted slopes). Bottom-left: cumulative residue e_dsm[k] + density inset. Bottom-right: e_dsm PSD — the spectrum the DTC has to cancel.",
    takeaway: (
      <>
        Higher-order MASH pushes its quantisation energy further out of
        band. The cumulative residue <Inline tex="e_{dsm}" /> — the
        signal the DTC drives — is itself shaped (one order lower than
        the divider output), and that&apos;s why a fast DTC alone is not
        enough: you still need calibration to keep the analog gain
        matched.
      </>
    ),
    script: "scripts/run_dsm_explorer.py",
  },
  {
    id: "bbpd",
    block: "BBPD",
    title: "Static + averaged characteristic, K_bb derivation",
    src: "/figures/bbpd_explorer.png",
    caption:
      "Top-left: sign(e) staircase vs. erf() S-curves at three σ levels. Top-right: K_bb = √(2/π)/σ — analytic line + Monte-Carlo crosses. Bottom-left: BBPD output autocorrelation at lock (white). Bottom-right: BBPD output PSD compared to 2/f_ref white floor.",
    takeaway: (
      <>
        The 1-bit detector behaves as a continuous linear gain block in
        the small-signal regime, with K_bb inversely proportional to the
        input dither. Monte-Carlo agrees with the closed-form to under
        1% across three decades of σ. The output is approximately white
        — that&apos;s the assumption the analytic noise model leans on.
      </>
    ),
    script: "scripts/run_bbpd_explorer.py",
  },
  {
    id: "dtc",
    block: "DTC",
    title: "Characteristic, impairments, spur cost of INL",
    src: "/figures/dtc_explorer.png",
    caption:
      "Top-left: DTC output τ vs. target τ for ideal + each impairment in isolation. Top-right: residual error τ_out − τ_target for the same set. Bottom-left: sinusoidal INL profiles at 2 / 4 / 8 / 16 ripples per full scale. Bottom-right: closed-loop worst spur vs. INL amplitude.",
    takeaway: (
      <>
        A 10% gain error tilts the line; offset shifts it; INL adds
        ripples; quantisation chops it into stairs. The worst-spur curve
        is roughly linear in INL amplitude — every extra ps of INL
        costs about 2 dB in the worst spur for our default loop BW.
      </>
    ),
    script: "scripts/run_dtc_explorer.py",
  },
  {
    id: "bode",
    block: "Loop",
    title: "Bode plot — open-loop magnitude, phase, NTFs",
    src: "/figures/loop_bode.png",
    caption:
      "Open-loop |L(jω)| and ∠L(jω) computed analytically from K_bb measured in a steady-state run; closed-loop |H_ref| and |H_dco_pn| on the same axis.",
    takeaway: (
      <>
        Crossover ≈ 5.5 MHz, phase margin ≈ 86° in our default setup —
        well-damped. The closed-loop magnitudes flip role at exactly
        the crossover frequency, which is the visual definition of
        &quot;loop bandwidth&quot;.
      </>
    ),
    script: "scripts/run_loop_bode.py",
  },
  {
    id: "ntf-family",
    block: "Loop",
    title: "NTF family + per-source contribution",
    src: "/figures/ntf_family.png",
    caption:
      "Top: |H_ref|, |H_DCO|, |H_DTC|, |H_BBPD| magnitudes (ref/DTC/BBPD all enter at the same point, so they overlap). Bottom: the closed-loop L(f) split by source, summed back into a total.",
    takeaway: (
      <>
        In our default configuration, BBPD-folded noise dominates the
        in-band floor. To improve it you have to either raise K_bb
        (smaller in-loop dither — i.e. better DTC cancellation, lower
        DCO PN) or change the loop bandwidth. Improving the DCO PN
        template only buys you something above the loop BW.
      </>
    ),
    script: "scripts/run_ntf_family.py",
  },
  {
    id: "lock",
    block: "Loop",
    title: "Lock-transient family — Kp / Ki / Δf₀ sweeps",
    src: "/figures/lock_family.png",
    caption:
      "Top: sweep Kp; middle: sweep Ki; bottom: sweep the initial DCO frequency offset. DCO and reference noise are off so the dynamics are visible.",
    takeaway: (
      <>
        Kp controls overshoot, Ki controls settling speed; both
        together set the loop bandwidth. The pull-in time scales
        roughly linearly with the initial offset for moderate offsets,
        but breaks down once the BBPD saturates for many cycles in a
        row.
      </>
    ),
    script: "scripts/run_lock_family.py",
  },
  {
    id: "budget",
    block: "Loop",
    title: "Per-source noise budget + variance pie",
    src: "/figures/noise_budget.png",
    caption:
      "Top: stacked decomposition of the closed-loop L(f). Middle: integrated jitter vs. upper bound of the integration band, with the paper&apos;s 560 fs marker. Bottom: variance pie over 3 kHz – 20 MHz.",
    takeaway: (
      <>
        At our default settings, the BBPD quantisation contributes ≈
        97% of the integrated phase-variance budget — DCO PN and
        reference jitter are decorations. This single chart is the
        reason cutting K_bb (better DTC cal, lower in-loop dither) is
        the highest-leverage knob in the design.
      </>
    ),
    script: "scripts/run_noise_budget.py",
  },
  {
    id: "lms",
    block: "Calibration",
    title: "LMS DTC-gain calibration — μ sweep + gain-error sweep",
    src: "/figures/lms_explorer.png",
    caption:
      "Top-left: g_hat trajectory for five μ values. Top-right: misadjustment std(g_hat) vs. μ on a log-log axis (textbook 10x μ → 10x std). Bottom-left: g_hat trajectory for six gain-error settings. Bottom-right: closed-loop L(f) before vs. after convergence.",
    takeaway: (
      <>
        The convergence-speed / steady-state-noise trade-off is the
        classical LMS picture. Even a heavy 20% gain error converges
        cleanly to its 1/(1 + gain_err) target inside the same loop
        bandwidth.
      </>
    ),
    script: "scripts/run_lms_calibration_demo.py",
  },
  {
    id: "dco-real",
    block: "DCO",
    title: "Realistic two-band DCO: coarse + dithered fine",
    src: "/figures/realistic_dco.png",
    caption:
      "Top: f(control_word) for the linear DCO, coarse-only staircase, coarse+fine (smoother), and coarse+fine+DSM (per-cycle samples). Middle: per-cycle frequency at a sub-LSB control word — dither hops between codes; mean lands at 400 Hz target. Bottom: PSD of the frequency deviation — DSM shaping pushes dither noise high.",
    takeaway: (
      <>
        The paper&apos;s 70 Hz resolution doesn&apos;t come from a
        70-Hz/LSB physical LSB. It comes from a sub-LSB DSM dither that
        time-averages to any sub-Hz target while pushing the
        per-sample quantisation noise to high offsets where the loop
        attenuates it.
      </>
    ),
    script: "scripts/run_realistic_dco.py",
  },
  {
    id: "ref-spur",
    block: "Effects",
    title: "Reference spur — how supply leakage becomes a spectral peak",
    src: "/figures/ref_spur.png",
    caption:
      "Top: reference edges, clean vs. with 5 ps sinusoidal modulation at 500 kHz. Middle: closed-loop L(f) — a spike at the injection offset. Bottom: peak level vs. injected amplitude — 20·log10 slope confirms linear in-band response of H_ref.",
    takeaway: (
      <>
        Reference-feedthrough spurs appear at whatever frequency the
        modulation occurs. Below the loop BW the closed loop has unity
        gain to ref jitter, so the spur tracks 1:1 (in dB) with the
        injected amplitude — and only an out-of-band offset attenuates
        it.
      </>
    ),
    script: "scripts/run_ref_spur_demo.py",
  },
  {
    id: "dco-pn-physics",
    block: "DCO",
    title: "DCO phase-noise physics template (1/f³ + 1/f² + white)",
    src: "/figures/dco_pn_physics.png",
    caption:
      "Top: three template anchors at L(1 MHz) = −105/−115/−125 dBc/Hz with the flicker corner at 100 kHz. Middle: regional decomposition into 1/f³ (flicker), 1/f² (thermal), and white floor. Bottom: closed-loop L(f) — DCO PN only matters above the loop bandwidth.",
    takeaway: (
      <>
        A meaningful DCO template has three physics-anchored knobs (L at
        1 MHz, flicker corner, white floor) instead of six arbitrary
        corner-point numbers. Inside the loop bandwidth, the loop
        attenuates DCO PN regardless of which knob you push.
      </>
    ),
    script: "scripts/run_dco_pn_physics.py",
  },
  {
    id: "loop-pole",
    block: "Loop",
    title: "Loop-filter smoothing pole",
    src: "/figures/loop_filter_pole.png",
    caption:
      "BBPD-input error trace vs. four pole-alpha values, tail RMS vs. alpha (log-log), and closed-loop L(f) overlay.",
    takeaway: (
      <>
        A 1-pole IIR on the integrator branch softens the
        BBPD-driven hunting at high offset frequencies. In our regime
        the tail RMS is already near the noise floor so changing alpha
        has tiny effect on the integrated number — but you can see the
        peaking near 1–10 MHz disappear.
      </>
    ),
    script: "scripts/run_loop_filter_pole.py",
  },
  {
    id: "multibit-bbpd",
    block: "BBPD",
    title: "Multi-bit BBPD — does adding bits help?",
    src: "/figures/multibit_bbpd.png",
    caption:
      "Per-cycle detector output histogram (1/2/3-bit), tail BBPD-input RMS vs. bit count, and closed-loop L(f) overlay. Kp/Ki are rescaled so each architecture has comparable small-signal loop gain.",
    takeaway: (
      <>
        For a well-calibrated DTC the comparator residue is already
        sub-picosecond, so giving the detector more bits buys very
        little in-band performance. The 1-bit BBPD is the right
        engineering trade — much cheaper hardware, same noise.
      </>
    ),
    script: "scripts/run_multibit_bbpd.py",
  },
  {
    id: "inl-table",
    block: "DTC",
    title: "DTC INL: sinusoidal model vs. arbitrary lookup table",
    src: "/figures/dtc_inl_table.png",
    caption:
      "Top: INL profile shapes — sinusoid at 4 ripples/full-scale vs. a synthetic 32-bin lookup table. Middle: closed-loop L(f) for ideal / sinusoid / table. Bottom: worst predicted-comb spur for each.",
    takeaway: (
      <>
        Real DTC INL is rarely a clean sinusoid. The lookup-table
        path lets you drop a measured INL profile into the simulator
        and see exactly which comb harmonics get amplified.
      </>
    ),
    script: "scripts/run_dtc_inl_table.py",
  },
  {
    id: "realistic-dco-closed",
    block: "DCO",
    title: "Realistic two-band DCO in the closed loop",
    src: "/figures/realistic_dco_closed.png",
    caption:
      "Top: per-cycle DCO frequency trace (steady state) — realistic DCO shows ± fine-LSB hopping. Middle: cycle-averaged frequency converging to target. Bottom: closed-loop L(f) — linear vs. realistic DCO.",
    takeaway: (
      <>
        Replacing the linear DCO with the coarse-bank + dithered-fine
        model lifts the per-cycle frequency noise but the loop&apos;s
        high-pass NTF eats most of that energy. Steady-state spectrum
        is essentially unchanged — the architecture wins again.
      </>
    ),
    script: "scripts/run_realistic_dco_closed.py",
  },
  {
    id: "lms-multi",
    block: "Calibration",
    title: "Stacked LMS calibration — gain + offset",
    src: "/figures/lms_multi.png",
    caption:
      "Top: g_hat trajectories for both single-learner cases. Middle: offset_hat learning a 4 ps static DTC offset. Bottom: tail BBPD-input RMS for no-LMS / gain-only / gain+offset.",
    takeaway: (
      <>
        Two LMS loops run in parallel without fighting each other.
        Each looks at a different correlation (gain learner ←
        s_bbpd · e_dsm; offset learner ← mean of s_bbpd), so they
        converge to different physical impairments independently.
      </>
    ),
    script: "scripts/run_lms_multi_explorer.py",
  },
  {
    id: "kbb-tracker",
    block: "Calibration",
    title: "K_bb adaptive tracking via rolling σ estimate",
    src: "/figures/kbb_tracker.png",
    caption:
      "Top: rolling σ at the BBPD input and the implied K_bb = √(2/π)/σ. Bottom: a switching-density alternative estimator (fraction of sign flips in a rolling window).",
    takeaway: (
      <>
        The BBPD&apos;s effective gain depends on its input dither.
        Running a slow LMS that estimates σ lets a downstream loop
        scale Kp/Ki to keep the closed-loop bandwidth on target as
        PVT drifts.
      </>
    ),
    script: "scripts/run_kbb_tracker.py",
  },
  {
    id: "allan",
    block: "Metrics",
    title: "Allan deviation σ_y(τ) — long-term stability",
    src: "/figures/allan.png",
    caption:
      "Overlapping ADEV of the closed-loop divider edges; theoretical slope guides for white / flicker / random-walk FM; and ADEV for three loop bandwidths showing where the dominant noise type shifts with τ.",
    takeaway: (
      <>
        Allan deviation is the long-term stability metric ADCs and
        timing-critical receivers actually care about. The slope of
        σ_y(τ) tells you what noise type dominates at each averaging
        time — and the loop bandwidth controls where the transitions
        happen.
      </>
    ),
    script: "scripts/run_allan_deviation.py",
  },
];


export default function ExtDeepViz() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">What this page is</h2>
        <p>
          Ten standalone figures, one per behaviour we want intuition
          for. Each section shows a multi-panel plot generated by a
          dedicated script under <code>scripts/</code>, plus a short
          &quot;what to look for&quot; / &quot;why this matters&quot;
          note. None of these duplicate the simulation work the
          per-figure pages cover — they isolate one block at a time so
          you can build a mental picture of where every dB and every ps
          comes from.
        </p>
      </section>

      <section className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-800/40">
        <div className="text-xs uppercase text-slate-500">in-page TOC</div>
        <ol className="ml-4 mt-2 list-decimal space-y-1">
          {sections.map((s, i) => (
            <li key={s.id}>
              <a href={`#${s.id}`}>
                §{i + 1}. {s.block} — {s.title}
              </a>
            </li>
          ))}
        </ol>
      </section>

      {sections.map((s, i) => (
        <section key={s.id} id={s.id} className="scroll-mt-24 space-y-3">
          <h2>
            §{i + 1}. {s.block} — {s.title}
          </h2>
          <PlotViewer src={s.src} alt={s.title} caption={s.caption} />
          <p>{s.takeaway}</p>
          <p className="text-xs text-slate-500">
            Script: <code>{s.script}</code>
          </p>
        </section>
      ))}

      <AssumptionBox kind="info" title="Reproducing these locally">
        Each script lives under <code>scripts/</code>. Re-running it
        regenerates a PNG under <code>results/figures/</code>; the
        site&apos;s <code>predev</code> hook copies that PNG into
        <code> web/public/figures/ </code> on the next dev/build, so
        the plot above refreshes automatically.
      </AssumptionBox>
    </PageLayout>
  );
}
