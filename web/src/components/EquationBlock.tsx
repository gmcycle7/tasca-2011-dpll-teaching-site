import { BlockMath, InlineMath } from "react-katex";

type Props = {
  tex: string;
  caption?: string;
};

export default function EquationBlock({ tex, caption }: Props) {
  return (
    <figure className="my-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="overflow-x-auto">
        <BlockMath math={tex} />
      </div>
      {caption && (
        <figcaption className="mt-2 text-center text-xs text-slate-500">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}

export function Inline({ tex }: { tex: string }) {
  return <InlineMath math={tex} />;
}
