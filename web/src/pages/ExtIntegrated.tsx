import { useState } from "react";
import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import AssumptionBox from "../components/AssumptionBox";

const meta = getPageBySlug("ext-integrated")!;
const STREAMLIT_URL = "http://localhost:8501";
const IS_PROD = import.meta.env.PROD;

export default function ExtIntegrated() {
  const [embedded, setEmbedded] = useState(!IS_PROD);

  return (
    <PageLayout meta={meta}>
      <section>
        <h2 className="!mt-0">Live, hands-on simulator</h2>
        <p>
          The Streamlit dashboard under <code>gui/app.py</code> calls the
          same <code>sim/</code> modules walked through on the other
          pages, but with sliders for every parameter and a re-run on
          every change. It runs at{" "}
          <a href={STREAMLIT_URL} target="_blank" rel="noreferrer">
            {STREAMLIT_URL}
          </a>{" "}
          when its server is up.
        </p>
      </section>

      {IS_PROD && (
        <AssumptionBox kind="warn" title="Running from the deployed site">
          <p>
            The Streamlit server only exists on your own machine. The
            iframe below would try to reach <code>localhost:8501</code> on
            your computer — that&apos;ll only work if you start the
            simulator yourself. Use the commands in the next section,
            then come back here and toggle &quot;show embed&quot;.
          </p>
        </AssumptionBox>
      )}

      <section>
        <h2>How to start it locally</h2>
        <pre>{`# clone the repo, then
python3 -m pip install -r requirements.txt
streamlit run gui/app.py             # http://localhost:8501

# (the Vite teaching site is npm install + npm run dev,
#  from the web/ subdirectory)`}</pre>
        <p>
          Once Streamlit is running, toggle the embed and the iframe
          below loads. If you see &quot;refused to connect&quot;, the
          server is not up yet — open the link in the section above
          first.
        </p>
      </section>

      <section>
        <h2>The live view</h2>
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>
            Target: <code>{STREAMLIT_URL}</code>
          </span>
          <button
            type="button"
            className="rounded px-2 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-800"
            onClick={() => setEmbedded((v) => !v)}
          >
            {embedded ? "hide" : "show"} embed
          </button>
        </div>
        {embedded && (
          <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
            <iframe
              title="Streamlit DPLL simulator"
              src={STREAMLIT_URL}
              className="block h-[820px] w-full bg-white"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
            />
          </div>
        )}
      </section>

      <section>
        <h2>Recommended exploration order</h2>
        <ol className="ml-6 list-decimal space-y-2 text-slate-700 dark:text-slate-300">
          <li>
            <strong>Phase noise view</strong>. Toggle &quot;DCO phase
            noise&quot; off and on — watch the closed-loop floor reshape
            into the loop-suppressed shape inside the loop BW.
          </li>
          <li>
            <strong>DTC cancellation view</strong>. Slide
            <code> DTC gain error </code> from 0 to 0.1 and notice how
            the BBPD-input RMS jumps from ~0.5 ps to ~20 ps.
          </li>
          <li>
            <strong>LMS calibration view</strong>. Keep the gain error at
            0.1 and tick the LMS box; watch <code>g_hat</code> march to
            0.909 in about 50 µs of simulated time.
          </li>
          <li>
            <strong>Fractional spurs view</strong>. Set
            <code> α = 0.01 </code> and impair the DTC; the comb is
            visible at integer multiples of 400 kHz.
          </li>
        </ol>
      </section>

      <AssumptionBox kind="info">
        Static-host limitation: GitHub Pages serves only static assets,
        so it can&apos;t run Python. The teaching pages themselves work
        fully online; the interactive simulator just needs you to clone
        the repo and start its server locally.
      </AssumptionBox>
    </PageLayout>
  );
}
