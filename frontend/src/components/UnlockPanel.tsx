import { useState } from "react";
import { api } from "../api";
import { formatClock } from "../session";
import type { ProblemMeta, RunResponse } from "../types";

export interface UnlockInfo {
  part: number;
  resp: RunResponse;
  elapsedPartS: number;
}

interface Props {
  info: UnlockInfo;
  meta: ProblemMeta;
  onClose: () => void;
}

export function UnlockPanel({ info, meta, onClose }: Props) {
  const [solution, setSolution] = useState<string | null>(null);
  const last = info.part >= meta.num_parts;
  const traps = info.resp.tests.filter((t) => t.trap);
  return (
    <div className="fixed inset-y-0 right-0 z-50 w-96 overflow-y-auto border-l border-gray-600 bg-gray-800 p-5 shadow-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-green-400">
          {last ? "All parts complete 🎉" : `Part ${info.part} passed`}
        </h2>
        <button onClick={onClose} className="rounded px-2 text-gray-400 hover:bg-gray-700">
          ✕
        </button>
      </div>
      <dl className="mt-4 space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-gray-400">Time on part</dt>
          <dd>
            {formatClock(info.elapsedPartS)} / {meta.part_budgets_min[info.part - 1]}:00
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-400">Tests passed</dt>
          <dd>
            {info.resp.tests.filter((t) => t.outcome === "passed").length}/{info.resp.tests.length}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-400">Traps</dt>
          <dd>
            {traps.length === 0
              ? "none in this run"
              : traps.map((t) => `${t.trap} ${t.outcome === "passed" ? "✓" : "✗"}`).join(", ")}
          </dd>
        </div>
      </dl>
      {!last && <p className="mt-4 text-sm text-gray-300">Part {info.part + 1} is unlocked. Your code carries forward.</p>}
      <div className="mt-6">
        {solution === null ? (
          <button
            onClick={() => api.getSolution(meta.id, info.part).then((r) => setSolution(r.solution))}
            className="rounded border border-gray-600 px-3 py-1 text-sm text-gray-300 hover:bg-gray-700"
          >
            Show reference solution
          </button>
        ) : (
          <pre className="overflow-x-auto rounded bg-gray-950 p-3 text-xs">{solution}</pre>
        )}
      </div>
    </div>
  );
}
