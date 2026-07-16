import { describe, expect, it } from "vitest";
import { allGreen, budgetStatus, clientStats, findRegressions, formatClock, resolveBuffer } from "./session";
import type { RunResponse, TestResult } from "./types";
import type { SessionState } from "./storage";

const t = (over: Partial<TestResult>): TestResult => ({
  name: "test_x",
  part: 1,
  outcome: "passed",
  duration: 0.01,
  trap: null,
  message: null,
  ...over,
});

const resp = (tests: TestResult[], over: Partial<RunResponse> = {}): RunResponse => ({
  tests,
  stdout: "",
  stderr: "",
  timed_out: false,
  exit_code: 0,
  ...over,
});

describe("findRegressions", () => {
  it("flags earlier-part failures only", () => {
    const tests = [
      t({ name: "old_broken", part: 1, outcome: "failed" }),
      t({ name: "old_fine", part: 1 }),
      t({ name: "new_broken", part: 2, outcome: "failed" }),
    ];
    expect(findRegressions(tests, 2).map((x) => x.name)).toEqual(["old_broken"]);
  });
  it("errors count as regressions too", () => {
    expect(findRegressions([t({ part: 1, outcome: "error" })], 2)).toHaveLength(1);
  });
  it("nothing regresses on part 1", () => {
    expect(findRegressions([t({ outcome: "failed" })], 1)).toHaveLength(0);
  });
});

describe("allGreen", () => {
  it("true when every test passes", () => {
    expect(allGreen(resp([t({})]))).toBe(true);
  });
  it("false on any failure, timeout, or zero tests", () => {
    expect(allGreen(resp([t({ outcome: "failed" })]))).toBe(false);
    expect(allGreen(resp([t({})], { timed_out: true }))).toBe(false);
    expect(allGreen(resp([]))).toBe(false);
  });
});

describe("formatClock", () => {
  it("formats m:ss", () => {
    expect(formatClock(0)).toBe("0:00");
    expect(formatClock(61)).toBe("1:01");
    expect(formatClock(1471)).toBe("24:31");
    expect(formatClock(3600)).toBe("60:00");
  });
});

describe("budgetStatus", () => {
  it("ok under 80%, amber at 80%, red at 100%", () => {
    expect(budgetStatus(0, 15)).toBe("ok");
    expect(budgetStatus(719, 15)).toBe("ok"); // 79.9%
    expect(budgetStatus(720, 15)).toBe("amber"); // 80% of 900s
    expect(budgetStatus(900, 15)).toBe("red");
    expect(budgetStatus(9999, 15)).toBe("red");
  });
});

describe("resolveBuffer", () => {
  const lookup = (buffers: Record<number, string>) => (p: number) => buffers[p] ?? null;
  it("prefers own saved buffer", () => {
    expect(resolveBuffer(2, lookup({ 1: "one", 2: "two" }), "st")).toBe("two");
  });
  it("falls back to previous part (carry-forward)", () => {
    expect(resolveBuffer(3, lookup({ 1: "one" }), "st")).toBe("one");
  });
  it("falls back to starter", () => {
    expect(resolveBuffer(1, lookup({}), "st")).toBe("st");
  });
});

describe("clientStats", () => {
  it("derives elapsed from timestamps", () => {
    const s: SessionState = {
      unlockedPart: 2,
      skippedParts: [1],
      startedAt: 1_000_000,
      partStartedAt: { 1: 1_000_000, 2: 1_060_000 },
      runCount: 7,
      submitCount: 2,
    };
    const stats = clientStats(s, 2, 1_090_000);
    expect(stats.elapsed_total_s).toBe(90);
    expect(stats.elapsed_part_s).toBe(30);
    expect(stats.run_count).toBe(7);
    expect(stats.submit_count).toBe(2);
    expect(stats.skipped_parts).toEqual([1]);
  });
});
