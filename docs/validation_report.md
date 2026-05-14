# Validation Report

> **Disclaimer.** Everything below is a behavioral-simulation result, NOT
> a silicon measurement. Default parameters include several ESTIMATED
> values (see `assumptions.md`); the simulator's numbers should be read
> as order-of-magnitude sanity checks, not reproductions.

## Smoke-test run (default parameters, no PDF reconciliation yet)

Each row reports the headline number from the most recent default-args
run of the corresponding script under `scripts/`.

| Script                              | Paper-figure target | Key result (behavioral)                                          |
|-------------------------------------|---------------------|------------------------------------------------------------------|
| `run_core_lock_test.py`             | ~Fig. 21 (lock)     | 2 MHz initial offset locks in ~150 us; tail BBPD RMS ≈ 0.5 ps.   |
| `run_dtc_cancellation_demo.py`      | ~Fig. 3             | BBPD-input RMS error 190 ps with DTC OFF -> 0.4 ps with DTC ON.  |
| `run_phase_noise_demo.py`           | ~Fig. 15 + Fig. 18  | Closed-loop L(f) ≈ -115 to -120 dBc/Hz mid-band; integrated jitter **3 kHz - 20 MHz** ≈ 500 fs RMS (paper integrates 3 kHz - 30 MHz; our sim is bounded at f_ref/2 = 20 MHz). |
| `run_fractional_spur_demo.py`       | ~Fig. 19            | With DTC gain_err=0.1 and 2 ps INL: first fractional spur at f_ref·alpha emerges at about -65 dBc/Hz; with ideal DTC the spurs collapse into the noise floor. |
| `run_lms_calibration_demo.py`       | ~Fig. 13            | With gain_err=0.1 and mu=1e-4, `g_hat` converges to ≈ 0.9092 vs target 0.9091; tail BBPD RMS drops from ~20 ps to ~0.5 ps. |

The ~500 fs integrated-jitter agreement with the paper's headline 560 fs
is **expected to be coincidental**: the DCO phase-noise template values
were estimated from typical numbers for an LC DCO in this band and
tuned to land near the right order of magnitude. Treat the match as a
calibration that the integration pipeline works, not as evidence the
simulator matches the chip.

## What the simulator does NOT yet model

- **Closed-loop noise-transfer-function check**. We do not yet compute
  H_ref(s), H_dco(s), H_dtc(s) analytically and overlay them with the
  measured PSD — this is the natural next validation step (~Fig. 6).
- **Reference spur**. Modeled implicitly via ref-path jitter PSD, but
  no explicit periodic ref-frequency modulation pathway.

## Validation policy

Each reproduced figure entry, once added, will document:
- the paper figure number it targets,
- the script path,
- numeric agreement to within a stated tolerance (e.g. ±3 dB on PSD,
  ±20 % on integrated jitter — a behavioral model has no business
  trying to do better),
- caveats and the date of last run.

If we exceed tolerance, log the gap here with a hypothesis and let the
user decide whether to refine parameters or accept the discrepancy.
