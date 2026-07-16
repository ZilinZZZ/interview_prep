import Markdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import type { PartContent, ProblemMeta } from "../types";
import type { TimerInfo } from "./TimerBar";
import { TimerBar } from "./TimerBar";

interface Props {
  meta: ProblemMeta;
  viewedPart: number;
  unlockedPart: number;
  content: PartContent | null;
  onSelectPart: (n: number) => void;
  onReveal: (n: number) => void;
  timer: TimerInfo | null;
}

export function ProblemPane({
  meta,
  viewedPart,
  unlockedPart,
  content,
  onSelectPart,
  onReveal,
  timer,
}: Props) {
  const partNums = Array.from({ length: meta.num_parts }, (_, i) => i + 1);
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-1 border-b border-gray-700 px-2 py-1">
        {partNums.map((n) => {
          const unlocked = n <= unlockedPart;
          const revealable = n === unlockedPart + 1;
          return (
            <button
              key={n}
              onClick={() => (unlocked ? onSelectPart(n) : revealable ? onReveal(n) : undefined)}
              disabled={!unlocked && !revealable}
              className={
                "rounded px-3 py-1 text-sm " +
                (n === viewedPart
                  ? "bg-gray-700 font-semibold"
                  : unlocked
                    ? "hover:bg-gray-800"
                    : revealable
                      ? "text-gray-500 hover:bg-gray-800"
                      : "cursor-not-allowed text-gray-600")
              }
              title={!unlocked ? (revealable ? "Reveal anyway" : "Locked") : undefined}
            >
              {unlocked ? `Part ${n}` : `🔒 Part ${n}`}
            </button>
          );
        })}
        <div className="ml-auto">{timer && <TimerBar info={timer} />}</div>
      </div>
      <div className="statement flex-1 overflow-y-auto p-4 text-sm">
        {content ? (
          <>
            <Markdown rehypePlugins={[rehypeHighlight]}>{content.statement}</Markdown>
            {content.sample_tests && (
              <>
                <h3 className="mt-4 font-bold">Sample tests</h3>
                <pre>
                  <code>{content.sample_tests}</code>
                </pre>
              </>
            )}
          </>
        ) : (
          <span className="text-gray-500">Loading…</span>
        )}
      </div>
    </div>
  );
}
