# Local Interview Practice Platform — Design

Date: 2026-07-15
Status: Approved (user), pending implementation plan

## Goal

A local web app that mimics the HackerRank/LeetCode live-coding experience for
practicing multi-part "practical coding" interview rounds. Problem statement on
the left, Monaco editor on the right, test results below. Run tests, submit,
get graded. Single user, localhost only, no auth. A practice harness, not a
judge.

The distinguishing feature: **multi-part problems** that reveal requirements
incrementally. Part 1 is easy, Part 2 breaks your Part 1 design, Part 3 adds a
dimension. Editor code carries forward between parts; earlier parts' tests keep
running so regressions surface loudly.

## Architecture decision

**Stateless backend, frontend owns session state.** The backend serves problem
content, runs pytest, and appends logs/snapshots. Part-unlock status, timer,
run counts, and editor buffers live in browser localStorage. Gating is
honor-system (there is a "reveal anyway" button by design), so server-side
enforcement buys nothing. Rejected alternative: backend-owned session state —
doubles API surface and adds sync bugs for a single-user local tool.

## Repo layout

Lives at the root of this repo (`interview_prep`), alongside the markdown
coaching layer (CLAUDE.md, interviews/). Session logs are shared so the
coaching layer can read them.

```
backend/               # FastAPI app + requirements.txt
frontend/              # Vite + React + TS + Tailwind + Monaco
problems/              # one folder per problem (format below)
sessions/              # SHARED: coaching scorecards (YYYY-MM-DD-<round>.md)
  <problem-id>/        #   platform submit logs (<timestamp>.json)
    keystrokes/        #   30s editor snapshots (<iso-ts>.py)
package.json           # root: `npm run dev` → concurrently(uvicorn, vite)
Makefile               # `make dev` alias; npm is the primary path on Windows
```

## Stack

- Frontend: React + Vite + TypeScript, Tailwind, `@monaco-editor/react`.
- Backend: Python 3.12, FastAPI, uvicorn bound to `127.0.0.1` explicitly.
- Storage: filesystem only. No database.
- Execution: `subprocess.run` of pytest (with `pytest-json-report`) in a temp
  dir, `timeout=10`, hard kill on timeout (Windows: `taskkill /T /F` on the
  process tree).

Clone-and-run target: `npm install && pip install -r backend/requirements.txt`,
then `npm run dev`. Under a minute.

## Problem format (filesystem, git-friendly)

```
problems/
  affirm-payment-allocator/
    meta.yaml
    part-1/
      statement.md
      starter.py          # only in part-1; later parts inherit editor state
      tests.py
      solution.py         # reference, gated behind a button client-side
    part-2/
      statement.md
      tests.py
      solution.py
    part-3/
      ...
```

`meta.yaml`:

```yaml
id: affirm-payment-allocator
title: Installment Payment Allocator
company: Affirm
round: practical-coding
language: python        # keep the seam; do not hardcode .py everywhere
time_limit_min: 60
part_budgets_min: [15, 15, 15]
tags: [ledger, money, allocation]
```

Statements are plain markdown rendered with code highlighting. Authoring a new
problem = making a folder. No admin UI.

## Test format

Plain pytest. Tests import from a fixed module name:

```python
from solution import Loan, allocate_payment
```

Three visibility levels via markers:

- `@pytest.mark.sample` — visible in the statement, runs on "Run"
- default — hidden, runs on "Submit"
- `@pytest.mark.trap("float-precision")` — hidden, runs on Submit; when it
  fails, results show the trap label so a known trap reads as a known trap,
  not just a red X. Label is the marker's positional arg.

## Backend API

All endpoints stateless; no endpoint accepts a filesystem path from the
client. Problem ids validated with `^[a-z0-9-]+$` AND a resolved-path-under-
`problems/` check.

- `GET /api/problems` — list problems (from each meta.yaml).
- `GET /api/problems/{id}/parts/{n}` — statement markdown, starter code
  (part 1 only), and the source of sample-marked tests for inline display.
- `GET /api/problems/{id}/parts/{n}/solution` — reference solution. Client
  gates it behind a collapsed "show reference solution" button.
- `POST /api/problems/{id}/run` — body `{part, code, mode: "run"|"submit",
  client_stats}`. Returns structured results (below). When `mode ==
  "submit"`, the server appends the session log; `client_stats` carries the
  client-owned clock and counters (`elapsed_total_s`, `elapsed_part_s`,
  `run_count`, `submit_count`).
- `POST /api/problems/{id}/snapshot` — editor buffer, written to
  `sessions/<id>/keystrokes/<iso-ts>.py`. Called every 30s by the client.

## Test execution

Per run, in a fresh temp dir:

1. Write editor buffer to `solution.py`.
2. Copy `part-K/tests.py` → `test_part_K.py` for every K ≤ current part.
3. Inject a `conftest.py` that registers the `sample`/`trap` markers and
   records each test's part number (from filename) and trap label into the
   JSON report.
4. `subprocess.run(pytest --json-report ...)`, `timeout=10`. Run mode adds
   `-m sample`; submit mode runs everything.
5. Capture stdout, stderr, and the JSON report separately. Return structured
   results — never a raw traceback string as the only signal.

Result shape per test: `{name, part, outcome, duration, trap_label?,
assertion_diff?}` plus run-level `{stdout, stderr, timed_out}`.

**Concurrency:** one run at a time. A new run kills the in-flight subprocess
(process-tree kill) and starts fresh.

**Regression rule:** being on Part N implies Parts 1…N-1 were green at unlock,
so any failing test with `part < current_part` IS a regression — no history
needed. Backend tags parts; frontend renders the loud banner.

## UI — three resizable panes

**Left — Problem.** Rendered statement for the current part only. Part tabs:
completed parts clickable to re-read, future parts locked (lock icon) with a
"reveal anyway" escape hatch — using it marks the prior part as skipped in the
log. Sample tests inline. Timer display:
`24:31 / 60:00 · Part 2: 9:31 / 15:00` — amber at 80% of part budget, red at
100%, never blocks anything. Timer starts on first open of the problem and
persists to localStorage; no pause.

**Right — Editor.** Monaco, Python, 4-space tabs, bracket matching. Buffer
persists to localStorage per (problem, part); Part N+1 starts with Part N's
buffer. Ctrl+Enter = Run, Ctrl+Shift+Enter = Submit (Cmd variants also bound).
Reset-to-starter button with confirm.

**Bottom — Results.** Tabs: Tests / Output / Notes.

- Tests: per-test pass/fail, name, assertion diff, duration. Trap failures
  show their label. Regression banner (earlier-part test failing) is loud —
  a banner, not a subtle red row.
- Output: raw stdout/stderr so print-debugging works.
- Notes: scratch textarea saved per problem (localStorage) — for stating
  assumptions out loud.

**On Submit:** run all tests through the current part. All green → unlock next
part, slide-in panel with time taken, tests passed, traps hit/missed, and a
collapsed "show reference solution" button. Any red → show failures, don't
unlock, don't lecture.

## Session log

On every submit, append `sessions/<problem-id>/<timestamp>.json`:

```json
{
  "problem_id": "...",
  "part": 2,
  "elapsed_total_s": 1471,
  "elapsed_part_s": 571,
  "run_count": 7,
  "submit_count": 2,
  "traps_failed": ["float-precision"],
  "regressions": [],
  "skipped_parts": [],
  "final_code": "..."
}
```

Editor buffer also snapshots every 30s to `sessions/<problem-id>/keystrokes/`
so code-at-minute-15 can be reconstructed. This log is the input to the
coaching layer — complete and boring.

## Security

Localhost, executes Python the user typed themselves — thin threat model, but:

- Bind `127.0.0.1` explicitly, never `0.0.0.0`.
- No filesystem paths from the client; server resolves and validates ids.
- No remote-problem-loading feature, ever, without a real sandbox.

## Out of scope (do not build; ask first if they seem needed)

Auth/users/accounts, Docker sandboxing, multi-language support (Python only,
but language stays in meta.yaml as a seam), leaderboards/streaks/gamification,
cloud deploy, CI, problem-authoring admin UI.

## Build order

1. Backend: problem loading, `GET /problems`, `GET /problems/{id}/parts/{n}`.
2. Backend: `POST /run` — code in, pytest results out. Solid before UI work.
3. Frontend: three-pane shell, Monaco wired, statement rendering.
4. Wire Run → results.
   — **Ship 1–4 as a working single-part harness before starting 5.**
5. Submit, part gating, unlock flow.
6. Timer, regression detection, session logging, snapshots.
7. Seed problem: `affirm-payment-allocator`, 3 parts, trap tests for float
   precision and remainder distribution.

## Seed problem: affirm-payment-allocator

The reference implementation of the format:

- **Part 1:** allocate a payment across installments oldest-first, return
  remaining balances.
- **Part 2:** partial payments and overpayment — leftover cascades to the next
  installment.
- **Part 3:** each installment has fees and principal; fees are paid first
  within an installment.
- Starter code uses **floats on purpose**; trap tests catch the precision
  drift. This trap is the single most valuable thing in the platform.
