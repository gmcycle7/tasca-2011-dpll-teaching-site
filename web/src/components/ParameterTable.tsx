type Row = {
  symbol: string;
  description: string;
  value: string;
  source: "PAPER" | "DERIVED" | "ESTIMATED" | "OPEN";
  notes?: string;
};

const sourceColor: Record<Row["source"], string> = {
  PAPER:     "bg-emerald-100 text-emerald-800 ring-emerald-200",
  DERIVED:   "bg-sky-100 text-sky-800 ring-sky-200",
  ESTIMATED: "bg-amber-100 text-amber-800 ring-amber-200",
  OPEN:      "bg-rose-100 text-rose-800 ring-rose-200",
};

export default function ParameterTable({ rows }: { rows: Row[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>
            <th className="px-3 py-2">Symbol</th>
            <th className="px-3 py-2">Description</th>
            <th className="px-3 py-2">Value</th>
            <th className="px-3 py-2">Source</th>
            <th className="px-3 py-2">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white">
          {rows.map((r) => (
            <tr key={r.symbol}>
              <td className="px-3 py-2 font-mono text-slate-800">{r.symbol}</td>
              <td className="px-3 py-2 text-slate-700">{r.description}</td>
              <td className="px-3 py-2 font-mono text-slate-700">{r.value}</td>
              <td className="px-3 py-2">
                <span
                  className={
                    "inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset " +
                    sourceColor[r.source]
                  }
                >
                  {r.source}
                </span>
              </td>
              <td className="px-3 py-2 text-slate-500">{r.notes ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export type { Row as ParameterRow };
