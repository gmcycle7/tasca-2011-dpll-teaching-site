import { getPageBySlug } from "../data/figureIndex";
import PageLayout from "../components/PageLayout";
import { Inline } from "../components/EquationBlock";
import { glossary } from "../data/glossary";

const meta = getPageBySlug("glossary")!;

export default function Glossary() {
  return (
    <PageLayout meta={meta}>
      <section>
        <p>
          One row per symbol used elsewhere on the site. &quot;Defined in&quot;
          points to either a dataclass field, a function, or a derivation.
          Hover over the rendered math to copy.
        </p>
      </section>

      <section>
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Symbol</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Units</th>
                <th className="px-3 py-2">Defined in</th>
                <th className="px-3 py-2">Used for</th>
                <th className="px-3 py-2">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white align-top">
              {glossary.map((g) => (
                <tr key={g.symbol}>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <Inline tex={g.symbol} />
                  </td>
                  <td className="px-3 py-2 text-slate-800">{g.name}</td>
                  <td className="px-3 py-2 font-mono text-slate-500">
                    {g.units}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-500">
                    {g.definedIn}
                  </td>
                  <td className="px-3 py-2 text-slate-600">{g.usedFor}</td>
                  <td className="px-3 py-2 text-slate-500">{g.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </PageLayout>
  );
}
