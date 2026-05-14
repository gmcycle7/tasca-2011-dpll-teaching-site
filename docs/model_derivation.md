# Behavioral Model — Implementation Notes

> Phase-domain / time-error simulator, NOT a transistor-level model.
> Goal: reproduce paper-level system behavior (phase-noise PSD, integrated
> jitter, fractional spurs, lock transient, DTC-cancellation principle)
> from a small, readable Python codebase.
>
> Status: **minimum viable model implemented**. The four demonstration
> scripts under `scripts/` exercise every block. See
> `validation_report.md` for headline numbers from a smoke-test run.

## 1. Simulator domains and event timeline

The simulator runs on the reference-clock grid (sample period `T_ref = 1/f_ref`).
At each reference edge `k` we maintain:

- `phi_ref[k]`  : reference phase (modeled as `2π f_ref k T_ref` + noise).
- `phi_div[k]`  : phase of the divided DCO output at the BBPD sampling instant.
- `tau_div[k]`  : the time error of the divider edge w.r.t. the ideal
                  ref edge, i.e. `(phi_ref[k] - phi_div[k]) / (2π f_ref)`.
- `tau_dtc[k]`  : the delay programmed into the DTC for this ref cycle.
- `e[k] = tau_div[k] - tau_dtc[k]` : the residual time error fed to BBPD.
- `s[k] = sign(e[k])` : BBPD output (±1), plus optional metastability noise.
- `u[k]`        : loop-filter output (DCO tuning word).
- `m[k]`        : divider modulus chosen by DSM for cycle k.
- `q[k]`        : DSM accumulated residue used to drive the DTC.

The DCO is integrated between reference edges using the average tuning
word, since its frequency is what is set by `u[k]`; phase advances by
`2π f_DCO(u[k]) m[k] T_ref` plus DCO phase noise.

This event-driven, single-sample-per-ref-cycle approach is much cheaper
than ns-resolution simulation while preserving all loop dynamics and
noise-transfer behavior up to f_ref/2.

## 2. Per-block model summary

### 2.1 Reference clock (`sim/pll_params.py` + injection in `pll_model.py`)
- Ideal phase: `2π f_ref t`.
- Noise: white phase noise generated from a target PSD model, or
  optionally a measured phase-noise template.

### 2.2 Fractional divider (`sim/fractional_divider.py`)
- Modulus `N + m[k]` where `m[k]` is the integer dither from the DSM.
- Phase update: divider edge time is the instant when accumulated DCO
  phase equals `2π (N + m[k])` more than at the previous edge.
- Bookkeeping: the DSM residue `q[k]` (the deferred fraction) is the
  exact information the DTC needs to cancel.

### 2.3 Delta-sigma modulator (`sim/dsm.py`)
- MASH 1-1-1 (default), configurable order (1, 2, 3).
- Input: target fractional value `alpha = (f_out / f_ref) - N`.
- Output: integer dither `m[k]` such that `<m[k]> = alpha`, with high-pass
  shaped quantization residue.
- Side output: the running residue, used as the "correct delay" target
  for the DTC.

### 2.4 BBPD (`sim/bbpd.py`)
- `s[k] = sign(e[k] + n_meta[k])` where `n_meta` is optional Gaussian
  metastability noise.
- Linearized gain returned as a helper for analytic comparisons:
  `K_bb = sqrt(2/π) / sigma_e`.

### 2.5 DTC (`sim/dtc.py`)
- Ideal model: `tau_dtc[k] = G * q[k] + offset + INL(code) + n_q[k]`,
  where:
  - `G` is the DTC gain (target = `T_ref / 2^Nbits`),
  - `offset` is a static delay,
  - `INL(code)` is a code-dependent nonlinearity (sinusoidal + random
    components, configurable),
  - `n_q[k]` is uniform quantization noise.

### 2.6 Digital loop filter (`sim/loop_filter.py`)
- Discrete-time PI: `u[k] = Kp * s[k] + Ki * sum(s[0..k])`.
- Optional smoothing IIR pole on the integral branch.

### 2.7 DCO (`sim/dco.py`)
- Frequency: `f_DCO = f_0 + K_DCO * u[k]` (linearized).
- Phase: integrated between ref edges with appropriate modulus updates.
- Phase noise: drawn from a piecewise PSD template
  (`sim/phase_noise.py`) and added to the DCO phase trajectory.

### 2.8 LMS DTC-gain calibration (`pll_model.py`, gated by `enable_lms`)
- The DSM residue `e_dsm[k]` is pre-scaled by an adaptive coefficient
  `g_hat` before being passed to the DTC, so
  `tau_target = g_hat * e_dsm[k] * T_dco_nominal`.
- After each BBPD decision, `g_hat` is updated by
  `g_hat[k+1] = g_hat[k] - mu * s_bbpd[k] * e_dsm[k]`.
- In steady state, `g_hat -> 1 / (1 + dtc_gain_err)` (verified
  empirically; with `gain_err = 0.10` the simulator converges to
  `g_hat ≈ 0.9092` against a target of `0.9091`).
- Sign reasoning: a positive `gain_err` makes the DTC over-delay, so
  for positive `e_dsm` the BBPD sees a positive residual (`s = +1`).
  The product `s * e_dsm` is then positive on average and the rule
  drives `g_hat` *down*, restoring cancellation.

### 2.9 Phase noise estimation and jitter integration
- `sim/phase_noise.py`: Welch PSD on the steady-state DCO excess phase
  output. Returns L(f) in dBc/Hz.
- `sim/jitter.py`: integrates L(f) over a user-specified band, converts
  to RMS time jitter in seconds.

### 2.10 Spur measurement
- Generated as part of phase_noise estimation: a peak-finding pass on
  the PSD detects fractional spurs above a configurable threshold.

## 3. Linearized phase-domain transfer functions

For the noise-analysis figure (~Fig. 6) we provide a separate "linear
model" mode (`pll_model.py: linear_psd_analysis()`) that returns:

- `H_BBPD(f)`  : noise transfer function from BBPD input noise to DCO phase.
- `H_DCO(f)`   : noise transfer function from DCO intrinsic noise to output phase.
- `H_REF(f)`   : noise transfer function from reference noise to output.
- `H_DTC(f)`   : noise transfer function from DTC quantization to output.

These are computed analytically from the small-signal model and used to
cross-check the time-domain simulation.

## 4. Why this is the minimum viable model

- One sample per reference cycle captures every event the actual chip
  reacts to. BBPD only fires at ref edges; loop filter only updates
  at ref edges; DTC only changes per ref edge.
- DCO frequency control is per-ref-edge in the real chip, so the
  zero-order-hold model is exact (not an approximation).
- Phase noise can be injected as colored noise on top of the
  deterministic phase, which is what real measurements see in PSD.
- This avoids ns-resolution oscillator simulation (which would need
  ~10^9 samples for the same band) while still producing a PSD
  comparable to a measured spectrum.

## 5. Out of scope for the minimum model

- Transistor-level DCO design, varactor capacitance curves.
- Latch metastability circuit-level modeling (we only inject decision
  noise).
- Reference-buffer thermal noise simulated at GHz rates (only modeled
  as low-rate jitter).
- Supply / substrate coupling.
- Temperature drift.
- (Originally deferred; now implemented) ~~LMS adaptive DTC gain calibration~~.

## 6. Sign conventions used in code

All time errors are in SECONDS. Positive `e_bbpd` means the DTC-delayed
divider edge is LATER than the reference edge. BBPD therefore outputs
`+1` when the feedback is late; the loop responds by raising `u`,
which speeds the DCO up, which shortens future divider periods and
drives `e_bbpd` back toward zero. The DSM residue uses the convention

    e_dsm[k] = (sum of alpha-per-step) - (sum of m[j])           [cycles]

so `e_dsm > 0` indicates the integer divider has emitted fewer cycles
than an ideal fractional divider would. The DTC delay is therefore
`tau_dtc = e_dsm * T_dco_nominal` (positive) — it pushes the divider
edge later to land on the ideal fractional time.

## 7. Off-by-one in initial alignment

Both the divider and reference are taken to be edge-aligned at `t=0`,
so the FIRST emitted divider edge corresponds to the FIRST post-zero
reference edge at `t = T_ref`. The simulator therefore samples
`t_ref[k] = (k+1) * T_ref + ref_jitter[k]`. Initial smoke tests
without this offset produced ~25 ns of constant bias error and the
loop never appeared to lock.

## 8. Module map

| File                          | Purpose                                                          |
|-------------------------------|------------------------------------------------------------------|
| `sim/pll_params.py`           | Dataclass with every parameter and sensible defaults.            |
| `sim/dsm.py`                  | MASH 1/2/3 modulator + cumulative residue exposed to DTC.        |
| `sim/fractional_divider.py`   | D = N_int + m thin wrapper (extension point).                    |
| `sim/dtc.py`                  | Gain error, offset, quantization, sinusoidal INL.                |
| `sim/bbpd.py`                 | sign() with optional Gaussian decision noise + Kbb formula.      |
| `sim/loop_filter.py`          | Discrete-time PI.                                                |
| `sim/dco.py`                  | f = f_nom + Kdco*u (linear tuning).                              |
| `sim/phase_noise.py`          | Colored PN sequence generator + Welch PSD estimator.             |
| `sim/jitter.py`               | Integrate L(f) -> RMS jitter in seconds.                         |
| `sim/spurs.py`                | Predicted fractional-spur offsets + local-peak picker.           |
| `sim/pll_model.py`            | Top-level closed-loop time-domain simulator.                     |

## 9. Per-script intent

| Script                                     | Demonstrates                                                                                  |
|--------------------------------------------|-----------------------------------------------------------------------------------------------|
| `scripts/run_core_lock_test.py`            | Lock transient from an initial frequency offset (Type-II PI behavior).                        |
| `scripts/run_dtc_cancellation_demo.py`     | Order-of-magnitude reduction of BBPD-input error when DTC is enabled.                         |
| `scripts/run_phase_noise_demo.py`          | Closed-loop L(f) shape + integrated RMS jitter compared to the DCO open-loop template.        |
| `scripts/run_fractional_spur_demo.py`      | Emergence of fractional spurs under DTC gain error + INL, vs. ideal DTC.                      |
| `scripts/run_lms_calibration_demo.py`      | LMS adaptive DTC-gain calibration: g_hat convergence, BBPD RMS collapse, steady-state spurs.  |
