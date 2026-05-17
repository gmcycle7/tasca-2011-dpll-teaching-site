// Single source of truth for every page in the teaching site.
// `kind` lets the navbar / index group them; `readingOrder` defines the
// guided tour the NextPrev component follows.

export type PageKind = "concept" | "figure" | "module" | "extension";

export type FigureMeta = {
  slug: string;
  kind: PageKind;
  shortLabel: string;
  title: string;
  oneLiner: string;
  paperFigGuess?: string;
  simScript?: string;
  plotPath?: string;
  status: "ready" | "partial" | "todo";
};

export const figureIndex: FigureMeta[] = [
  // ---------- conceptual / orientation ----------
  {
    slug: "big-picture",
    kind: "concept",
    shortLabel: "Big picture",
    title: "Big picture: why this PLL architecture exists",
    oneLiner:
      "Where Tasca 2011 sits in PLL history, what problem it solves, and why each block is the way it is.",
    status: "ready",
  },

  // ---------- figure-level concepts ----------
  {
    slug: "fig-architecture",
    kind: "figure",
    shortLabel: "Architecture",
    title: "System architecture: BBPD + DSM + DTC fractional-N DPLL",
    oneLiner: "Top-level block diagram and the role of every block.",
    paperFigGuess: "~Fig. 2 (UNVERIFIED)",
    status: "ready",
  },
  {
    slug: "fig-dtc-cancellation",
    kind: "figure",
    shortLabel: "DTC cancel",
    title: "DTC cancellation of DSM quantization error",
    oneLiner: "Why a single-bit TDC can work in a fractional-N PLL.",
    paperFigGuess: "~Fig. 3 (UNVERIFIED)",
    simScript: "scripts/run_dtc_cancellation_demo.py",
    plotPath: "/figures/dtc_cancellation.png",
    status: "ready",
  },
  {
    slug: "fig-bbpd-linearize",
    kind: "figure",
    shortLabel: "BBPD K_bb",
    title: "Bang-bang phase detector and its small-signal gain",
    oneLiner:
      "Where K_bb = sqrt(2/pi)/sigma comes from and why we still use sign().",
    paperFigGuess: "~Fig. 4 / Fig. 5 (UNVERIFIED)",
    status: "ready",
  },
  {
    slug: "fig-lock-transient",
    kind: "figure",
    shortLabel: "Lock",
    title: "Lock transient (Type-II PI loop)",
    oneLiner: "Pulling out an initial DCO frequency offset.",
    paperFigGuess: "~Fig. 21 (UNVERIFIED)",
    simScript: "scripts/run_core_lock_test.py",
    plotPath: "/figures/core_lock_test.png",
    status: "ready",
  },
  {
    slug: "fig-phase-noise",
    kind: "figure",
    shortLabel: "Phase noise",
    title: "Closed-loop phase noise & integrated jitter",
    oneLiner: "L(f) at the DCO output and how 560 fs_rms is integrated.",
    paperFigGuess: "~Fig. 15 + Fig. 18 (UNVERIFIED)",
    simScript: "scripts/run_phase_noise_demo.py",
    plotPath: "/figures/phase_noise.png",
    status: "ready",
  },
  {
    slug: "fig-frac-spur",
    kind: "figure",
    shortLabel: "Frac spur",
    title: "Fractional-spur generation by DTC nonidealities",
    oneLiner: "How DTC gain error and INL push spurs back into the spectrum.",
    paperFigGuess: "~Fig. 19 (UNVERIFIED)",
    simScript: "scripts/run_fractional_spur_demo.py",
    plotPath: "/figures/fractional_spurs.png",
    status: "ready",
  },
  {
    slug: "fig-lms",
    kind: "figure",
    shortLabel: "LMS cal",
    title: "LMS adaptive DTC-gain calibration",
    oneLiner: "g_hat converges to 1/(1+gain_err); BBPD residual collapses.",
    paperFigGuess: "~Fig. 13 (UNVERIFIED)",
    simScript: "scripts/run_lms_calibration_demo.py",
    plotPath: "/figures/lms_calibration.png",
    status: "ready",
  },

  // ---------- module deep-dives (one per sim/ file) ----------
  {
    slug: "mod-pll-params",
    kind: "module",
    shortLabel: "params",
    title: "sim/pll_params.py — every knob, every default",
    oneLiner: "The dataclass that defines what the simulator can do.",
    status: "ready",
  },
  {
    slug: "mod-dsm",
    kind: "module",
    shortLabel: "dsm",
    title: "sim/dsm.py — MASH 1-1-1 delta-sigma modulator",
    oneLiner: "How the fractional ratio is realised by integer division dither.",
    status: "ready",
  },
  {
    slug: "mod-fractional-divider",
    kind: "module",
    shortLabel: "divider",
    title: "sim/fractional_divider.py — multi-modulus divider wrapper",
    oneLiner: "Why this file is intentionally one screen.",
    status: "ready",
  },
  {
    slug: "mod-dco",
    kind: "module",
    shortLabel: "dco",
    title: "sim/dco.py — DCO frequency law",
    oneLiner: "Linear tuning; phase noise injected elsewhere.",
    status: "ready",
  },
  {
    slug: "mod-dtc",
    kind: "module",
    shortLabel: "dtc",
    title: "sim/dtc.py — digital-to-time converter impairments",
    oneLiner: "Gain, offset, INL, quantization — and how their ordering matters.",
    status: "ready",
  },
  {
    slug: "mod-bbpd",
    kind: "module",
    shortLabel: "bbpd",
    title: "sim/bbpd.py — single-bit detector + linearized helper",
    oneLiner: "sign() with optional metastability; K_bb exposed for hand calcs.",
    status: "ready",
  },
  {
    slug: "mod-loop-filter",
    kind: "module",
    shortLabel: "loop filter",
    title: "sim/loop_filter.py — discrete-time PI",
    oneLiner: "The Type-II controller; why integrator runs before the output.",
    status: "ready",
  },
  {
    slug: "mod-phase-noise",
    kind: "module",
    shortLabel: "phase_noise",
    title: "sim/phase_noise.py — generate + estimate L(f)",
    oneLiner: "IFFT-shaped colored noise; Welch back-conversion to dBc/Hz.",
    status: "ready",
  },
  {
    slug: "mod-jitter-spurs",
    kind: "module",
    shortLabel: "jitter+spurs",
    title: "sim/jitter.py and sim/spurs.py — post-processing",
    oneLiner: "From PSD to RMS jitter; from PSD to spur table.",
    status: "ready",
  },
  {
    slug: "mod-pll-model",
    kind: "module",
    shortLabel: "pll_model",
    title: "sim/pll_model.py — the closed-loop simulator",
    oneLiner: "All blocks wired together; sign convention, off-by-one fix, LMS path.",
    status: "ready",
  },

  // ---------- simulator extensions ----------
  {
    slug: "ext-deepviz",
    kind: "extension",
    shortLabel: "Deep viz",
    title: "Deep visualisations — ten figures that explain the architecture",
    oneLiner:
      "Block-by-block: what every signal looks like, what each knob does, where every dB comes from.",
    status: "ready",
  },
  {
    slug: "ext-ntf",
    kind: "extension",
    shortLabel: "Analytic NTF",
    title: "Analytic noise-transfer functions vs. simulated PSD",
    oneLiner:
      "Where the spectrum's shape comes from — overlay closed-form NTFs onto our PSD.",
    paperFigGuess: "~Fig. 6 (UNVERIFIED)",
    simScript: "scripts/run_noise_tf_demo.py",
    plotPath: "/figures/noise_tf.png",
    status: "ready",
  },
  {
    slug: "ext-multibit-tdc",
    kind: "extension",
    shortLabel: "Multi-bit TDC",
    title: "Why BBPD+DTC instead of a multi-bit TDC?",
    oneLiner: "A side-by-side simulation that motivates the architecture choice.",
    simScript: "scripts/run_multibit_tdc_demo.py",
    plotPath: "/figures/multibit_tdc.png",
    status: "ready",
  },
  {
    slug: "ext-sensitivity",
    kind: "extension",
    shortLabel: "Sensitivity",
    title: "Parameter sensitivity sweep",
    oneLiner: "How integrated jitter and worst spur move when knobs move.",
    simScript: "scripts/run_sensitivity_sweep.py",
    plotPath: "/figures/sensitivity_sweep.png",
    status: "ready",
  },
  {
    slug: "ext-kbb-tracker",
    kind: "extension",
    shortLabel: "K_bb tracker",
    title: "K_bb adaptive tracking — making loop BW robust to PVT",
    oneLiner:
      "Estimate σ at the BBPD input online, recover K_bb, scale Kp/Ki to hold loop BW constant.",
    simScript: "scripts/run_kbb_tracker.py",
    plotPath: "/figures/kbb_tracker.png",
    status: "ready",
  },
  {
    slug: "ext-allan",
    kind: "extension",
    shortLabel: "Allan dev",
    title: "Allan deviation σ_y(τ) — long-term stability",
    oneLiner:
      "Time-domain stability metric from the same closed-loop trace as L(f).",
    simScript: "scripts/run_allan_deviation.py",
    plotPath: "/figures/allan.png",
    status: "ready",
  },
  {
    slug: "ext-integrated",
    kind: "extension",
    shortLabel: "Interactive",
    title: "Interactive simulator (Streamlit)",
    oneLiner: "Adjust parameters and re-run live — embedded below.",
    status: "ready",
  },

  // ---------- glossary ----------
  {
    slug: "glossary",
    kind: "concept",
    shortLabel: "Glossary",
    title: "Glossary of symbols",
    oneLiner: "Every symbol used on this site, with units and where it appears.",
    status: "ready",
  },
];

// Guided tour. NextPrev navigation walks this list.
export const readingOrder: string[] = [
  "big-picture",
  "fig-architecture",
  "fig-dtc-cancellation",
  "fig-bbpd-linearize",
  "fig-lock-transient",
  "fig-phase-noise",
  "fig-frac-spur",
  "fig-lms",
  "ext-deepviz",
  "ext-kbb-tracker",
  "ext-allan",
  "ext-ntf",
  "ext-multibit-tdc",
  "ext-sensitivity",
  "mod-pll-params",
  "mod-dsm",
  "mod-fractional-divider",
  "mod-dco",
  "mod-dtc",
  "mod-bbpd",
  "mod-loop-filter",
  "mod-phase-noise",
  "mod-jitter-spurs",
  "mod-pll-model",
  "ext-integrated",
  "glossary",
];

export function getPageBySlug(slug: string): FigureMeta | undefined {
  return figureIndex.find((f) => f.slug === slug);
}

export const headlineFacts = {
  technology: "65-nm CMOS",
  tuningRange: "2.92 – 4.05 GHz",
  dcoStep: "70 Hz",
  power: "4.5 mW",
  jitterRms: "560 fs",
  jitterBand: "3 kHz – 30 MHz",
  inbandPN50k: "−102 dBc/Hz @ 50 kHz",
  worstFracSpur: "−42 dBc",
};
