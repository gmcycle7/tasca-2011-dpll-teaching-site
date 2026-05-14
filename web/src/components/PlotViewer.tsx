import { useState } from "react";

type Props = {
  src: string;
  alt: string;
  caption?: string;
};

export default function PlotViewer({ src, alt, caption }: Props) {
  const [errored, setErrored] = useState(false);

  return (
    <figure className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      {errored ? (
        <div className="flex items-center justify-center p-8 text-center text-sm text-slate-500">
          <span>
            Plot <code>{src}</code> not found.
            <br />
            Run the matching simulation script and then{" "}
            <code>npm run copy:figures</code> to refresh.
          </span>
        </div>
      ) : (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          className="block w-full"
          onError={() => setErrored(true)}
        />
      )}
      <figcaption className="border-t border-slate-200 bg-slate-50 px-4 py-2 text-xs text-slate-600">
        <span className="font-medium">{caption ?? alt}</span>
        <span className="ml-2 text-slate-400">
          (behavioral approximation — recreated from our own simulator)
        </span>
      </figcaption>
    </figure>
  );
}
