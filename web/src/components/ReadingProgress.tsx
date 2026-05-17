import { useEffect, useState } from "react";

/**
 * Thin horizontal bar at the very top of the page that tracks how far
 * the reader has scrolled through the current article. Pure visual
 * aid; no behavior is gated on it.
 */
export default function ReadingProgress() {
  const [pct, setPct] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement;
      const total = h.scrollHeight - h.clientHeight;
      setPct(total > 0 ? (h.scrollTop / total) * 100 : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div
      aria-hidden
      className="fixed left-0 top-0 z-20 h-[3px] w-full bg-transparent"
    >
      <div
        className="h-full bg-accent transition-[width] duration-100"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
