import { useState } from "react";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("bash", bash);

type Props = {
  code: string;
  language?: "python" | "tsx" | "bash";
  filename?: string;
  lineRange?: string;
  startLine?: number;
  caption?: string;
};

export default function CodeBlock({
  code,
  language = "python",
  filename,
  lineRange,
  startLine = 1,
  caption,
}: Props) {
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      /* clipboard not available */
    }
  };

  return (
    <figure className="my-3 overflow-hidden rounded-lg border border-slate-200 bg-white">
      {(filename || lineRange) && (
        <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-3 py-1.5 text-xs">
          <span className="font-mono text-slate-700">
            {filename}
            {lineRange && (
              <span className="text-slate-400">:{lineRange}</span>
            )}
          </span>
          <button
            type="button"
            onClick={onCopy}
            className="rounded px-2 py-0.5 text-[11px] text-slate-500 hover:bg-slate-200 hover:text-slate-800"
          >
            {copied ? "copied ✓" : "copy"}
          </button>
        </div>
      )}
      <div className="overflow-x-auto text-[13px]">
        <SyntaxHighlighter
          language={language}
          style={oneLight}
          showLineNumbers
          startingLineNumber={startLine}
          customStyle={{
            margin: 0,
            background: "white",
            padding: "12px 14px",
            fontSize: "13px",
            lineHeight: "1.55",
          }}
          lineNumberStyle={{
            minWidth: "2.4em",
            paddingRight: "0.9em",
            color: "#94a3b8",
            userSelect: "none",
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
      {caption && (
        <figcaption className="border-t border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}
