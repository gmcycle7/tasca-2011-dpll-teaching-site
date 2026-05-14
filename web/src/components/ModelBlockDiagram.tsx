// Original SVG block diagram drawn from our simulator's module map.
// This is NOT a tracing of any paper figure; it is the way OUR
// `sim/pll_model.py` is wired and is meant to teach the model, not the chip.

type Props = {
  highlight?:
    | "ref"
    | "dsm"
    | "divider"
    | "dtc"
    | "bbpd"
    | "lpf"
    | "dco"
    | "lms"
    | null;
};

export default function ModelBlockDiagram({ highlight = null }: Props) {
  const lit = (k: string) =>
    highlight === k
      ? { fill: "#dbeafe", stroke: "#1d4ed8" }
      : { fill: "#ffffff", stroke: "#475569" };

  const text = (k: string) =>
    highlight === k ? "fill-accent-fg font-semibold" : "fill-slate-700";

  return (
    <figure className="rounded-lg border border-slate-200 bg-white p-4">
      <svg
        viewBox="0 0 760 360"
        className="mx-auto block w-full max-w-3xl"
        role="img"
        aria-label="DPLL block diagram"
      >
        <defs>
          <marker
            id="arr"
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
          </marker>
        </defs>

        {/* Reference */}
        <rect x="20" y="60" width="100" height="50" rx="8"
              {...lit("ref")} strokeWidth="1.5" />
        <text x="70" y="92" textAnchor="middle" className={text("ref")} fontSize="13">
          Reference
        </text>
        <text x="70" y="120" textAnchor="middle" fontSize="11" fill="#64748b">
          f_ref ≈ 40 MHz
        </text>

        {/* BBPD */}
        <rect x="180" y="60" width="100" height="50" rx="8"
              {...lit("bbpd")} strokeWidth="1.5" />
        <text x="230" y="86" textAnchor="middle" className={text("bbpd")} fontSize="13">
          BBPD
        </text>
        <text x="230" y="102" textAnchor="middle" fontSize="11" fill="#64748b">
          sign(e)
        </text>

        {/* Loop filter */}
        <rect x="330" y="60" width="100" height="50" rx="8"
              {...lit("lpf")} strokeWidth="1.5" />
        <text x="380" y="86" textAnchor="middle" className={text("lpf")} fontSize="13">
          Digital PI
        </text>
        <text x="380" y="102" textAnchor="middle" fontSize="11" fill="#64748b">
          Kp + Ki/(1−z⁻¹)
        </text>

        {/* DCO */}
        <rect x="490" y="60" width="100" height="50" rx="8"
              {...lit("dco")} strokeWidth="1.5" />
        <text x="540" y="86" textAnchor="middle" className={text("dco")} fontSize="13">
          DCO
        </text>
        <text x="540" y="102" textAnchor="middle" fontSize="11" fill="#64748b">
          f₀ + K_DCO·u
        </text>

        {/* Output */}
        <rect x="640" y="60" width="100" height="50" rx="8"
              fill="#f1f5f9" stroke="#475569" strokeWidth="1.5" />
        <text x="690" y="92" textAnchor="middle" fontSize="13" fill="#0f172a">
          f_out
        </text>
        <text x="690" y="120" textAnchor="middle" fontSize="11" fill="#64748b">
          ~3.6 GHz
        </text>

        {/* Divider */}
        <rect x="490" y="220" width="100" height="50" rx="8"
              {...lit("divider")} strokeWidth="1.5" />
        <text x="540" y="246" textAnchor="middle" className={text("divider")} fontSize="13">
          MMD
        </text>
        <text x="540" y="262" textAnchor="middle" fontSize="11" fill="#64748b">
          ÷(N_int + m)
        </text>

        {/* DTC */}
        <rect x="330" y="220" width="100" height="50" rx="8"
              {...lit("dtc")} strokeWidth="1.5" />
        <text x="380" y="246" textAnchor="middle" className={text("dtc")} fontSize="13">
          DTC
        </text>
        <text x="380" y="262" textAnchor="middle" fontSize="11" fill="#64748b">
          ĝ · e_dsm · T_DCO
        </text>

        {/* DSM */}
        <rect x="490" y="290" width="220" height="50" rx="8"
              {...lit("dsm")} strokeWidth="1.5" />
        <text x="600" y="316" textAnchor="middle" className={text("dsm")} fontSize="13">
          MASH 1-1-1 DSM
        </text>
        <text x="600" y="332" textAnchor="middle" fontSize="11" fill="#64748b">
          α = f_out/f_ref − N_int  →  m[k], e_dsm[k]
        </text>

        {/* LMS calibration */}
        <rect x="180" y="220" width="100" height="50" rx="8"
              {...lit("lms")} strokeWidth="1.5" strokeDasharray="4 3" />
        <text x="230" y="246" textAnchor="middle" className={text("lms")} fontSize="13">
          LMS
        </text>
        <text x="230" y="262" textAnchor="middle" fontSize="11" fill="#64748b">
          ĝ update
        </text>

        {/* Signal arrows */}
        <line x1="120" y1="85" x2="180" y2="85" stroke="#475569" strokeWidth="1.5" markerEnd="url(#arr)" />
        <line x1="280" y1="85" x2="330" y2="85" stroke="#475569" strokeWidth="1.5" markerEnd="url(#arr)" />
        <line x1="430" y1="85" x2="490" y2="85" stroke="#475569" strokeWidth="1.5" markerEnd="url(#arr)" />
        <line x1="590" y1="85" x2="640" y2="85" stroke="#475569" strokeWidth="1.5" markerEnd="url(#arr)" />

        {/* DCO -> MMD feedback */}
        <path d="M 540 110 L 540 220" stroke="#475569" strokeWidth="1.5" fill="none" markerEnd="url(#arr)" />

        {/* MMD -> DTC */}
        <line x1="490" y1="245" x2="430" y2="245" stroke="#475569" strokeWidth="1.5" markerEnd="url(#arr)" />

        {/* DTC -> BBPD (negative input) */}
        <path d="M 380 220 L 380 150 L 230 150 L 230 110"
              stroke="#475569" strokeWidth="1.5" fill="none" markerEnd="url(#arr)" />
        <text x="240" y="142" fontSize="10" fill="#64748b">feedback edge</text>

        {/* DSM -> DTC (residue) */}
        <line x1="490" y1="315" x2="430" y2="315" stroke="#475569" strokeWidth="1.5" />
        <line x1="430" y1="315" x2="380" y2="315" stroke="#475569" strokeWidth="1.5" />
        <line x1="380" y1="315" x2="380" y2="270" stroke="#475569" strokeWidth="1.5" markerEnd="url(#arr)" />
        <text x="385" y="290" fontSize="10" fill="#64748b">e_dsm</text>

        {/* DSM -> MMD (m[k]) */}
        <line x1="540" y1="290" x2="540" y2="270" stroke="#475569" strokeWidth="1.5" markerEnd="url(#arr)" />
        <text x="548" y="285" fontSize="10" fill="#64748b">m[k]</text>

        {/* LMS taps */}
        <path d="M 230 220 L 230 165 L 235 165" stroke="#1d4ed8"
              strokeWidth="1" strokeDasharray="3 3" fill="none" />
        <path d="M 280 245 L 330 245" stroke="#1d4ed8"
              strokeWidth="1" strokeDasharray="3 3" fill="none" markerEnd="url(#arr)" />
        <text x="290" y="240" fontSize="10" fill="#1d4ed8">ĝ</text>
      </svg>
      <figcaption className="mt-2 text-center text-xs text-slate-500">
        Our simulator&apos;s block layout (not a tracing of the paper figure).
        Dashed: optional LMS calibration loop.
      </figcaption>
    </figure>
  );
}
