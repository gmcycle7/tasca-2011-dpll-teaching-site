import { useEffect, useState } from "react";

type Item = { id: string; text: string };

/**
 * Auto-scans h2 headings in the article, gives each an anchor id if
 * one is missing, and renders a sticky right-side TOC on wide screens.
 *
 * Highlights the section currently in view. Pure read-only DOM mutation
 * for anchor ids; layout is unaffected.
 */
export default function StickyToc() {
  const [items, setItems] = useState<Item[]>([]);
  const [active, setActive] = useState<string | null>(null);

  // Rebuild the TOC after the page renders. Run on every route change
  // by watching the URL hash key (caller mounts/unmounts on page swap).
  useEffect(() => {
    const collect = () => {
      const heads = Array.from(
        document.querySelectorAll<HTMLHeadingElement>("article h2"),
      );
      const list: Item[] = heads.map((h, i) => {
        if (!h.id) {
          h.id = `s-${i}-` + (h.textContent ?? "")
            .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")
            .slice(0, 32);
        }
        return { id: h.id, text: h.textContent?.trim() || `Section ${i + 1}` };
      });
      setItems(list);
    };
    // Defer so React has committed children
    const id = window.setTimeout(collect, 0);
    return () => window.clearTimeout(id);
  }, []);

  // Highlight the current section based on viewport position
  useEffect(() => {
    if (items.length === 0) return;
    const onScroll = () => {
      const tops = items.map((it) => {
        const el = document.getElementById(it.id);
        return el ? el.getBoundingClientRect().top : Infinity;
      });
      // The currently-active section is the latest one whose top has
      // crossed ~80 px from the viewport top.
      let idx = 0;
      for (let i = 0; i < tops.length; i++) {
        if (tops[i] < 80) idx = i;
      }
      setActive(items[idx]?.id ?? null);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [items]);

  if (items.length < 2) return null;

  return (
    <aside
      className="hidden xl:block fixed right-6 top-24 z-0 w-56
                 max-h-[70vh] overflow-y-auto rounded-lg border
                 border-slate-200 bg-white/85 p-3 text-xs shadow-sm
                 backdrop-blur dark:border-slate-800
                 dark:bg-slate-900/85"
      aria-label="page contents"
    >
      <div className="mb-2 text-[10px] uppercase tracking-wide text-slate-400">
        on this page
      </div>
      <ol className="space-y-1">
        {items.map((it) => (
          <li key={it.id}>
            <a
              href={`#${it.id}`}
              className={
                "block rounded px-2 py-0.5 !no-underline transition " +
                (active === it.id
                  ? "bg-accent/10 !text-accent-fg"
                  : "!text-slate-600 hover:!text-slate-900 dark:!text-slate-400 dark:hover:!text-slate-100")
              }
            >
              {it.text}
            </a>
          </li>
        ))}
      </ol>
    </aside>
  );
}
