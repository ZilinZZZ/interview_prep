---
name: generate-problem
description: Generate a new practice problem folder for a given interview spec. Use when the user asks to generate/create a new practice problem for an interview (e.g. /generate-problem affirm-practical-coding).
---

# Generate Problem

Author a new problem folder under `problems/` for the interview named in the
argument, then prove it valid. The user is the candidate: never show them
traps, edge cases, hidden tests, or solutions — only the problem id, title,
domain, and part count when done.

## Step 1 — Read the interview spec

The argument names a spec file: `interviews/<argument>.md`. Read it fully.
If the argument is missing or no such file exists, list the files in
`interviews/` (excluding `_TEMPLATE.md`) and stop.

The spec is the source of truth for: domain flavor, structure (part count
and per-part minute budgets), difficulty ceiling, named traps, and
anti-patterns. Do not import flavor from other specs or invent constraints.

## Step 2 — Pick a fresh domain

Read every `problems/*/meta.yaml` (`tags` and `title`) and any scorecards in
`sessions/`. Pick a domain from the spec's domain-flavor list that has not
been used recently; never repeat the most recent problem's domain.

## Step 3 — Author the folder

Layout (exact — the validator enforces it):

```
problems/<new-id>/            # id: lowercase letters, digits, hyphens only
  meta.yaml                   # id, title, company, round, language,
                              # time_limit_min, part_budgets_min, tags
  part-1/
    statement.md
    starter.py                # part-1 ONLY
    tests.py
    solution.py
  part-2/                     # statement.md, tests.py, solution.py
  ...                         # part count & budgets from the spec's structure
```

Content rules:

- **Statement**: business framing plausible for the company, concrete
  example input/output. Withhold the edge-case list.
- **Starter code** (part-1 only): deliberately imperfect — mediocre naming,
  a missing edge case, or a wrong-type-for-the-job (e.g. floats where cents
  belong, if the spec's traps include that). Never annotate the flaws. It
  must NOT pass part-1's full test suite.
- **Each part breaks the naive shape of the previous part.** Part 1 is
  trivially achievable and establishes the model.
- **Tests** import `from solution import ...`. Three visibility levels:
  `@pytest.mark.sample` (shown in statement, runs on Run), unmarked
  (hidden, runs on Submit), `@pytest.mark.trap("label")` (hidden; label
  shown when it fails). Every part needs ≥1 sample and ≥1 hidden test.
- **Every trap named in the spec's Traps section** gets at least one
  trap-marked test in some part, labeled after the trap.
- **Solutions are cumulative**: `part-N/solution.py` must pass the tests of
  parts 1..N.
- **Difficulty ceiling** per the spec — if it says "commonly-used data
  structures", it's dicts, lists, sorting, grouping; no DP/graphs.

## Step 4 — Validate

Run from the repo root:

```
backend\.venv\Scripts\python scripts\validate_problem.py <new-id>
```

It checks structure (meta fields, contiguous parts, budgets matching part
count, sample/hidden tests per part) and behavior (each part's solution
passes parts 1..N cumulatively; the starter does NOT pass part-1). Fix
failures and re-run until it prints `OK: <new-id>`. Do not report the
problem as ready before that.

## Step 5 — Report

Tell the user: problem id, title, domain, number of parts, and time budget.
Nothing else — no traps, no edge cases, no solution commentary. The problem
appears in the app on refresh; no registration step.
