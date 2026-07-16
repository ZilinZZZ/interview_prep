import { describe, expect, it } from "vitest";
import { loadSession } from "./storage";

// vitest runs without a DOM; stub the minimal localStorage surface we need.
const stubLocalStorage = (store: Record<string, string>) => {
  globalThis.localStorage = {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
  } as Storage;
};

describe("loadSession", () => {
  it("returns null on corrupted JSON instead of throwing", () => {
    stubLocalStorage({ "ip:demo:session": "{not valid json" });
    expect(loadSession("demo")).toBeNull();
  });

  it("returns null when nothing is stored", () => {
    stubLocalStorage({});
    expect(loadSession("demo")).toBeNull();
  });

  it("returns the parsed session when valid", () => {
    const s = {
      unlockedPart: 1,
      skippedParts: [],
      startedAt: 123,
      partStartedAt: { 1: 123 },
      runCount: 0,
      submitCount: 0,
    };
    stubLocalStorage({ "ip:demo:session": JSON.stringify(s) });
    expect(loadSession("demo")).toEqual(s);
  });
});
