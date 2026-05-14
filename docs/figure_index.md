# Figure Index — Tasca et al., JSSC Dec. 2011

> **STATUS: PARTIALLY VERIFIED, PDF still not in hand.** Headline numbers
> and overall architecture have been cross-checked against external
> open-access sources (NASA ADS abstract; Semantic Scholar abstract;
> "Design of DTC-Assisted High Performance Fractional-N PLLs" CAS
> tutorial slides by W. Wu, 2024-11-10, which cites Tasca 2011 as the
> canonical DTC-based BBPD frac-N DPLL). Re-searched 2026-05-14 with
> additional queries — no further open-access source surfaced. The IEEE
> Xplore PDF and the publishers' PDFs remain paywalled; ResearchGate
> "Request full text" requires direct contact with an author.
>
> Per-row page numbers and verbatim captions therefore remain
> `Verified? = NO` and the teaching site self-documents this on every
> page via the `paperFigGuess` field.
>
> **Externally confirmed facts** (Nov 2024 tutorial + 2011 abstract):
>   - 65-nm CMOS, tuning range 2.92–4.05 GHz, 70 Hz DCO step
>   - Integrated jitter 560 fs RMS over **3 kHz – 30 MHz**
>   - −102 dBc/Hz @ 50 kHz; worst in-band frac spur −42 dBc; 4.5 mW
>   - Block-diagram top level contains: BBPD, MMD (multi-modulus divider),
>     DSM, DTC, KDTC LMS calibration, DLF, DCO — matches our simulator
>   - DSM is MASH-1-1-1 (3rd order); residue bounded in ±2 T_VCO
>   - DTC cancels accumulated DSM quantization error on the feedback path
>     so that the BBPD sees near-zero phase error at lock — the same
>     principle our `pll_model.py` implements
>
> Reconcile remaining UNVERIFIED rows by:
> 1. Dropping the PDF into `/paper/`.
> 2. Running `scripts/extract_paper_structure.py` (to be implemented).
> 3. Diffing the extracted list against this file.

## Conventions

- **Caption summary** is paraphrased, not quoted verbatim, to avoid
  reproducing copyrighted text.
- **Status** column tracks our simulator's coverage of the figure, not
  whether the row itself has been verified against the PDF.
- **Verified?** column tracks PDF reconciliation. All rows start `NO`.

| #     | Caption summary (paraphrased)                                              | Page (approx) | Section                       | Proposed simulation model                                                                       | Expected output plot                                                  | Status | Verified? |
|-------|-----------------------------------------------------------------------------|---------------|-------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|--------|-----------|
| 1     | Conventional fractional-N analog PLL with multi-bit TDC — context figure   | ~2745         | I. Introduction               | Block-diagram only (no simulation). Used as motivation.                                          | Hand-drawn block diagram (SVG in `web/`).                             | TODO   | NO        |
| 2     | Proposed BBPD-based digital fractional-N PLL with DTC in feedback path     | ~2746         | II. Proposed architecture     | Top-level `pll_model.py` integrating all blocks.                                                | Block diagram (SVG) + pointer to time-domain sim.                     | TODO   | NO        |
| 3     | Operating principle: DTC cancels divider quantization residue              | ~2746-2747    | II. Proposed architecture     | Demonstrate that DTC injects the matching delay so BBPD sees ~0 residual error.                  | Time-domain trace: divider edge, DTC-shifted edge, residual error.    | TODO   | NO        |
| 4     | Bang-bang phase detector waveform / characteristic (sign(Δt))              | ~2747         | III. BBPD model               | `bbpd.py`: returns ±1 based on edge order; optional metastability noise.                         | Static BBPD output vs. Δt; with noise: smoothed S-curve.              | TODO   | NO        |
| 5     | Linearized BBPD gain: K_bb = sqrt(2/π)/σ_Δt                                | ~2747-2748    | III. BBPD model               | Analytical formula; Monte-Carlo check in `bbpd.py`.                                              | Effective gain vs. input jitter σ.                                    | TODO   | NO        |
| 6     | Linear phase-domain noise model of the loop                                | ~2748         | IV. Noise analysis            | `pll_model.py` linear-model mode: transfer functions H_ref, H_dco, H_bbpd, H_dtc.                | Magnitude vs. offset frequency for each noise transfer function.      | TODO   | NO        |
| 7     | Loop-filter architecture (digital PI + extra pole)                          | ~2749         | V. Loop filter                | `loop_filter.py`: proportional + integral path, optional IIR smoothing of the integral path.    | Open-loop gain Bode plot.                                             | TODO   | NO        |
| 8     | Digitally controlled oscillator (DCO) tuning bank scheme                   | ~2749-2750    | VI. DCO                       | `dco.py`: ideal frequency-controlled phase accumulator + phase noise injection from PSD model.   | Frequency vs. control word; phase-noise PSD.                          | TODO   | NO        |
| 9     | DCO measured / modeled free-running phase noise                            | ~2750         | VI. DCO                       | `phase_noise.py`: piecewise 1/f^3, 1/f^2, flat regions matched to paper.                         | L(f) [dBc/Hz] vs. offset.                                             | partial| NO        |
| 10    | Delta-sigma modulator (MASH 1-1-1 or similar) for fractional division     | ~2750         | VII. Fractional control       | `dsm.py`: MASH-1-1-1 (3rd-order) generating divider modulus dither.                              | Time-series of modulus; output PSD showing 3rd-order shaping.         | TODO   | NO        |
| 11    | DTC implementation block diagram (delay-line / interpolating)              | ~2751         | VIII. DTC                     | `dtc.py`: ideal DTC with gain error, offset, INL, quantization.                                  | Code-to-delay transfer; INL plot.                                     | TODO   | NO        |
| 12    | DTC nonlinearity (INL) impact on fractional spurs                          | ~2751-2752    | VIII. DTC                     | Inject configurable INL into `dtc.py`; measure spectrum at fractional offsets.                   | Output spectrum with vs. without INL.                                 | TODO   | NO        |
| 13    | LMS-based adaptive DTC gain calibration loop                               | ~2752         | VIII. DTC calibration         | LMS update of DTC gain estimate driven by BBPD sign correlated with DSM residue.                 | Gain estimate vs. iteration; spur level vs. iteration.                | TODO   | NO        |
| 14    | Chip micrograph                                                            | ~2753         | IX. Implementation            | Not simulated.                                                                                  | Replaced with placeholder note.                                       | n/a    | NO        |
| 15    | Measured phase noise spectrum (key result)                                 | ~2754         | X. Measurements               | Full top-level sim + Welch PSD on the phase output.                                              | L(f) [dBc/Hz] from 1 kHz to 40 MHz; integer vs. fractional case.      | partial| NO        |
| 16    | Phase noise at integer-N vs. fractional-N channel                          | ~2754         | X. Measurements               | Same as 15 with two carrier configs.                                                            | Overlaid L(f) plots.                                                  | TODO   | NO        |
| 17    | Phase noise sensitivity to DTC calibration on/off                          | ~2754-2755    | X. Measurements               | Toggle LMS calibration in sim.                                                                  | L(f) with calibration on vs. off.                                     | TODO   | NO        |
| 18    | Integrated RMS jitter vs. integration band                                 | ~2755         | X. Measurements               | `jitter.py`: integrate L(f) over band, convert to seconds.                                       | sigma_t (fs) vs. f_max.                                               | TODO   | NO        |
| 19    | Fractional spur level vs. fractional offset / channel                      | ~2755-2756    | X. Measurements               | Sweep fractional ratio; locate spurs in spectrum; report worst level.                            | Spur level (dBc) vs. fractional offset.                               | TODO   | NO        |
| 20    | Reference spur measurement                                                 | ~2756         | X. Measurements               | Modulation of DCO by ref-frequency residue, captured in spectrum.                                | Spectrum zoom around f_ref offset.                                    | TODO   | NO        |
| 21    | Locking transient / settling                                               | ~2756         | X. Measurements               | Time-domain sim with initial frequency offset; record DCO control word.                          | DCO frequency vs. time during acquisition.                            | TODO   | NO        |
| 22    | Performance comparison table with state of the art                         | ~2757         | XI. Comparison                | Not simulated.                                                                                  | Rendered as HTML table on summary page; our sim results in own row.   | n/a    | NO        |

## Likely figure count

The drafted index lists 22 entries. The actual paper may have anywhere from
~16 to ~22 figures (this paper class typically does). Several entries
(e.g. 14, 22) are non-simulation content. The actual numbering may collapse
or expand some of the conceptual figures above.

## Highest-priority figures for Step C

Per the user's stated reproduction priorities:

1. **Fig. 2** — system architecture (block diagram + entry point for sim)
2. **Fig. 5** — linearized BBPD model (analytic + Monte-Carlo)
3. **Fig. 3** — DTC quantization-noise cancellation concept
4. **Fig. 15 / 9** — phase noise plot
5. **Fig. 18** — integrated jitter
6. **Fig. 19** — fractional spur behavior
7. **Fig. 21** — lock transient
