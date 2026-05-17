import { lazy, Suspense } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { figureIndex, FigureMeta } from "./data/figureIndex";
import DarkModeToggle from "./components/DarkModeToggle";
import ReadingProgress from "./components/ReadingProgress";

// Eagerly load the home page — it's small and renders the index
import Home from "./pages/Home";

// Lazy-load every figure / module / extension page so each becomes
// its own chunk. The KaTeX + Prism imports inside these pages now
// only show up when the user navigates to a page that uses them.
const BigPicture          = lazy(() => import("./pages/BigPicture"));
const FigArchitecture     = lazy(() => import("./pages/FigArchitecture"));
const FigBBPDLinearize    = lazy(() => import("./pages/FigBBPDLinearize"));
const FigDTCCancellation  = lazy(() => import("./pages/FigDTCCancellation"));
const FigPhaseNoise       = lazy(() => import("./pages/FigPhaseNoise"));
const FigFracSpur         = lazy(() => import("./pages/FigFracSpur"));
const FigLockTransient    = lazy(() => import("./pages/FigLockTransient"));
const FigLMS              = lazy(() => import("./pages/FigLMS"));

const ModPllParams        = lazy(() => import("./pages/ModPllParams"));
const ModDsm              = lazy(() => import("./pages/ModDsm"));
const ModFractionalDivider = lazy(() => import("./pages/ModFractionalDivider"));
const ModDco              = lazy(() => import("./pages/ModDco"));
const ModDtc              = lazy(() => import("./pages/ModDtc"));
const ModBbpd             = lazy(() => import("./pages/ModBbpd"));
const ModLoopFilter       = lazy(() => import("./pages/ModLoopFilter"));
const ModPhaseNoise       = lazy(() => import("./pages/ModPhaseNoise"));
const ModJitterSpurs      = lazy(() => import("./pages/ModJitterSpurs"));
const ModPllModel         = lazy(() => import("./pages/ModPllModel"));

const ExtDeepViz          = lazy(() => import("./pages/ExtDeepViz"));
const ExtKbbTracker       = lazy(() => import("./pages/ExtKbbTracker"));
const ExtAllan            = lazy(() => import("./pages/ExtAllan"));
const ExtNtf              = lazy(() => import("./pages/ExtNtf"));
const ExtMultibitTdc      = lazy(() => import("./pages/ExtMultibitTdc"));
const ExtSensitivity      = lazy(() => import("./pages/ExtSensitivity"));
const ExtIntegrated       = lazy(() => import("./pages/ExtIntegrated"));

const Glossary            = lazy(() => import("./pages/Glossary"));

const pageComponents: Record<string, React.ComponentType> = {
  "big-picture": BigPicture,
  "fig-architecture": FigArchitecture,
  "fig-dtc-cancellation": FigDTCCancellation,
  "fig-bbpd-linearize": FigBBPDLinearize,
  "fig-lock-transient": FigLockTransient,
  "fig-phase-noise": FigPhaseNoise,
  "fig-frac-spur": FigFracSpur,
  "fig-lms": FigLMS,
  "mod-pll-params": ModPllParams,
  "mod-dsm": ModDsm,
  "mod-fractional-divider": ModFractionalDivider,
  "mod-dco": ModDco,
  "mod-dtc": ModDtc,
  "mod-bbpd": ModBbpd,
  "mod-loop-filter": ModLoopFilter,
  "mod-phase-noise": ModPhaseNoise,
  "mod-jitter-spurs": ModJitterSpurs,
  "mod-pll-model": ModPllModel,
  "ext-deepviz": ExtDeepViz,
  "ext-kbb-tracker": ExtKbbTracker,
  "ext-allan": ExtAllan,
  "ext-ntf": ExtNtf,
  "ext-multibit-tdc": ExtMultibitTdc,
  "ext-sensitivity": ExtSensitivity,
  "ext-integrated": ExtIntegrated,
  "glossary": Glossary,
};

const navOrder: FigureMeta["kind"][] = [
  "concept",
  "figure",
  "extension",
  "module",
];

function PageFallback() {
  return (
    <div className="card flex items-center gap-3 text-sm text-slate-500">
      <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-accent" />
      loading page…
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <ReadingProgress />
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/85 backdrop-blur
                         dark:border-slate-800 dark:bg-slate-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <NavLink to="/" className="!no-underline">
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Tasca 2011 DPLL — behavioral teaching site
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Recreated plots only. NOT a silicon reproduction.
              </span>
            </div>
          </NavLink>
          <details className="md:hidden">
            <summary className="cursor-pointer rounded px-2 py-1 text-sm text-slate-600">
              menu
            </summary>
            <NavGrid />
          </details>
          <div className="hidden items-center gap-2 md:flex">
            <NavGrid />
            <DarkModeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-10">
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Home />} />
            {figureIndex.map((f) => {
              const C = pageComponents[f.slug];
              if (!C) return null;
              return <Route key={f.slug} path={`/${f.slug}`} element={<C />} />;
            })}
            <Route
              path="*"
              element={
                <div className="card">
                  <h1>Not found</h1>
                  <p>Use the top nav to pick a page.</p>
                </div>
              }
            />
          </Routes>
        </Suspense>
      </main>

      <footer className="border-t border-slate-200 bg-white
                         dark:border-slate-800 dark:bg-slate-950">
        <div className="mx-auto max-w-6xl px-6 py-6 text-xs text-slate-500 dark:text-slate-400">
          Behavioral approximation built from the abstract + open-access
          tutorial material; every plot here is generated by our Python
          simulator under <code>sim/</code>, not copied from the paper.
          Citation: D. Tasca <i>et al.</i>, IEEE JSSC 46(12), 2745–2758,
          Dec 2011.
        </div>
      </footer>
    </div>
  );
}

function NavGrid() {
  return (
    <nav className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
      {navOrder.map((kind) => (
        <div key={kind} className="flex items-center gap-1">
          <span className="text-[10px] uppercase tracking-wide text-slate-400">
            {kind}
          </span>
          {figureIndex
            .filter((f) => f.kind === kind)
            .map((f) => (
              <NavLink
                key={f.slug}
                to={`/${f.slug}`}
                className={({ isActive }) =>
                  "rounded px-1.5 py-0.5 " +
                  (isActive
                    ? "bg-accent/10 text-accent-fg"
                    : "text-slate-600 hover:text-slate-900")
                }
              >
                {f.shortLabel}
              </NavLink>
            ))}
        </div>
      ))}
    </nav>
  );
}
