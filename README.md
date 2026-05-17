# Tasca 2011 DPLL — Behavioral Simulator + Teaching Site

[![Tests](https://github.com/gmcycle7/tasca-2011-dpll-teaching-site/actions/workflows/test.yml/badge.svg)](https://github.com/gmcycle7/tasca-2011-dpll-teaching-site/actions/workflows/test.yml)
[![Pages](https://github.com/gmcycle7/tasca-2011-dpll-teaching-site/actions/workflows/deploy.yml/badge.svg)](https://github.com/gmcycle7/tasca-2011-dpll-teaching-site/actions/workflows/deploy.yml)

A behavioral model and a guided-tour teaching website for the
fractional-N digital PLL architecture described in:

> D. Tasca, M. Zanuso, G. Marzin, S. Levantino, C. Samori, A. L. Lacaita,
> "A 2.9–4.0-GHz Fractional-N Digital PLL With Bang-Bang Phase Detector
> and 560-fs_rms Integrated Jitter at 4.5-mW Power," **IEEE Journal of
> Solid-State Circuits**, vol. 46, no. 12, pp. 2745–2758, Dec. 2011.
> [IEEE Xplore](https://ieeexplore.ieee.org/document/6006551/)

> [!IMPORTANT]
> This is a **behavioral approximation** — every plot is produced by
> the Python simulator under `sim/`. **No paper figures or text are
> reproduced**, only paraphrased and cited.

## What's inside

| Folder | Purpose |
|---|---|
| `sim/` | Python phase-domain DPLL simulator (≈ 700 lines). |
| `scripts/` | 16 runnable demo + explorer scripts that produce all PNGs in `results/figures/`. |
| `gui/app.py` | Streamlit interactive dashboard against the same simulator. |
| `web/` | Vite + React + TS + Tailwind teaching site (25 pages). |
| `tests/` | 18 pytest invariants covering DSM, BBPD, DTC, NTF, LMS, integration. |
| `docs/` | Figure index, assumptions audit, model derivation, validation log. |

## Live site

If GitHub Pages is enabled for this repo, the site auto-deploys on every
push to `main`. The URL has the form:

    https://<your-username>.github.io/tasca-2011-dpll-teaching-site/

## Running locally

### Python simulator + plots

    python3 -m pip install -r requirements.txt
    python3 scripts/run_phase_noise_demo.py
    python3 scripts/run_dsm_explorer.py
    # ... or run them all:
    for s in scripts/run_*.py; do python3 "$s"; done

PNGs land in `results/figures/`, CSV data in `results/data/`.

### Streamlit dashboard

    streamlit run gui/app.py            # http://localhost:8501

Sliders for every parameter; five views (lock, DTC cancel, phase noise,
fractional spurs, LMS calibration).

### Teaching website

    cd web
    npm install
    npm run dev                          # http://localhost:5173

The `predev` hook copies fresh PNGs from `results/figures/` into
`web/public/figures/`. To refresh after a re-run, `npm run copy:figures`.

### Pytest

    python3 -m pytest tests/ -q          # 18 tests, ≈ 1 second

## Reading order for the site

The `Next →` button on every page walks this tour:

1. **Big picture** — why this PLL architecture exists.
2. **Architecture** → **DTC cancellation** → **BBPD K_bb**.
3. **Lock transient** → **Phase noise** → **Fractional spurs** → **LMS**.
4. **Deep visualisations** — 10 multi-panel explorers (DSM, BBPD, DTC,
   Bode, NTF family, lock family, noise budget, LMS sweep, realistic
   DCO, reference spur).
5. **Analytic NTF** → **Multi-bit TDC contrast** → **Sensitivity sweep**.
6. **Module deep-dives** — one page per `sim/` file.
7. **Interactive (Streamlit)** — embedded for local use.
8. **Glossary**.

## Status / limitations

- The paper PDF was not used when building the simulator. Headline
  numbers (560 fs RMS over 3 kHz – 30 MHz, −102 dBc/Hz @ 50 kHz, etc.)
  are cross-checked against the abstract and one open-access tutorial.
  Per-figure caption verification still needs the PDF; the figure
  index notes which rows remain `UNVERIFIED`.
- DCO phase-noise template is **ESTIMATED** for a typical LC oscillator
  at this carrier and power. The simulator's ≈ 500 fs RMS jitter is a
  pipeline sanity-check, not a chip-match.
- The interactive Streamlit page on the live site can't reach a server
  running on the visitor's `localhost:8501`; it explains how to start
  one locally.

## License

[MIT](LICENSE) for the original code and commentary in this repository.
The paper itself is © IEEE and is not included.

## Citation

If you use this teaching material, please cite the original paper, not
this repository. A bibtex stub:

```bibtex
@article{tasca2011fracn,
  author  = {Tasca, D. and Zanuso, M. and Marzin, G. and Levantino, S. and Samori, C. and Lacaita, A. L.},
  title   = {{A 2.9--4.0-GHz Fractional-N Digital PLL With Bang-Bang Phase Detector and 560-$\mathrm{fs}_{\mathrm{rms}}$ Integrated Jitter at 4.5-mW Power}},
  journal = {IEEE Journal of Solid-State Circuits},
  volume  = {46},
  number  = {12},
  pages   = {2745--2758},
  year    = {2011},
  doi     = {10.1109/JSSC.2011.2162923}
}
```
