import { useState } from "react";
import { findRegressions } from "../session";
import type { RunResponse, TestResult } from "../types";

interface Props {
  results: RunResponse | null;
  currentPart: number;
  error: string | null;
  notes: string;
  onNotesChange: (v: string) => void;
}

type Tab = "tests" | "output" | "notes";

function Row({ t }: { t: TestResult }) {
  const [open, setOpen] = useState(false);
  const color =
    t.outcome === "passed" ? "text-green-400" : t.outcome === "failed" ? "text-red-400" : "text-orange-400";
  return (
    <div className="border-b border-gray-800 py-1">
      <button className="flex w-full items-center gap-2 text-left" onClick={() => setOpen(!open)}>
        <span className={color}>{t.outcome === "passed" ? "✓" : "✗"}</span>
        <span className="font-mono text-sm">{t.name}</span>
        <span className="text-xs text-gray-500">part {t.part}</span>
        {t.trap && t.outcome !== "passed" && (
          <span className="rounded bg-yellow-900 px-2 py-0.5 text-xs text-yellow-300">
            trap: {t.trap}
          </span>
        )}
        <span className="ml-auto text-xs text-gray-500">{(t.duration * 1000).toFixed(0)}ms</span>
      </button>
      {open && t.message && (
        <pre className="mt-1 overflow-x-auto rounded bg-gray-950 p-2 text-xs text-red-300">
          {t.message}
        </pre>
      )}
    </div>
  );
}

export function ResultsPane({ results, currentPart, error, notes, onNotesChange }: Props) {
  const [tab, setTab] = useState<Tab>("tests");
  const regressions = results ? findRegressions(results.tests, currentPart) : [];
  const tabs: Tab[] = ["tests", "output", "notes"];
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex gap-1 border-b border-gray-700 px-2 py-1">
        {tabs.map((name) => (
          <button
            key={name}
            onClick={() => setTab(name)}
            className={
              "rounded px-3 py-0.5 text-sm capitalize " +
              (tab === name ? "bg-gray-700 font-semibold" : "hover:bg-gray-800")
            }
          >
            {name}
          </button>
        ))}
        {results && (
          <span className="ml-auto self-center text-xs text-gray-500">
            {results.tests.filter((t) => t.outcome === "passed").length}/{results.tests.length} passed
          </span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {tab === "tests" && (
          <>
            {regressions.length > 0 && (
              <div className="mb-2 rounded border-2 border-red-500 bg-red-950 p-3 font-semibold text-red-200">
                ⚠ REGRESSION — {regressions.length} previously-passing earlier-part test
                {regressions.length > 1 ? "s" : ""} now failing:{" "}
                {regressions.map((r) => r.name).join(", ")}
              </div>
            )}
            {error && <div className="mb-2 rounded bg-red-950 p-2 text-red-300">{error}</div>}
            {results?.timed_out && (
              <div className="mb-2 rounded bg-orange-950 p-2 text-orange-300">
                Timed out after 10s — infinite loop? Process was killed.
              </div>
            )}
            {results === null && !error && (
              <span className="text-sm text-gray-500">Run tests to see results.</span>
            )}
            {results !== null && results.tests.length === 0 && !results.timed_out && (
              <pre className="overflow-x-auto text-xs text-gray-400">
                {results.stdout || results.stderr || "No tests collected."}
              </pre>
            )}
            {results?.tests.map((t) => <Row key={`${t.part}:${t.name}`} t={t} />)}
          </>
        )}
        {tab === "output" && (
          <pre className="overflow-x-auto text-xs text-gray-300">
            {results ? (results.stdout || "(no stdout)") + "\n\n--- stderr ---\n" + (results.stderr || "(no stderr)") : "No run yet."}
          </pre>
        )}
        {tab === "notes" && (
          <textarea
            value={notes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Assumptions you'd state out loud…"
            className="h-full w-full resize-none bg-transparent font-mono text-sm outline-none"
          />
        )}
      </div>
    </div>
  );
}
