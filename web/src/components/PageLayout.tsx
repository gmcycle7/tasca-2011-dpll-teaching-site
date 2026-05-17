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

// Map a slug to the source page file name (e.g. "fig-architecture" ->
// "FigArchitecture"; "mod-pll-params" -> "ModPllParams") so the
// "edit on GitHub" link points to the right TSX file.
function pageFileFromSlug(slug: string): string {
  const overrides: Record<string, string> = {
    "big-picture": "BigPicture",
    "glossary": "Glossary",
  };
  if (overrides[slug]) return overrides[slug];
  return slug
    .split("-")
    .map((part, idx) => {
      const head = (
        idx === 0
          ? { fig: "Fig", mod: "Mod", ext: "Ext" }[part] ?? part.charAt(0).toUpperCase() + part.slice(1)
          : part.charAt(0).toUpperCase() + part.slice(1)
      );
      return head;
    })
    .join("");
}

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

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 pt-6 text-xs text-slate-500 dark:border-slate-800">
        <Link to="/" className="!text-slate-500 hover:!text-slate-800 dark:hover:!text-slate-200">
          ← back to index
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          {meta.simScript && (
            <span>
              Script: <code>{meta.simScript}</code>
            </span>
          )}
          <a
            href={`https://github.com/gmcycle7/tasca-2011-dpll-teaching-site/blob/main/web/src/pages/${pageFileFromSlug(meta.slug)}.tsx`}
            target="_blank"
            rel="noreferrer"
            className="!text-slate-500 hover:!text-slate-800 dark:hover:!text-slate-200"
          >
            edit this page on GitHub ↗
          </a>
        </div>
      </div>

      <NextPrev slug={meta.slug} />
    </article>
  );
}
