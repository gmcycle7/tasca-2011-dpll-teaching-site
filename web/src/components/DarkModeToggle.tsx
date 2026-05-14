import { useEffect, useState } from "react";

const STORAGE_KEY = "tasca-dpll-theme";

function preferredTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === "dark" || saved === "light") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function apply(theme: "light" | "dark") {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export default function DarkModeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(() => preferredTheme());

  useEffect(() => {
    apply(theme);
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* private mode */
    }
  }, [theme]);

  return (
    <button
      type="button"
      onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
      title={`switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className="rounded px-2 py-1 text-sm text-slate-600 hover:bg-slate-100
                 dark:text-slate-300 dark:hover:bg-slate-800"
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}
