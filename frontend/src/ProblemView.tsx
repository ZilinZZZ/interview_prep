import { useCallback, useEffect, useRef, useState } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { api } from "./api";
import { allGreen, clientStats, resolveBuffer } from "./session";
import * as store from "./storage";
import type { PartContent, ProblemMeta, RunResponse } from "./types";
import { EditorPane } from "./components/EditorPane";
import { ProblemPane } from "./components/ProblemPane";
import { ResultsPane } from "./components/ResultsPane";
import { UnlockPanel, type UnlockInfo } from "./components/UnlockPanel";

export function ProblemView({ meta }: { meta: ProblemMeta }) {
  const id = meta.id;
  const [session, setSession] = useState(
    () => store.loadSession(id) ?? store.freshSession(Date.now()),
  );
  useEffect(() => store.saveSession(id, session), [id, session]);

  const activePart = Math.min(session.unlockedPart, meta.num_parts);
  const [viewedPart, setViewedPart] = useState(activePart);
  const [parts, setParts] = useState<Record<number, PartContent>>({});
  const [code, setCode] = useState<string | null>(null);
  const [results, setResults] = useState<RunResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState(() => store.loadNotes(id));
  const [unlockInfo, setUnlockInfo] = useState<UnlockInfo | null>(null);
  const runSeq = useRef(0);

  // fetch viewed part + part 1 (for the starter) lazily
  useEffect(() => {
    for (const n of new Set([viewedPart, 1])) {
      if (!parts[n]) {
        api.getPart(id, n).then((p) => setParts((prev) => ({ ...prev, [n]: p })));
      }
    }
  }, [id, viewedPart, parts]);

  // initialize the buffer once part 1 (starter) is available
  const starter = parts[1]?.starter ?? null;
  useEffect(() => {
    if (code === null && starter !== null) {
      setCode(resolveBuffer(activePart, (p) => store.loadBuffer(id, p), starter));
    }
  }, [code, starter, activePart, id]);

  const onCodeChange = useCallback(
    (value: string) => {
      setCode(value);
      store.saveBuffer(id, activePart, value);
    },
    [id, activePart],
  );

  const doRun = useCallback(
    async (mode: "run" | "submit") => {
      if (code === null) return;
      const seq = ++runSeq.current;
      setRunning(true);
      setError(null);
      const stats = clientStats(session, activePart, Date.now());
      setSession((s) =>
        mode === "run"
          ? { ...s, runCount: s.runCount + 1 }
          : { ...s, submitCount: s.submitCount + 1 },
      );
      try {
        const resp = await api.run(id, {
          part: activePart,
          code,
          mode,
          client_stats: stats,
        });
        if (seq !== runSeq.current) return; // stale — a newer run superseded us
        setResults(resp);
        if (mode === "submit" && allGreen(resp)) {
          const elapsedPartS = clientStats(session, activePart, Date.now()).elapsed_part_s;
          setUnlockInfo({ part: activePart, resp, elapsedPartS });
          if (activePart < meta.num_parts) {
            store.saveBuffer(id, activePart + 1, code); // carry forward
            setSession((s) => ({
              ...s,
              unlockedPart: activePart + 1,
              partStartedAt: { ...s.partStartedAt, [activePart + 1]: Date.now() },
            }));
            setViewedPart(activePart + 1);
          }
        }
      } catch (e) {
        if (seq === runSeq.current) setError(String(e));
      } finally {
        if (seq === runSeq.current) setRunning(false);
      }
    },
    [id, activePart, code, session],
  );

  const onReset = useCallback(() => {
    const target =
      activePart === 1 ? (starter ?? "") : (store.loadBuffer(id, activePart - 1) ?? starter ?? "");
    if (window.confirm("Reset editor to starting state for this part?")) {
      setCode(target);
      store.saveBuffer(id, activePart, target);
    }
  }, [id, activePart, starter]);

  const onReveal = useCallback(
    (nextPart: number) => {
      if (
        !window.confirm(
          `Reveal Part ${nextPart} without passing Part ${activePart}? ` +
            `Part ${activePart} will be logged as skipped.`,
        )
      )
        return;
      if (code !== null) store.saveBuffer(id, nextPart, code);
      setSession((s) => ({
        ...s,
        unlockedPart: nextPart,
        skippedParts: [...new Set([...s.skippedParts, activePart])],
        partStartedAt: { ...s.partStartedAt, [nextPart]: Date.now() },
      }));
      setViewedPart(nextPart);
    },
    [id, code, activePart],
  );

  // when the active part changes (unlock/reveal), load that part's buffer
  const prevPart = useRef(activePart);
  useEffect(() => {
    if (prevPart.current !== activePart) {
      prevPart.current = activePart;
      setCode(resolveBuffer(activePart, (p) => store.loadBuffer(id, p), starter ?? ""));
    }
  }, [activePart, id, starter]);

  const onNotesChange = useCallback(
    (v: string) => {
      setNotes(v);
      store.saveNotes(id, v);
    },
    [id],
  );

  return (
    <div className="flex h-screen flex-col">
      {unlockInfo && (
        <UnlockPanel info={unlockInfo} meta={meta} onClose={() => setUnlockInfo(null)} />
      )}
      <header className="flex items-center gap-4 border-b border-gray-700 px-4 py-2">
        <a href="#/" className="text-sm text-gray-400 hover:text-gray-200">
          ← Problems
        </a>
        <span className="font-semibold">{meta.title}</span>
        <span className="text-sm text-gray-500">{meta.company}</span>
      </header>
      <Group orientation="vertical" className="flex-1">
        <Panel defaultSize={70} minSize={30}>
          <Group orientation="horizontal">
            <Panel defaultSize={40} minSize={20}>
              <ProblemPane
                meta={meta}
                viewedPart={viewedPart}
                unlockedPart={session.unlockedPart}
                content={parts[viewedPart] ?? null}
                onSelectPart={setViewedPart}
                onReveal={onReveal}
                timer={null}
              />
            </Panel>
            <Separator className="w-1 bg-gray-700 hover:bg-gray-500" />
            <Panel minSize={30}>
              <EditorPane
                code={code ?? "# loading…"}
                onChange={onCodeChange}
                onRun={() => doRun("run")}
                onSubmit={() => doRun("submit")}
                onReset={onReset}
                running={running}
              />
            </Panel>
          </Group>
        </Panel>
        <Separator className="h-1 bg-gray-700 hover:bg-gray-500" />
        <Panel defaultSize={30} minSize={10}>
          <ResultsPane
            results={results}
            currentPart={activePart}
            error={error}
            notes={notes}
            onNotesChange={onNotesChange}
          />
        </Panel>
      </Group>
    </div>
  );
}
