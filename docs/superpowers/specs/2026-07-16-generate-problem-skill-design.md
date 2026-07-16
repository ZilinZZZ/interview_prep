# Generate-Problem Skill — Design

Date: 2026-07-16
Status: Approved

## Goal

A repeatable way to generate new practice problems for a given interview,
invoked as `/generate-problem <interview>` inside a Claude Code session.
No LLM-calling infrastructure: the skill carries the authoring judgment,
a validation script carries the mechanical guarantees. A generated problem
is a normal folder under `problems/` and appears in the app on refresh.

## Components

### 1. Skill: `.claude/skills/generate-problem/SKILL.md`

Invocation: `/generate-problem <interview>`, where `<interview>` names a spec
file in `interviews/` (e.g. `affirm-practical-coding`). If the argument is
missing or doesn't match a spec file, list the available specs and stop.

Workflow the skill encodes:

1. **Read the interview spec fully.** The spec is the source of truth for
   domain flavor, structure (part count, budgets), difficulty ceiling,
   traps, and anti-patterns.
2. **Rotate domains.** Read existing `problems/*/meta.yaml` tags and recent
   `sessions/` scorecards; pick a domain from the spec's flavor list that
   has not been used recently. Never repeat the most recent problem's domain.
3. **Author the problem folder** to the format contract (below). Part count
   and `part_budgets_min` come from the spec's structure section.
4. **Validate**: run `python scripts/validate_problem.py <problem-id>` and
   fix failures until it exits 0. Only then report the problem as ready.
5. **Report**: problem id, title, domain, part count — but never the traps,
   edge cases, or solutions (the user is the candidate).

Content rules (restated in the skill, derived from CLAUDE.md + spec):

- Starter code is deliberately imperfect — mediocre naming, a missing edge
  case, or a wrong-type-for-the-job — and never annotated as such.
- Each part breaks the naive shape of the previous part.
- Every trap named in the spec's Traps section gets at least one
  `@pytest.mark.trap("label")` test in some part.
- Statements withhold the edge-case list; concrete example input/output only.
- Difficulty ceiling per the spec (e.g. for Affirm: dicts, lists, sorting,
  grouping — no DP/graphs).

### 2. Validator: `scripts/validate_problem.py`

`python scripts/validate_problem.py <problem-id>` — stdlib + yaml + pytest
only. Also usable standalone for hand-written problems.

Structural checks:

- Problem id matches `^[a-z0-9-]+$`; folder exists under `problems/`.
- `meta.yaml` parses and contains all required fields: `id` (== folder name),
  `title`, `company`, `round`, `language`, `time_limit_min`,
  `part_budgets_min`, `tags`.
- Part dirs are contiguous `part-1..part-N`;
  `len(part_budgets_min) == N`.
- Every part has `statement.md`, `tests.py`, `solution.py`;
  `part-1` also has `starter.py` (later parts must not need one).
- Each part's `tests.py` has ≥1 `@pytest.mark.sample` test and ≥1
  non-sample test (the frontend renders sample tests inline).

Behavioral checks (mirrors how `backend/app/runner.py` stages a submission —
cumulative tests in a temp dir, `conftest.py` registering `sample`/`trap`
markers):

- For each part N: with `part-N/solution.py` as `solution.py`, tests for
  parts 1..N all pass.
- With `part-1/starter.py` as `solution.py`, part-1's full suite does NOT
  fully pass (the starter is supposed to be imperfect/incomplete).

Output: exit 0 on success; on failure, exit non-zero with a readable list of
every failed check (don't stop at the first).

### 3. Tests

`backend/tests/test_validate_problem.py`:

- Validator passes on the seed problem `problems/affirm-payment-allocator`
  (verified to conform: samples in every part, contiguous parts, budgets
  match).
- Validator fails with the right messages on synthetic broken fixtures
  (built per-test in tmp dirs): missing solution file, budget/part-count
  mismatch, no sample test, solution that fails its own tests, starter that
  passes everything.
- The existing `demo-problem` fixture is left as-is; it intentionally does
  not conform (part-2 has no sample test) and is not used by these tests.

## Out of scope (YAGNI)

- No backend endpoint, frontend button, or Claude API integration.
- No single-part drill mode — full multi-part problems only.
- No registration step; the filesystem is the registry.
