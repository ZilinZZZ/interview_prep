# Generate-Problem Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `/generate-problem <interview>` skill that authors new practice-problem folders, backed by `scripts/validate_problem.py` which deterministically verifies structure and behavior.

**Architecture:** The validator is a standalone script at repo root that reuses `backend/app/runner.py`'s `run_tests()` for behavioral checks (so validation stages tests exactly like the app does). The skill is a project skill (`.claude/skills/generate-problem/SKILL.md`) that encodes the authoring workflow and ends by running the validator. No backend/frontend changes.

**Tech Stack:** Python 3.12, pytest, PyYAML (already in `backend/requirements.txt`). Skill is markdown.

**Spec:** `docs/superpowers/specs/2026-07-16-generate-problem-skill-design.md`

## Global Constraints

- All file reads/writes pass `encoding="utf-8"` (existing codebase convention).
- Problem id regex is exactly `^[a-z0-9-]+$` (matches `backend/app/problems.py`).
- Required `meta.yaml` fields: `id`, `title`, `company`, `round`, `language`, `time_limit_min`, `part_budgets_min`, `tags`.
- Only `part-1` has `starter.py`; later parts must not.
- Backend tests run from the `backend/` directory: `python -m pytest tests/... -v` (pytest.ini sets `pythonpath = .`).
- Dev machine is Windows; never hardcode `/tmp` or POSIX-only paths. Use `pathlib`.
- Commit after each task with a conventional-commits message ending in the Claude co-author trailer.

---

### Task 1: Structural validator

**Files:**
- Create: `scripts/validate_problem.py`
- Test: `backend/tests/test_validate_problem.py`

**Interfaces:**
- Produces: `validate(base: Path, problem_id: str) -> list[str]` — structural failure messages, empty list means structurally valid. `_part_numbers(d: Path) -> list[int]` — sorted part numbers found under a problem dir (Task 2 reuses it). Module constant `ROOT` (repo root `Path`).
- Consumes: nothing from other tasks.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_validate_problem.py`:

```python
"""Tests for scripts/validate_problem.py (imported by path from repo root)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_problem  # noqa: E402

META = """\
id: {pid}
title: Demo
company: TestCo
round: practical-coding
language: python
time_limit_min: 30
part_budgets_min: [10, 10]
tags: [demo]
"""

TESTS_P1 = """\
import pytest
from solution import add


@pytest.mark.sample
def test_add_sample():
    assert add(1, 2) == 3


def test_add_hidden():
    assert add(2, 2) == 4
"""

TESTS_P2 = """\
import pytest
from solution import add


@pytest.mark.sample
def test_add_negative_sample():
    assert add(-1, -2) == -3


def test_add_zero_hidden():
    assert add(0, 5) == 5
"""

SOLUTION = "def add(a, b):\n    return a + b\n"
STARTER = "def add(a, b):\n    pass\n"


def make_problem(base: Path, pid: str = "gen-demo") -> Path:
    """Build a fully conformant two-part problem under base/pid."""
    d = base / pid
    for n, tests in ((1, TESTS_P1), (2, TESTS_P2)):
        pd = d / f"part-{n}"
        pd.mkdir(parents=True)
        (pd / "statement.md").write_text("# Statement", encoding="utf-8")
        (pd / "tests.py").write_text(tests, encoding="utf-8")
        (pd / "solution.py").write_text(SOLUTION, encoding="utf-8")
    (d / "part-1" / "starter.py").write_text(STARTER, encoding="utf-8")
    (d / "meta.yaml").write_text(META.format(pid=pid), encoding="utf-8")
    return d


def test_conformant_problem_has_no_structural_errors(tmp_path):
    make_problem(tmp_path)
    assert validate_problem.validate(tmp_path, "gen-demo") == []


def test_invalid_id_rejected(tmp_path):
    errors = validate_problem.validate(tmp_path, "../escape")
    assert len(errors) == 1 and "invalid problem id" in errors[0]


def test_missing_directory_reported(tmp_path):
    errors = validate_problem.validate(tmp_path, "nope")
    assert len(errors) == 1 and "no such problem" in errors[0]


def test_meta_missing_field_reported(tmp_path):
    d = make_problem(tmp_path)
    meta = (d / "meta.yaml").read_text(encoding="utf-8")
    (d / "meta.yaml").write_text(
        meta.replace("company: TestCo\n", ""), encoding="utf-8"
    )
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("missing field: company" in e for e in errors)


def test_meta_id_mismatch_reported(tmp_path):
    d = make_problem(tmp_path)
    meta = (d / "meta.yaml").read_text(encoding="utf-8")
    (d / "meta.yaml").write_text(
        meta.replace("id: gen-demo", "id: other-name"), encoding="utf-8"
    )
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("!= folder name" in e for e in errors)


def test_budget_count_mismatch_reported(tmp_path):
    d = make_problem(tmp_path)
    meta = (d / "meta.yaml").read_text(encoding="utf-8")
    (d / "meta.yaml").write_text(
        meta.replace("[10, 10]", "[10, 10, 10]"), encoding="utf-8"
    )
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("part_budgets_min" in e for e in errors)


def test_noncontiguous_parts_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-2").rename(d / "part-3")
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("not contiguous" in e for e in errors)


def test_missing_solution_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-2" / "solution.py").unlink()
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("part-2/solution.py missing" in e for e in errors)


def test_missing_part1_starter_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-1" / "starter.py").unlink()
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("part-1/starter.py missing" in e for e in errors)


def test_starter_in_later_part_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-2" / "starter.py").write_text(STARTER, encoding="utf-8")
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("part-2/starter.py should not exist" in e for e in errors)


def test_no_sample_test_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-2" / "tests.py").write_text(
        "from solution import add\n\n\ndef test_only_hidden():\n"
        "    assert add(1, 1) == 2\n",
        encoding="utf-8",
    )
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("no @pytest.mark.sample" in e for e in errors)


def test_no_hidden_test_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-2" / "tests.py").write_text(
        "import pytest\nfrom solution import add\n\n\n"
        "@pytest.mark.sample\ndef test_only_sample():\n"
        "    assert add(1, 1) == 2\n",
        encoding="utf-8",
    )
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("no hidden" in e for e in errors)


def test_unparseable_tests_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-1" / "tests.py").write_text("def broken(:\n", encoding="utf-8")
    errors = validate_problem.validate(tmp_path, "gen-demo")
    assert any("does not parse" in e for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_validate_problem.py -v`
Expected: collection error — `ModuleNotFoundError: No module named 'validate_problem'` (the script doesn't exist yet).

- [ ] **Step 3: Write the structural validator**

Create `scripts/validate_problem.py`:

```python
"""Validate a problem folder: structure, meta, test markers, and behavior.

Usage: python scripts/validate_problem.py <problem-id> [--problems-dir DIR]

Exit 0 if valid; exit 1 with a readable list of every failed check.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

ID_RE = re.compile(r"^[a-z0-9-]+$")
PART_RE = re.compile(r"^part-(\d+)$")
REQUIRED_META = [
    "id", "title", "company", "round", "language",
    "time_limit_min", "part_budgets_min", "tags",
]
PART_FILES = ("statement.md", "tests.py", "solution.py")


def _part_numbers(d: Path) -> list[int]:
    nums = []
    for p in d.glob("part-*"):
        m = PART_RE.fullmatch(p.name)
        if p.is_dir() and m:
            nums.append(int(m.group(1)))
    return sorted(nums)


def _is_sample(dec: ast.expr) -> bool:
    target = dec.func if isinstance(dec, ast.Call) else dec
    return isinstance(target, ast.Attribute) and target.attr == "sample"


def _test_counts(tests_source: str) -> tuple[int, int]:
    """(sample, hidden) counts of top-level test functions."""
    tree = ast.parse(tests_source)
    sample = hidden = 0
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            if any(_is_sample(dec) for dec in node.decorator_list):
                sample += 1
            else:
                hidden += 1
    return sample, hidden


def _check_meta(d: Path, problem_id: str, errors: list[str]) -> dict | None:
    meta_file = d / "meta.yaml"
    if not meta_file.is_file():
        errors.append("meta.yaml missing")
        return None
    try:
        meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        errors.append(f"meta.yaml does not parse: {e}")
        return None
    if not isinstance(meta, dict):
        errors.append("meta.yaml is not a mapping")
        return None
    for field in REQUIRED_META:
        if field not in meta:
            errors.append(f"meta.yaml missing field: {field}")
    if "id" in meta and meta["id"] != problem_id:
        errors.append(
            f"meta.yaml id {meta['id']!r} != folder name {problem_id!r}"
        )
    return meta


def _check_part(pd: Path, n: int, errors: list[str]) -> None:
    for fname in PART_FILES:
        if not (pd / fname).is_file():
            errors.append(f"part-{n}/{fname} missing")
    if n == 1 and not (pd / "starter.py").is_file():
        errors.append("part-1/starter.py missing")
    if n > 1 and (pd / "starter.py").is_file():
        errors.append(
            f"part-{n}/starter.py should not exist (only part-1 has starter)"
        )
    tests_file = pd / "tests.py"
    if tests_file.is_file():
        try:
            sample, hidden = _test_counts(
                tests_file.read_text(encoding="utf-8")
            )
        except SyntaxError as e:
            errors.append(f"part-{n}/tests.py does not parse: {e}")
            return
        if sample == 0:
            errors.append(f"part-{n}/tests.py has no @pytest.mark.sample test")
        if hidden == 0:
            errors.append(f"part-{n}/tests.py has no hidden (non-sample) test")


def validate(base: Path, problem_id: str) -> list[str]:
    """Structural checks only. Empty list means structurally valid."""
    if not ID_RE.fullmatch(problem_id):
        return [f"invalid problem id: {problem_id!r}"]
    d = base / problem_id
    if not d.is_dir():
        return [f"no such problem directory: {d}"]
    errors: list[str] = []
    meta = _check_meta(d, problem_id, errors)
    parts = _part_numbers(d)
    if not parts:
        errors.append("no part-N directories")
    elif parts != list(range(1, len(parts) + 1)):
        errors.append(f"part directories not contiguous from 1: {parts}")
    if meta and isinstance(meta.get("part_budgets_min"), list):
        if len(meta["part_budgets_min"]) != len(parts):
            errors.append(
                f"part_budgets_min has {len(meta['part_budgets_min'])} "
                f"entries but there are {len(parts)} part dirs"
            )
    for n in parts:
        _check_part(d / f"part-{n}", n, errors)
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_validate_problem.py -v`
Expected: all 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_problem.py backend/tests/test_validate_problem.py
git commit -m "feat: structural problem validator (meta, parts, markers)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Behavioral validator

**Files:**
- Modify: `scripts/validate_problem.py` (append; also add one import block near the top)
- Test: `backend/tests/test_validate_problem.py` (append)

**Interfaces:**
- Consumes: `validate`, `_part_numbers`, `ROOT` from Task 1; `run_tests(problem_dir: Path, code: str, part: int, mode: str, timeout_s: int) -> dict` from `backend/app/runner.py` (returns keys `tests` — list of dicts with `name`/`outcome` — plus `stdout`, `stderr`, `timed_out`, `exit_code`; exit_code 0 means every collected test passed).
- Produces: `validate_behavior(base: Path, problem_id: str, timeout_s: int = 30) -> list[str]`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_validate_problem.py`:

```python
def test_conformant_problem_passes_behavior(tmp_path):
    make_problem(tmp_path)
    assert validate_problem.validate_behavior(tmp_path, "gen-demo") == []


def test_broken_solution_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-2" / "solution.py").write_text(
        "def add(a, b):\n    return a - b\n", encoding="utf-8"
    )
    errors = validate_problem.validate_behavior(tmp_path, "gen-demo")
    assert any("part-2 solution fails" in e for e in errors)


def test_part1_solution_only_runs_part1_tests(tmp_path):
    # A part-1 solution that would fail part-2 tests must still validate:
    # behavior for part N runs tests 1..N only.
    d = make_problem(tmp_path)
    (d / "part-2" / "tests.py").write_text(
        TESTS_P2.replace(
            "from solution import add",
            "from solution import add, sub",
        )
        + "\n\ndef test_sub_hidden():\n    assert sub(3, 1) == 2\n",
        encoding="utf-8",
    )
    (d / "part-2" / "solution.py").write_text(
        SOLUTION + "\n\ndef sub(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    assert validate_problem.validate_behavior(tmp_path, "gen-demo") == []


def test_starter_that_passes_everything_reported(tmp_path):
    d = make_problem(tmp_path)
    (d / "part-1" / "starter.py").write_text(SOLUTION, encoding="utf-8")
    errors = validate_problem.validate_behavior(tmp_path, "gen-demo")
    assert any("starter passes" in e for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_validate_problem.py -v -k "behavior or broken_solution or starter_that_passes or part1_solution"`
Expected: 4 FAIL with `AttributeError: module 'validate_problem' has no attribute 'validate_behavior'`.

- [ ] **Step 3: Implement validate_behavior**

In `scripts/validate_problem.py`, add after the `ROOT = ...` line (before the other constants):

```python
sys.path.insert(0, str(ROOT / "backend"))

from app.runner import run_tests  # noqa: E402
```

Append at the end of the file:

```python
def validate_behavior(
    base: Path, problem_id: str, timeout_s: int = 30
) -> list[str]:
    """Run each part's solution (and the part-1 starter) like the app does.

    Requires a structurally valid problem; call validate() first.
    """
    errors: list[str] = []
    d = base / problem_id
    for n in _part_numbers(d):
        code = (d / f"part-{n}" / "solution.py").read_text(encoding="utf-8")
        result = run_tests(d, code, part=n, mode="submit", timeout_s=timeout_s)
        failed = [t["name"] for t in result["tests"] if t["outcome"] != "passed"]
        if result["timed_out"]:
            errors.append(f"part-{n} solution: tests timed out")
        elif failed or result["exit_code"] != 0:
            detail = ", ".join(failed) or result["stderr"].strip()[:200]
            errors.append(f"part-{n} solution fails parts 1..{n} tests: {detail}")
    starter = d / "part-1" / "starter.py"
    if starter.is_file():
        result = run_tests(
            d,
            starter.read_text(encoding="utf-8"),
            part=1,
            mode="submit",
            timeout_s=timeout_s,
        )
        if result["exit_code"] == 0 and not result["timed_out"]:
            errors.append(
                "part-1 starter passes the full part-1 suite; "
                "the starter must be imperfect"
            )
    return errors
```

- [ ] **Step 4: Run the full test file to verify everything passes**

Run: `cd backend && python -m pytest tests/test_validate_problem.py -v`
Expected: all 17 tests PASS (behavioral ones take a few seconds each — they shell out to pytest).

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_problem.py backend/tests/test_validate_problem.py
git commit -m "feat: behavioral validation — solutions pass, starter must not

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: CLI entry point + seed-problem validation

**Files:**
- Modify: `scripts/validate_problem.py` (append `main`)
- Test: `backend/tests/test_validate_problem.py` (append)

**Interfaces:**
- Consumes: `validate`, `validate_behavior`, `ROOT` from Tasks 1–2.
- Produces: `main(argv: list[str] | None = None) -> int` and `python scripts/validate_problem.py <problem-id> [--problems-dir DIR]` as the command the skill (Task 4) runs.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_validate_problem.py`:

```python
def test_main_ok_exit_zero(tmp_path, capsys):
    make_problem(tmp_path)
    rc = validate_problem.main(["gen-demo", "--problems-dir", str(tmp_path)])
    assert rc == 0
    assert "OK: gen-demo" in capsys.readouterr().out


def test_main_invalid_exit_one_lists_all_errors(tmp_path, capsys):
    d = make_problem(tmp_path)
    (d / "part-2" / "solution.py").unlink()
    (d / "part-1" / "starter.py").unlink()
    rc = validate_problem.main(["gen-demo", "--problems-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "INVALID: gen-demo" in out
    assert "part-2/solution.py missing" in out
    assert "part-1/starter.py missing" in out


def test_main_skips_behavior_when_structure_broken(tmp_path, capsys):
    # Structural failures must not attempt to run tests (files are missing).
    d = make_problem(tmp_path)
    (d / "part-1" / "tests.py").unlink()
    rc = validate_problem.main(["gen-demo", "--problems-dir", str(tmp_path)])
    assert rc == 1
    assert "solution fails" not in capsys.readouterr().out


def test_seed_problem_is_valid():
    base = ROOT / "problems"
    assert validate_problem.validate(base, "affirm-payment-allocator") == []
    assert (
        validate_problem.validate_behavior(base, "affirm-payment-allocator")
        == []
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_validate_problem.py -v -k main`
Expected: 3 FAIL with `AttributeError: module 'validate_problem' has no attribute 'main'`. (`test_seed_problem_is_valid` should already pass — if it fails, the seed problem or validator has a real bug; investigate before proceeding.)

- [ ] **Step 3: Implement main**

Append to `scripts/validate_problem.py` (also add `import argparse` to the imports at the top):

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a problem folder (structure + behavior)."
    )
    parser.add_argument("problem_id")
    parser.add_argument(
        "--problems-dir", type=Path, default=ROOT / "problems"
    )
    args = parser.parse_args(argv)
    errors = validate(args.problems_dir, args.problem_id)
    if not errors:
        errors = validate_behavior(args.problems_dir, args.problem_id)
    if errors:
        print(f"INVALID: {args.problem_id}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {args.problem_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the full test file, then the CLI against the seed problem**

Run: `cd backend && python -m pytest tests/test_validate_problem.py -v`
Expected: all 21 tests PASS.

Run: `python scripts/validate_problem.py affirm-payment-allocator` (from repo root)
Expected output: `OK: affirm-payment-allocator`, exit code 0.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_problem.py backend/tests/test_validate_problem.py
git commit -m "feat: validator CLI entry point; assert seed problem validates

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: The generate-problem skill + README note

**Files:**
- Create: `.claude/skills/generate-problem/SKILL.md`
- Modify: `README.md` (the "Adding a problem" section)

**Interfaces:**
- Consumes: the Task 3 CLI command `python scripts/validate_problem.py <problem-id>`.
- Produces: the `/generate-problem` skill, invocable in any Claude Code session in this repo.

- [ ] **Step 1: Write the skill**

Create `.claude/skills/generate-problem/SKILL.md`:

````markdown
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
python scripts/validate_problem.py <new-id>
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
````

- [ ] **Step 2: Update README**

In `README.md`, replace:

```markdown
## Adding a problem

Make a folder under `problems/` — see
`docs/superpowers/specs/2026-07-15-interview-platform-design.md` for the format.
No registration step; it appears in the list on refresh.
```

with:

```markdown
## Adding a problem

Make a folder under `problems/` — see
`docs/superpowers/specs/2026-07-15-interview-platform-design.md` for the format.
No registration step; it appears in the list on refresh.

To have Claude Code write one for you: `/generate-problem <interview>`
(e.g. `/generate-problem affirm-practical-coding`). Check any problem folder,
hand-written or generated, with `python scripts/validate_problem.py <id>`.
```

- [ ] **Step 3: Verify the skill file loads**

Run: `python -c "import yaml, pathlib; fm = pathlib.Path('.claude/skills/generate-problem/SKILL.md').read_text(encoding='utf-8').split('---')[1]; print(yaml.safe_load(fm))"`
Expected: a dict with `name: generate-problem` and the description — proves the frontmatter parses.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/generate-problem/SKILL.md README.md
git commit -m "feat: /generate-problem skill for authoring validated problems

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
