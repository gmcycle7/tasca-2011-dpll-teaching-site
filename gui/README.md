# Streamlit GUI

Interactive front-end for the behavioral DPLL simulator under `../sim/`.

## Run

From the **project root** (so relative imports of `sim/` work):

    pip install -r requirements.txt
    streamlit run gui/app.py

Streamlit opens a browser tab at http://localhost:8501 by default.

## Layout

- **Sidebar** — four parameter groups + a view selector:
  1. Core PLL parameters (f_ref, f_out, K_DCO, Kp, Ki, n_cycles, seed)
  2. DSM / DTC impairments (DSM order, DTC gain error, INL, quant LSB)
  3. Noise sources (DCO PN on/off, ref jitter on/off, BBPD metastability)
  4. View: lock transient / DTC cancellation / phase noise / fractional spurs

- **Main area** — the selected view's plot plus key metrics
  (lock time, integrated jitter, worst spur, etc.).

Results are cached by parameter signature, so toggling between views
does NOT re-run the simulator unless a parameter changed.

## Disclaimer

Every plot is labeled "behavioral approximation — not a silicon
measurement". The defaults under `sim/pll_params.py` include several
ESTIMATED values (see `../docs/assumptions.md`).
