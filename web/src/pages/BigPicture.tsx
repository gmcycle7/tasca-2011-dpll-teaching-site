import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import AssumptionBox from "../components/AssumptionBox";
import { Inline } from "../components/EquationBlock";

const meta = getPageBySlug("big-picture")!;

export default function BigPicture() {
  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Read this first</h2>
        <p>
          A phase-locked loop multiplies a clean reference clock up to a
          much higher carrier. For wireless transceivers the multiplier is
          a non-integer number (so the synthesizer can land on every
          channel), which forces an architecture that can divide by a
          <em> fractional </em> ratio. Fractional-N synthesizers have been
          studied since the 1970s; the question this paper answers is:
          <strong>
            {" "}
            how do you build one in deeply scaled CMOS, with a tiny power
            budget, while keeping jitter at the sub-picosecond level?
          </strong>
        </p>
      </section>

      <section>
        <h2>The road that led here</h2>
        <p>
          Three architectural eras you can read off the literature:
        </p>
        <ol className="ml-6 list-decimal space-y-2 text-slate-700">
          <li>
            <strong>Analog charge-pump fractional-N</strong> (pre-2000s).
            A phase/frequency detector drives a charge pump and a passive
            loop filter; a delta-sigma modulator dithers the integer
            divider. Works, but the time error injected by the dither has
            to be cancelled in the analog domain — usually by a current
            DAC — which is sensitive to mismatch and burns area.
          </li>
          <li>
            <strong>All-digital / multi-bit TDC PLL</strong> (mid-2000s).
            Replace the charge pump and the analog filter with a digital
            loop filter; replace the phase detector with a time-to-digital
            converter (TDC). Now the dither residue is digital and you can
            cancel it digitally, but the multi-bit TDC has to resolve
            sub-picosecond steps over a full reference period, so its
            <em> power and area scale poorly</em>.
          </li>
          <li>
            <strong>Single-bit TDC plus DTC in the feedback path</strong>{" "}
            (Tasca 2011). Throw the multi-bit TDC away — use a flip-flop
            that only tells you which edge came first. Then move the
            cancellation into the time domain: a digital-to-time converter
            in the feedback path delays the divider edge by exactly the
            amount the DSM &quot;owes&quot;. The flip-flop sees a
            near-zero phase error and a 1-bit answer is enough.
          </li>
        </ol>
      </section>

      <section>
        <h2>Why this trick wins</h2>
        <ul className="ml-6 list-disc space-y-2 text-slate-700">
          <li>
            <strong>Sub-ps resolution becomes a DTC problem, not a TDC
            problem.</strong> A delay line is cheap to build with fine
            resolution; a low-noise multi-bit time digitizer is not.
          </li>
          <li>
            <strong>Loop noise floor is set by the BBPD&apos;s tiny
            dither.</strong> Because the DTC has already done the
            cancellation, what reaches the BBPD is at most a few
            picoseconds of residual jitter, which it linearizes around.
          </li>
          <li>
            <strong>Calibration is digital and free.</strong> The DTC
            gain drifts; an LMS loop tracks it from the BBPD output alone,
            no auxiliary analog measurement needed.
          </li>
        </ul>
      </section>

      <section>
        <h2>The numbers the paper reports</h2>
        <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
          <Fact k="Process" v="65-nm CMOS" />
          <Fact k="Tuning" v="2.92 – 4.05 GHz" />
          <Fact k="Step" v="70 Hz" />
          <Fact k="Power" v="4.5 mW" />
          <Fact k="L(50 kHz)" v="−102 dBc/Hz" />
          <Fact k="Worst frac spur" v="−42 dBc" />
          <Fact k="Integrated jitter" v="560 fs RMS" />
          <Fact k="Jitter band" v="3 kHz – 30 MHz" />
        </div>
        <p>
          Sub-picosecond RMS jitter at sub-5 mW is the line that made this
          architecture famous.
        </p>
      </section>

      <section>
        <h2>How to read this site</h2>
        <p>
          The Next/Prev buttons walk a guided tour. The intended order is:
        </p>
        <ol className="ml-6 list-decimal space-y-1 text-slate-700">
          <li>
            <strong>This page</strong> — orientation.
          </li>
          <li>
            <strong>Architecture</strong> — top-level diagram and what each
            block is for.
          </li>
          <li>
            <strong>DTC cancellation</strong> — the central trick.
          </li>
          <li>
            <strong>BBPD linearization</strong> — why a 1-bit detector
            still gives a continuous loop response.
          </li>
          <li>
            <strong>Lock transient → phase noise → spurs → LMS</strong> —
            the behavior you measure on a real chip, in order of
            usefulness.
          </li>
          <li>
            <strong>Simulator extensions</strong> — analytic NTF vs sim,
            multi-bit TDC contrast, sensitivity sweep.
          </li>
          <li>
            <strong>Module deep-dives</strong> — open each
            <Inline tex="\,\texttt{sim/}\," /> file and read it line by
            line.
          </li>
          <li>
            <strong>Interactive simulator</strong> — sliders + live plots.
          </li>
          <li>
            <strong>Glossary</strong> — symbol cheat sheet.
          </li>
        </ol>
      </section>

      <AssumptionBox kind="warn" title="Honesty bar">
        Everything on this site comes from our own behavioral simulator,
        the paper&apos;s abstract, and a 2024 IEEE-CAS tutorial that cites
        the paper. We have not yet read the full PDF, so per-figure
        numbering inside the paper remains unverified. All plots are
        recreated by our simulator and labeled accordingly.
      </AssumptionBox>
    </PageLayout>
  );
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <div className="text-xs uppercase text-slate-500">{k}</div>
      <div className="mt-1 font-mono text-slate-800">{v}</div>
    </div>
  );
}
