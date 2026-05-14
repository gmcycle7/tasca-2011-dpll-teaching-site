import { Link } from "react-router-dom";
import { readingOrder, getPageBySlug } from "../data/figureIndex";

export default function NextPrev({ slug }: { slug: string }) {
  const idx = readingOrder.indexOf(slug);
  const prevSlug = idx > 0 ? readingOrder[idx - 1] : null;
  const nextSlug =
    idx >= 0 && idx < readingOrder.length - 1 ? readingOrder[idx + 1] : null;
  const prev = prevSlug ? getPageBySlug(prevSlug) : null;
  const next = nextSlug ? getPageBySlug(nextSlug) : null;

  return (
    <nav className="mt-8 grid gap-3 border-t border-slate-200 pt-6 sm:grid-cols-2">
      {prev ? (
        <Link
          to={`/${prev.slug}`}
          className="card !p-4 !no-underline transition hover:border-accent/40"
        >
          <div className="text-xs uppercase text-slate-400">← previous</div>
          <div className="mt-1 font-medium text-slate-800">{prev.title}</div>
          <div className="mt-1 text-xs text-slate-500">{prev.oneLiner}</div>
        </Link>
      ) : (
        <div />
      )}
      {next ? (
        <Link
          to={`/${next.slug}`}
          className="card !p-4 text-right !no-underline transition hover:border-accent/40"
        >
          <div className="text-xs uppercase text-slate-400">next →</div>
          <div className="mt-1 font-medium text-slate-800">{next.title}</div>
          <div className="mt-1 text-xs text-slate-500">{next.oneLiner}</div>
        </Link>
      ) : (
        <div />
      )}
    </nav>
  );
}
