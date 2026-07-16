import { useEffect, useState } from "react";
import { api } from "./api";
import type { ProblemMeta } from "./types";
import { ProblemView } from "./ProblemView";

function useHashRoute(): string {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

export default function App() {
  const [problems, setProblems] = useState<ProblemMeta[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const hash = useHashRoute();

  useEffect(() => {
    api.listProblems().then(setProblems).catch((e) => setError(String(e)));
  }, []);

  const match = hash.match(/^#\/p\/([a-z0-9-]+)$/);
  const selected = match && problems?.find((p) => p.id === match[1]);

  if (error) return <div className="p-8 text-red-400">Backend unreachable: {error}</div>;
  if (!problems) return <div className="p-8 text-gray-400">Loading…</div>;
  if (selected) return <ProblemView key={selected.id} meta={selected} />;

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Problems</h1>
      {problems.length === 0 && (
        <p className="text-gray-400">No problems found. Add a folder under problems/.</p>
      )}
      <ul className="space-y-3">
        {problems.map((p) => (
          <li key={p.id}>
            <a
              href={`#/p/${p.id}`}
              className="block rounded-lg border border-gray-700 p-4 hover:border-gray-500"
            >
              <div className="flex items-baseline justify-between">
                <span className="font-semibold">{p.title}</span>
                <span className="text-sm text-gray-400">
                  {p.company} · {p.num_parts} parts · {p.time_limit_min} min
                </span>
              </div>
              <div className="mt-1 text-sm text-gray-500">{p.tags.join(", ")}</div>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
