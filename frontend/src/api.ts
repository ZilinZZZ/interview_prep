import type { PartContent, ProblemMeta, RunRequestBody, RunResponse } from "./types";

async function j<T>(r: Promise<Response>): Promise<T> {
  const resp = await r;
  if (!resp.ok) throw new Error(`${resp.status}: ${await resp.text()}`);
  return resp.json() as Promise<T>;
}

const post = (url: string, body: unknown) =>
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const api = {
  listProblems: () => j<ProblemMeta[]>(fetch("/api/problems")),
  getPart: (id: string, n: number) => j<PartContent>(fetch(`/api/problems/${id}/parts/${n}`)),
  getSolution: (id: string, n: number) =>
    j<{ solution: string }>(fetch(`/api/problems/${id}/parts/${n}/solution`)),
  run: (id: string, body: RunRequestBody) => j<RunResponse>(post(`/api/problems/${id}/run`, body)),
  snapshot: (id: string, code: string) => post(`/api/problems/${id}/snapshot`, { code }),
};
