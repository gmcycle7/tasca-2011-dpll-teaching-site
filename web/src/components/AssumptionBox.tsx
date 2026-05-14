type Kind = "info" | "warn" | "limit";

const styles: Record<Kind, string> = {
  info:  "border-sky-200 bg-sky-50    text-sky-900",
  warn:  "border-amber-200 bg-amber-50 text-amber-900",
  limit: "border-rose-200 bg-rose-50   text-rose-900",
};

const labels: Record<Kind, string> = {
  info: "Modeling assumption",
  warn: "Caveat",
  limit: "Known limitation",
};

type Props = {
  kind?: Kind;
  title?: string;
  children: React.ReactNode;
};

export default function AssumptionBox({
  kind = "info",
  title,
  children,
}: Props) {
  return (
    <aside className={`rounded-lg border p-4 text-sm ${styles[kind]}`}>
      <div className="mb-1 text-xs font-semibold uppercase tracking-wide opacity-80">
        {title ?? labels[kind]}
      </div>
      <div className="space-y-1 leading-relaxed">{children}</div>
    </aside>
  );
}
