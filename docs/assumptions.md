# Assumptions and Parameter Sourcing

> **STATUS: INITIAL DRAFT, PDF NOT YET PARSED.** Every parameter labeled
> *Estimated* must be re-checked once the PDF is read. The "Paper-stated"
> column reflects my best recollection of values from this paper, not a
> verified extraction. Treat all rows as provisional.

## Legend

| Source tag       | Meaning                                                                                              |
|------------------|------------------------------------------------------------------------------------------------------|
| **PAPER**        | Value is given numerically in the paper. (To be re-confirmed from PDF.)                              |
| **DERIVED**      | Computed from PAPER values (e.g. division ratio from carrier and ref).                               |
| **ESTIMATED**    | Not given in the paper; we picked a reasonable default. Must be flagged in code as such.             |
| **OPEN**         | We don't yet know the value or how the paper specifies it.                                           |

## 1. Top-level system parameters

| Symbol         | Description                                          | Value (draft)                       | Source     | Notes                                                                 |
|----------------|------------------------------------------------------|-------------------------------------|------------|-----------------------------------------------------------------------|
| f_ref          | Reference frequency                                  | 40 MHz                              | PAPER (?)  | Common for this generation; needs PDF check.                          |
| f_out          | Output carrier (tunable)                             | 2.9 - 4.0 GHz                       | PAPER      | Stated in title.                                                      |
| N_nom          | Nominal divide ratio                                 | f_out / f_ref ≈ 72.5-100            | DERIVED    | Fractional.                                                           |
| sigma_jitter   | Integrated RMS jitter (target)                       | 560 fs                              | PAPER      | Integration band **3 kHz - 30 MHz** (verified via external sources: ADS abstract + Semantic Scholar abstract). Behavioral sim returns ~500 fs with default ESTIMATED DCO PN template — order-of-magnitude only, NOT a silicon reproduction. |
| L_50kHz        | In-band phase noise at 50 kHz offset                 | -102 dBc/Hz                         | PAPER      | Confirmed via abstract (ADS).                                          |
| spur_max       | Worst-case in-band fractional spur                   | -42 dBc                             | PAPER      | Confirmed via abstract (ADS).                                          |
| f_dco_res      | DCO frequency-step resolution                        | 70 Hz                               | PAPER      | Confirmed via abstract — much finer than our default 10 kHz/LSB ESTIMATE; the chip's DCO must combine a coarse bank with a fine dithered branch. |
| P_diss         | Power dissipation                                    | 4.5 mW                              | PAPER      | Stated in title.                                                      |
| Integration band| Band over which the 560 fs RMS jitter is integrated  | 3 kHz - 30 MHz                      | PAPER      | Confirmed via abstract.                                                |
| Process        | CMOS technology node                                 | 65 nm                               | PAPER      | Confirmed via abstract.                                                |

## 2. BBPD parameters

| Symbol         | Description                                          | Value (draft)                       | Source     | Notes                                                                 |
|----------------|------------------------------------------------------|-------------------------------------|------------|-----------------------------------------------------------------------|
| K_bb           | Linearized BBPD gain                                 | sqrt(2/π)/sigma_in                  | DERIVED    | Standard small-signal result for a sign(.) detector with Gaussian input. |
| sigma_in       | Total RMS jitter seen by BBPD at lock                | ~1-3 ps                             | ESTIMATED  | Set so that linearization is valid; refine after sim.                 |
| meta_noise     | Metastability noise floor on BBPD output             | none by default                     | ESTIMATED  | Optional knob.                                                        |

## 3. DTC parameters

| Symbol         | Description                                          | Value (draft)                       | Source     | Notes                                                                 |
|----------------|------------------------------------------------------|-------------------------------------|------------|-----------------------------------------------------------------------|
| DTC_range      | Full-scale delay range                               | ≥ 1 / f_ref ≈ 25 ns                 | DERIVED    | Must cover one ref period of divider residue.                         |
| DTC_resolution | LSB delay step                                       | ~1 ps                               | ESTIMATED  | Pick to keep quantization noise below DCO noise.                      |
| DTC_INL_pp     | Peak-peak INL                                        | ESTIMATED (configurable)            | ESTIMATED  | Sweep to study spur generation.                                       |
| DTC_gain_err   | Initial gain error (relative)                        | ESTIMATED ~10 %                     | ESTIMATED  | LMS calibration converges from this.                                  |
| DTC_offset     | Static delay offset                                  | ESTIMATED                           | ESTIMATED  | Should be absorbed by loop integrator.                                |

## 4. Loop filter (digital PI)

| Symbol         | Description                                          | Value (draft)                       | Source     | Notes                                                                 |
|----------------|------------------------------------------------------|-------------------------------------|------------|-----------------------------------------------------------------------|
| Kp             | Proportional gain                                    | 8.0                                 | ESTIMATED  | Picked empirically so that ~2 MHz initial offset locks in ~150 us.    |
| Ki             | Integral gain                                        | 0.5                                 | ESTIMATED  | An initial 0.02 wound up the integrator too slowly to lock; raised.   |
| Loop BW        | Closed-loop -3 dB bandwidth                          | ~300-500 kHz (implied)              | ESTIMATED  | Not measured directly; inferred from the ringdown period in the lock test. |
| Extra pole     | Smoothing pole on integral branch                    | none                                | OPEN       | Not yet implemented; PDF should state architecture.                   |

## 5. DCO parameters

| Symbol         | Description                                          | Value (draft)                       | Source     | Notes                                                                 |
|----------------|------------------------------------------------------|-------------------------------------|------------|-----------------------------------------------------------------------|
| K_DCO          | Frequency step per LSB                               | ESTIMATED ~10 kHz/LSB               | ESTIMATED  | Choose to span tuning range with reasonable word width.               |
| L_DCO(1 MHz)   | Phase noise at 1 MHz offset                          | ~ -120 dBc/Hz                       | ESTIMATED  | Typical for LC DCO at this f_out and 4.5 mW.                          |
| Flicker corner | 1/f^3 to 1/f^2 corner                                | ~ 100 kHz                           | ESTIMATED  | Refine from paper if stated.                                          |
| Floor          | Noise floor                                          | ~ -150 dBc/Hz                       | ESTIMATED  |                                                                       |

## 6. Delta-sigma modulator

| Symbol         | Description                                          | Value (draft)                       | Source     | Notes                                                                 |
|----------------|------------------------------------------------------|-------------------------------------|------------|-----------------------------------------------------------------------|
| Architecture   | MASH 1-1-1 (3rd order)                               | OPEN                                | OPEN       | Common choice; PDF must confirm.                                      |
| Bit-width      | Fractional bit width                                 | ESTIMATED 24 bits                   | ESTIMATED  |                                                                       |
| f_dsm          | Clock                                                | f_ref (40 MHz)                      | DERIVED    |                                                                       |

## 7. Reference clock

| Symbol         | Description                                          | Value (draft)                       | Source     | Notes                                                                 |
|----------------|------------------------------------------------------|-------------------------------------|------------|-----------------------------------------------------------------------|
| sigma_ref      | RMS jitter of reference                              | ESTIMATED ~80 fs                    | ESTIMATED  | Typical crystal oscillator; refine if paper states.                   |
| L_ref(10 kHz)  | Reference phase noise at 10 kHz                      | ESTIMATED ~ -150 dBc/Hz             | ESTIMATED  | Crystal-class.                                                        |

## Open questions for the user / for PDF reconciliation

1. Reference frequency: 40 MHz assumed. (Could be 50 MHz.)
2. Integration band for the 560-fs_rms figure. (Likely 1 kHz - 40 MHz or 10 kHz - 40 MHz.)
3. Process node.
4. Exact DSM architecture and order.
5. Number of DTC bits and full-scale range.
6. Loop bandwidth (paper-stated, vs. our estimate).
7. Whether DCO is single LC tank or with capacitor bank switching during operation.
8. DTC calibration sign / algorithm specifics (LMS step size, correlation source).
9. Whether the paper includes a divider-modulus randomization beyond the DSM.
10. Whether reference path uses a duty-cycle / slicer model that contributes meaningful noise.

## Implementation defaults (committed in code)

The actual values that ship in `sim/pll_params.py` defaults right now:

| Symbol             | Value           | Notes                                                  |
|--------------------|-----------------|--------------------------------------------------------|
| f_ref              | 40 MHz          | ESTIMATED                                              |
| f_out_target       | 3.605 GHz       | Chosen so `alpha = 0.125` exercises DSM/DTC. ESTIMATED.|
| K_dco              | 10 kHz / LSB    | ESTIMATED                                              |
| dsm_order          | 3 (MASH 1-1-1)  | ESTIMATED                                              |
| dtc_quant_lsb      | 1 ps            | ESTIMATED                                              |
| dtc_gain_err       | 0 (ideal)       | knob, defaults ideal                                   |
| dtc_inl_amp        | 0 (ideal)       | knob, defaults ideal                                   |
| Kp, Ki             | 8.0, 0.5        | ESTIMATED, tuned empirically                           |
| lms_mu             | 1e-4            | ESTIMATED; demo-friendly step (converges in ~50 us @ gain_err=0.1) |
| lms_g_hat_init     | 1.0             | "I believe the gain is correct" prior                  |
| ref_jitter_rms     | 80 fs           | ESTIMATED                                              |
| DCO PN template    | (1k,10k,100k,1M,10M,100M Hz) -> (-65,-95,-110,-120,-135,-148) dBc/Hz | ESTIMATED for an LC DCO at 3.6 GHz; chosen to produce ~500 fs RMS jitter into a 1 kHz-20 MHz band. Every value is a guess, not a paper-stated number.|

