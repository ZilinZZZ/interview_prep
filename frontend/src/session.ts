import type { SessionState } from "./storage";
import type { ClientStats, RunResponse, TestResult } from "./types";

/** Earlier-part tests failing now. Being on part N implies parts < N were green. */
export function findRegressions(tests: TestResult[], currentPart: number): TestResult[] {
  return tests.filter((t) => t.outcome !== "passed" && t.part > 0 && t.part < currentPart);
}

export function allGreen(resp: RunResponse): boolean {
  return !resp.timed_out && resp.tests.length > 0 && resp.tests.every((t) => t.outcome === "passed");
}

export function formatClock(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export type BudgetStatus = "ok" | "amber" | "red";

export function budgetStatus(elapsedS: number, budgetMin: number): BudgetStatus {
  const budgetS = budgetMin * 60;
  if (elapsedS >= budgetS) return "red";
  if (elapsedS >= 0.8 * budgetS) return "amber";
  return "ok";
}

/** Own buffer, else nearest earlier part's buffer (carry-forward), else starter. */
export function resolveBuffer(
  part: number,
  lookup: (p: number) => string | null,
  starter: string,
): string {
  for (let p = part; p >= 1; p--) {
    const b = lookup(p);
    if (b !== null) return b;
  }
  return starter;
}

export function clientStats(s: SessionState, activePart: number, now: number): ClientStats {
  const partStart = s.partStartedAt[activePart] ?? s.startedAt;
  return {
    elapsed_total_s: Math.floor((now - s.startedAt) / 1000),
    elapsed_part_s: Math.floor((now - partStart) / 1000),
    run_count: s.runCount,
    submit_count: s.submitCount,
    skipped_parts: s.skippedParts,
  };
}
