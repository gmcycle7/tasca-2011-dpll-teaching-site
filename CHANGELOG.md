# CHANGELOG

All notable changes to the Tasca 2011 DPLL behavioral simulator and
teaching site, newest first.

## [0.3.0] — P1 + P2 build-out

### Simulator
- `PLLParams` extended with: optional ref-PN template (colored ref
  jitter), `bbpd_bits` + `bbpd_full_scale_s` for multi-bit BBPD,
  `loop_filter_pole_alpha` for a 1st-order smoothing IIR on the
  integral branch, `dtc_inl_table_s` for an arbitrary code-bin INL
  lookup, `use_realistic_dco` (+ band parameters), `lms_mu_offset`
  for digital DTC offset calibration, `lms_mu_inl` + `lms_inl_n_bins`
  for piecewise INL calibration.
- `sim/phase_noise.py` adds `physics_dco_pn_template` and
  `physics_ref_pn_template` — 1/f³ + 1/f² + white parameterisation.
- `sim/bbpd.py` adds multi-bit mid-tread quantiser.
- `sim/loop_filter.py` adds the smoothing-pole option.
- `sim/dtc.py` adds lookup-table INL path.
- `sim/allan.py` new module: overlapping Allan deviation σ_y(τ)
  from edge timestamps.
- `sim/pll_model.py` rewritten to wire all the new options while
  keeping default behaviour bit-identical to v0.2.0.
- 10 new pytest cases (`tests/test_sim_invariants.py`), total 28/28
  passing in 1.6 s.

### Scripts and figures
- `scripts/run_dco_pn_physics.py` — three-region template + closed-loop overlay.
- `scripts/run_loop_filter_pole.py` — α sweep, tail RMS, L(f).
- `scripts/run_multibit_bbpd.py` — 1/2/3-bit comparator comparison.
- `scripts/run_dtc_inl_table.py` — sinusoid vs. 32-bin lookup table.
- `scripts/run_realistic_dco_closed.py` — `RealisticDCO` in closed loop.
- `scripts/run_lms_multi_explorer.py` — gain + offset stacked LMS.
- `scripts/run_kbb_tracker.py` — rolling σ + switching-density K_bb estimators.
- `scripts/run_allan_deviation.py` — overlapping ADEV with slope guides.

### Web site
- New pages: `/ext-kbb-tracker`, `/ext-allan`.
- `ExtDeepViz` expanded from 10 to 18 sections (the 8 new figures
  added with the same "what to look for / why it matters" format).
- `ReadingProgress` component: thin top bar showing scroll position.
- "Edit this page on GitHub" link added to every page footer.
- Dark-mode polish on footer separators.
- New navbar pills for the two new extension pages.

### Known caveats
- INL piecewise calibration learner is in the codebase but the
  per-bin index needs an indexing-scheme refactor before it&apos;s
  enabled by default (only 1–2 bins exercised in our typical alpha;
  divergent updates if mu is non-trivial). Demo script currently
  shows gain + offset only.
- The K_bb tracking page is a post-processing demo. Hooking the
  estimator into a live Kp/Ki adapter is a follow-up.

## [0.2.0] — Phase 1 + 2 + 3 + 4 (earlier session)

- Vite + React + TS + Tailwind teaching site with 25 pages, dark
  mode toggle, code-split bundle (entry 23 kB after splitting).
- 18 educational PNGs from `scripts/run_*.py`.
- Analytic NTF module (`sim/noise_tf.py`) + page; multi-bit TDC
  contrast page; parameter-sensitivity sweep page.
- 18 pytest invariants, GitHub Pages auto-deploy.

## [0.1.0] — Phase 1 (initial session)

- Python phase-domain DPLL simulator under `sim/` (10 modules,
  ~700 lines).
- Five demo scripts producing the first plots.
- Streamlit dashboard at `gui/app.py`.
- Initial teaching pages (architecture, DTC cancellation, BBPD K_bb,
  lock, phase noise, fractional spurs, LMS).
- `docs/figure_index.md`, `docs/assumptions.md`,
  `docs/model_derivation.md`, `docs/validation_report.md`.
