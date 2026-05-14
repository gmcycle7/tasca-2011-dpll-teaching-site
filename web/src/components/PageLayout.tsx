import { Link } from "react-router-dom";
import { FigureMeta, readingOrder } from "../data/figureIndex";
import NextPrev from "./NextPrev";

type Props = {
  meta: FigureMeta;
  children: React.ReactNode;
};

const kindBadge: Record<FigureMeta["kind"], string> = {
  concept:   "bg-indigo-100 text-indigo-700 ring-indigo-200",
  figure:    "bg-emerald-100 text-emerald-700 ring-emerald-200",
  module:    "bg-amber-100 text-amber-800 ring-amber-200",
  extension: "bg-rose-100 text-rose-700 ring-rose-200",
};

export default function PageLayout({ meta, children }: Props) {
  const stepIdx = readingOrder.indexOf(meta.slug);
  const stepTotal = readingOrder.length;

  return (
    <article className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={
              "rounded-full px-2.5 py-0.5 text-[11px] font-medium ring-1 ring-inset " +
              kindBadge[meta.kind]
            }
          >
            {meta.kind}
          </span>
          {meta.paperFigGuess && <span className="pill">{meta.paperFigGuess}</span>}
          {stepIdx >= 0 && (
            <span className="pill">
              step {stepIdx + 1} / {stepTotal}
            </span>
          )}
        </div>
        <h1>{meta.title}</h1>
        <p className="text-slate-600">{meta.oneLiner}</p>
      </header>

      <div className="space-y-6">{children}</div>

      <div className="flex items-center justify-between border-t border-slate-200 pt-6 text-xs text-slate-500">
        <Link to="/" className="!text-slate-500 hover:!text-slate-800">
          ← back to index
        </Link>
        {meta.simScript && (
          <span>
            Script: <code>{meta.simScript}</code>
          </span>
        )}
      </div>

      <NextPrev slug={meta.slug} />
    </article>
  );
}
