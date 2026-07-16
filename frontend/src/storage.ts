export interface SessionState {
  unlockedPart: number;
  skippedParts: number[];
  startedAt: number; // epoch ms; timer starts on first open, never pauses
  partStartedAt: Record<number, number>;
  runCount: number;
  submitCount: number;
}

export function freshSession(now: number): SessionState {
  return {
    unlockedPart: 1,
    skippedParts: [],
    startedAt: now,
    partStartedAt: { 1: now },
    runCount: 0,
    submitCount: 0,
  };
}

const k = (id: string, suffix: string) => `ip:${id}:${suffix}`;

export function loadSession(id: string): SessionState | null {
  const raw = localStorage.getItem(k(id, "session"));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SessionState;
  } catch {
    return null;
  }
}
export function saveSession(id: string, s: SessionState): void {
  localStorage.setItem(k(id, "session"), JSON.stringify(s));
}
export function loadBuffer(id: string, part: number): string | null {
  return localStorage.getItem(k(id, `buffer:${part}`));
}
export function saveBuffer(id: string, part: number, code: string): void {
  localStorage.setItem(k(id, `buffer:${part}`), code);
}
export function loadNotes(id: string): string {
  return localStorage.getItem(k(id, "notes")) ?? "";
}
export function saveNotes(id: string, v: string): void {
  localStorage.setItem(k(id, "notes"), v);
}
