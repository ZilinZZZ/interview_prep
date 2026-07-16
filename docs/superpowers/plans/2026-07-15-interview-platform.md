# Local Interview Practice Platform Implementation Plan
Use at least Sonnet for sub-agents.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A localhost web app for practicing multi-part coding-interview problems: statement left, Monaco editor right, pytest results below, with part gating, regression detection, and session logging.

**Architecture:** Stateless FastAPI backend (serve problems, run pytest in temp dirs, append logs); React frontend owns all session state in localStorage. Spec: `docs/superpowers/specs/2026-07-15-interview-platform-design.md`.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, PyYAML, pytest · React 19, Vite, TypeScript, Tailwind v4, @monaco-editor/react, react-markdown, react-resizable-panels, vitest.

## Global Constraints

- Backend binds `127.0.0.1` explicitly. Never `0.0.0.0`.
- No endpoint accepts a filesystem path from the client. Problem ids validated with `^[a-z0-9-]+$` AND resolved-path-under-problems-dir check.
- One test run at a time; a new run kills the in-flight subprocess (Windows: `taskkill /F /T`).
- pytest subprocess timeout 10s, hard kill.
- Filename timestamps use `%Y-%m-%dT%H-%M-%S` — no colons (Windows-illegal).
- Language comes from `meta.yaml` (`language: python`). Don't hardcode `.py` in frontend logic.
- Timer is pressure, never enforcement — nothing is ever blocked on time.
- Return structured test results; never a raw traceback string as the only signal.
- Out of scope (do NOT build): auth, Docker, multi-language, gamification, cloud deploy, CI, admin UI.
- Platform is Windows 11; the dev machine runs commands via Git Bash or PowerShell. Venv python is `backend/.venv/Scripts/python`.
- Commit after every task. Commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

## File Structure

```
backend/
  requirements.txt
  pytest.ini
  app/
    __init__.py
    main.py          # FastAPI app + routes (thin; delegates to modules)
    problems.py      # filesystem problem loading, id validation, sample extraction
    runner.py        # temp-dir assembly, pytest subprocess, result parsing
    sessions.py      # submit logs + keystroke snapshots
  tests/
    test_problems.py
    test_api.py
    test_runner.py
    test_sessions.py
    fixtures/problems/demo-problem/   # committed fixture, 2 parts
frontend/
  (Vite react-ts scaffold)
  src/
    types.ts         # API payload types (mirror backend exactly)
    api.ts           # fetch wrappers
    storage.ts       # localStorage persistence (SessionState, buffers, notes)
    session.ts       # pure logic: regressions, clock format, budgets, buffer resolution
    session.test.ts  # vitest unit tests for session.ts
    App.tsx          # problem list + hash routing
    ProblemView.tsx  # per-problem state owner, composes panes
    components/
      ProblemPane.tsx  EditorPane.tsx  ResultsPane.tsx  UnlockPanel.tsx  TimerBar.tsx
problems/affirm-payment-allocator/    # seed problem, 3 parts
package.json         # root: npm run dev / setup (concurrently)
Makefile             # make dev → npm run dev
.gitignore
README.md
```

---

### Task 1: Backend problem loading (`problems.py`)

**Files:**
- Create: `backend/requirements.txt`, `backend/pytest.ini`, `backend/app/__init__.py`, `backend/app/problems.py`
- Create: `backend/tests/test_problems.py`
- Create: `backend/tests/fixtures/problems/demo-problem/` (meta.yaml, part-1/, part-2/)

**Interfaces:**
- Produces: `problems.problem_dir(base: Path, problem_id: str) -> Path` (raises `ProblemNotFound`), `problems.list_problems(base) -> list[dict]`, `problems.load_meta(base, id) -> dict` (meta.yaml fields + `num_parts: int`), `problems.load_part(base, id, n) -> dict` with keys `statement: str`, `starter: str | None`, `sample_tests: str` (raises `PartNotFound`), `problems.load_solution(base, id, n) -> str`.

- [ ] **Step 1: Create backend scaffold + venv**

`backend/requirements.txt`:

```
fastapi>=0.115
uvicorn>=0.34
pyyaml>=6.0
pytest>=8.0
httpx>=0.27
```

`backend/pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

`backend/app/__init__.py`: empty file.

Run:

```bash
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt
```

Expected: pip installs fastapi, uvicorn, pyyaml, pytest, httpx without error.

- [ ] **Step 2: Create the committed fixture problem**

`backend/tests/fixtures/problems/demo-problem/meta.yaml`:

```yaml
id: demo-problem
title: Demo Problem
company: TestCo
round: practical-coding
language: python
time_limit_min: 30
part_budgets_min: [10, 10]
tags: [demo]
```

`backend/tests/fixtures/problems/demo-problem/part-1/statement.md`:

```markdown
## Part 1

Implement `add(a, b)` returning the sum.
```

`backend/tests/fixtures/problems/demo-problem/part-1/starter.py`:

```python
def add(a, b):
    pass
```

`backend/tests/fixtures/problems/demo-problem/part-1/tests.py`:

```python
import pytest
from solution import add


@pytest.mark.sample
def test_add_small():
    assert add(1, 2) == 3


def test_add_negative():
    assert add(-1, 1) == 0


@pytest.mark.trap("silent-none")
def test_add_returns_value_not_none():
    assert add(0, 0) == 0
```

`backend/tests/fixtures/problems/demo-problem/part-1/solution.py`:

```python
def add(a, b):
    return a + b
```

`backend/tests/fixtures/problems/demo-problem/part-2/statement.md`:

```markdown
## Part 2

Add `scale(a, factor)` returning `a * factor`. `add` must keep working.
```

`backend/tests/fixtures/problems/demo-problem/part-2/tests.py`:

```python
from solution import scale


def test_scale():
    assert scale(2, 3) == 6
```

`backend/tests/fixtures/problems/demo-problem/part-2/solution.py`:

```python
def add(a, b):
    return a + b


def scale(a, factor):
    return a * factor
```

- [ ] **Step 3: Write failing tests for problems.py**

`backend/tests/test_problems.py`:

```python
from pathlib import Path

import pytest

from app import problems

FIXTURES = Path(__file__).parent / "fixtures" / "problems"


def test_list_problems_returns_meta_with_num_parts():
    result = problems.list_problems(FIXTURES)
    assert len(result) == 1
    meta = result[0]
    assert meta["id"] == "demo-problem"
    assert meta["title"] == "Demo Problem"
    assert meta["num_parts"] == 2
    assert meta["part_budgets_min"] == [10, 10]


def test_list_problems_empty_for_missing_dir(tmp_path):
    assert problems.list_problems(tmp_path / "nope") == []


def test_problem_dir_rejects_path_traversal():
    for bad in ["../evil", "demo-problem/../../etc", "a/b", "UPPER", "demo problem", ""]:
        with pytest.raises(problems.ProblemNotFound):
            problems.problem_dir(FIXTURES, bad)


def test_problem_dir_rejects_unknown_id():
    with pytest.raises(problems.ProblemNotFound):
        problems.problem_dir(FIXTURES, "no-such-problem")


def test_load_part_1_has_starter_statement_and_samples():
    part = problems.load_part(FIXTURES, "demo-problem", 1)
    assert part["statement"].startswith("## Part 1")
    assert "def add(a, b):" in part["starter"]
    assert "test_add_small" in part["sample_tests"]
    assert "test_add_negative" not in part["sample_tests"]  # not sample-marked
    assert "test_add_returns_value_not_none" not in part["sample_tests"]  # trap


def test_load_part_2_has_no_starter():
    part = problems.load_part(FIXTURES, "demo-problem", 2)
    assert part["starter"] is None


def test_load_part_out_of_range():
    with pytest.raises(problems.PartNotFound):
        problems.load_part(FIXTURES, "demo-problem", 3)
    with pytest.raises(problems.PartNotFound):
        problems.load_part(FIXTURES, "demo-problem", 0)


def test_load_solution():
    sol = problems.load_solution(FIXTURES, "demo-problem", 2)
    assert "def scale" in sol
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_problems.py -v`
Expected: FAIL — `ModuleNotFoundError` / `AttributeError` (problems module missing).

- [ ] **Step 5: Implement `backend/app/problems.py`**

```python
"""Load problems from the problems/ directory. Pure filesystem reads."""
from __future__ import annotations

import ast
import re
from pathlib import Path

import yaml

ID_RE = re.compile(r"^[a-z0-9-]+$")


class ProblemNotFound(Exception):
    pass


class PartNotFound(Exception):
    pass


def problem_dir(base: Path, problem_id: str) -> Path:
    """Resolve a problem id to its directory. Rejects anything path-like."""
    if not ID_RE.fullmatch(problem_id):
        raise ProblemNotFound(problem_id)
    base = base.resolve()
    d = (base / problem_id).resolve()
    if d.parent != base or not (d / "meta.yaml").is_file():
        raise ProblemNotFound(problem_id)
    return d


def _num_parts(d: Path) -> int:
    return len([p for p in d.glob("part-*") if p.is_dir()])


def load_meta(base: Path, problem_id: str) -> dict:
    d = problem_dir(base, problem_id)
    meta = yaml.safe_load((d / "meta.yaml").read_text(encoding="utf-8"))
    meta["num_parts"] = _num_parts(d)
    return meta


def list_problems(base: Path) -> list[dict]:
    if not base.is_dir():
        return []
    out = []
    for d in sorted(base.iterdir()):
        if d.is_dir() and (d / "meta.yaml").is_file():
            out.append(load_meta(base, d.name))
    return out


def _part_dir(base: Path, problem_id: str, n: int) -> Path:
    d = problem_dir(base, problem_id)
    pd = d / f"part-{n}"
    if n < 1 or not pd.is_dir():
        raise PartNotFound(f"{problem_id}/part-{n}")
    return pd


def _is_sample(dec: ast.expr) -> bool:
    target = dec.func if isinstance(dec, ast.Call) else dec
    return isinstance(target, ast.Attribute) and target.attr == "sample"


def sample_test_source(tests_source: str) -> str:
    """Extract source of @pytest.mark.sample tests for inline display."""
    tree = ast.parse(tests_source)
    chunks = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and any(
            _is_sample(dec) for dec in node.decorator_list
        ):
            seg = ast.get_source_segment(tests_source, node)
            if seg:
                chunks.append(seg)
    return "\n\n".join(chunks)


def load_part(base: Path, problem_id: str, n: int) -> dict:
    pd = _part_dir(base, problem_id, n)
    starter = pd / "starter.py"
    tests_source = (pd / "tests.py").read_text(encoding="utf-8")
    return {
        "statement": (pd / "statement.md").read_text(encoding="utf-8"),
        "starter": starter.read_text(encoding="utf-8") if starter.is_file() else None,
        "sample_tests": sample_test_source(tests_source),
    }


def load_solution(base: Path, problem_id: str, n: int) -> str:
    return (_part_dir(base, problem_id, n) / "solution.py").read_text(encoding="utf-8")
```

Note: `ast.get_source_segment` on a `FunctionDef` excludes decorators — samples display without marker noise. That's intended.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_problems.py -v`
Expected: 8 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat(backend): problem loading from filesystem"
```

---

### Task 2: Problem API endpoints

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `problems.*` from Task 1.
- Produces: FastAPI `app` in `app.main` with `GET /api/problems`, `GET /api/problems/{id}/parts/{n}`, `GET /api/problems/{id}/parts/{n}/solution`. Dirs resolved per-request via env vars `PROBLEMS_DIR` / `SESSIONS_DIR` (defaults: `<repo-root>/problems`, `<repo-root>/sessions`) so tests can monkeypatch.

- [ ] **Step 1: Write failing API tests**

`backend/tests/test_api.py`:

```python
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures" / "problems"


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("PROBLEMS_DIR", str(FIXTURES))
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path / "sessions"))
    return TestClient(app)


def test_list_problems(client):
    resp = client.get("/api/problems")
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["id"] == "demo-problem"
    assert body[0]["num_parts"] == 2


def test_get_part(client):
    resp = client.get("/api/problems/demo-problem/parts/1")
    assert resp.status_code == 200
    body = resp.json()
    assert "## Part 1" in body["statement"]
    assert body["starter"] is not None
    assert "test_add_small" in body["sample_tests"]


def test_get_part_404s(client):
    assert client.get("/api/problems/demo-problem/parts/99").status_code == 404
    assert client.get("/api/problems/nope/parts/1").status_code == 404
    # path-traversal shaped ids must 404, never resolve
    assert client.get("/api/problems/..%2Fevil/parts/1").status_code == 404


def test_get_solution(client):
    resp = client.get("/api/problems/demo-problem/parts/2/solution")
    assert resp.status_code == 200
    assert "def scale" in resp.json()["solution"]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Implement `backend/app/main.py`**

```python
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from . import problems

ROOT = Path(__file__).resolve().parents[2]  # repo root

app = FastAPI(title="Interview Practice Platform")


def problems_dir() -> Path:
    return Path(os.environ.get("PROBLEMS_DIR", str(ROOT / "problems")))


def sessions_dir() -> Path:
    return Path(os.environ.get("SESSIONS_DIR", str(ROOT / "sessions")))


@app.get("/api/problems")
def get_problems():
    return problems.list_problems(problems_dir())


@app.get("/api/problems/{problem_id}/parts/{n}")
def get_part(problem_id: str, n: int):
    try:
        return problems.load_part(problems_dir(), problem_id, n)
    except (problems.ProblemNotFound, problems.PartNotFound):
        raise HTTPException(404)


@app.get("/api/problems/{problem_id}/parts/{n}/solution")
def get_solution(problem_id: str, n: int):
    try:
        return {"solution": problems.load_solution(problems_dir(), problem_id, n)}
    except (problems.ProblemNotFound, problems.PartNotFound):
        raise HTTPException(404)
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: 4 passed.

- [ ] **Step 5: Smoke the real server**

Run (background, then curl, then kill):

```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
sleep 3
curl -s http://127.0.0.1:8000/api/problems
kill %1
```

Expected: `[]` (real `problems/` dir doesn't exist yet — empty list, not an error).

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat(backend): problem API endpoints"
```

---

### Task 3: Test runner (`runner.py`)

**Files:**
- Create: `backend/app/runner.py`
- Create: `backend/tests/test_runner.py`

**Interfaces:**
- Consumes: a problem directory `Path` (from `problems.problem_dir`).
- Produces: `runner.run_tests(problem_dir: Path, code: str, part: int, mode: str, timeout_s: int = 10) -> dict` returning `{"tests": [{"name": str, "part": int, "outcome": "passed"|"failed"|"error", "duration": float, "trap": str|None, "message": str|None}], "stdout": str, "stderr": str, "timed_out": bool, "exit_code": int}`. Also `runner.cancel_current_run() -> None`.

**How it works:** fresh temp dir per run → write editor buffer as `solution.py` → write an injected `conftest.py` (records outcome/trap/file per test to `results.json` via pytest hooks) → copy `part-K/tests.py` as `test_part_K.py` for K = 1..part → run `[sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"]`, plus `["-m", "sample"]` when mode is `"run"` → `communicate(timeout)` → on `TimeoutExpired`, kill the process tree (`taskkill /F /T` on Windows) → parse `results.json`, derive `part` from the test filename.

- [ ] **Step 1: Write failing runner tests**

`backend/tests/test_runner.py`:

```python
from pathlib import Path

from app import runner

DEMO = Path(__file__).parent / "fixtures" / "problems" / "demo-problem"

GOOD = "def add(a, b):\n    return a + b\n"
GOOD_2 = GOOD + "\n\ndef scale(a, factor):\n    return a * factor\n"
BAD = "def add(a, b):\n    return None\n"
SYNTAX_ERROR = "def add(a, b:\n"
INFINITE = "def add(a, b):\n    while True:\n        pass\n"


def by_name(result):
    return {t["name"]: t for t in result["tests"]}


def test_submit_all_pass():
    result = runner.run_tests(DEMO, GOOD, part=1, mode="submit")
    assert result["timed_out"] is False
    assert result["exit_code"] == 0
    tests = by_name(result)
    assert len(tests) == 3
    assert all(t["outcome"] == "passed" for t in tests.values())
    assert all(t["part"] == 1 for t in tests.values())


def test_run_mode_only_samples():
    result = runner.run_tests(DEMO, GOOD, part=1, mode="run")
    tests = by_name(result)
    assert set(tests) == {"test_add_small"}


def test_failure_carries_trap_label_and_message():
    result = runner.run_tests(DEMO, BAD, part=1, mode="submit")
    tests = by_name(result)
    trap = tests["test_add_returns_value_not_none"]
    assert trap["outcome"] == "failed"
    assert trap["trap"] == "silent-none"
    assert trap["message"]  # assertion detail present
    assert tests["test_add_small"]["trap"] is None


def test_multi_part_runs_earlier_parts_and_tags_them():
    result = runner.run_tests(DEMO, GOOD_2, part=2, mode="submit")
    tests = by_name(result)
    assert tests["test_scale"]["part"] == 2
    assert tests["test_add_small"]["part"] == 1
    assert all(t["outcome"] == "passed" for t in tests.values())


def test_part_2_code_missing_scale_reports_error_not_crash():
    # part-2 tests can't import `scale` -> collection error surfaces as a result
    result = runner.run_tests(DEMO, GOOD, part=2, mode="submit")
    assert result["exit_code"] != 0
    assert any(t["outcome"] == "error" for t in result["tests"])


def test_syntax_error_is_structured():
    result = runner.run_tests(DEMO, SYNTAX_ERROR, part=1, mode="submit")
    assert result["exit_code"] != 0
    assert any(t["outcome"] == "error" for t in result["tests"]) or result["stdout"]


def test_timeout_hard_kills():
    result = runner.run_tests(DEMO, INFINITE, part=1, mode="submit", timeout_s=3)
    assert result["timed_out"] is True


def test_stdout_captured():
    code = GOOD + "\nprint('debug-marker-xyz')\n"
    result = runner.run_tests(DEMO, code, part=1, mode="submit")
    assert "debug-marker-xyz" in result["stdout"]
```

Note on `INFINITE`: the loop runs at import time of... no — it runs when `add` is *called* by the sample test, inside pytest. Either way the subprocess exceeds the timeout and must be killed.

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_runner.py -v`
Expected: FAIL — no `app.runner` module.

- [ ] **Step 3: Implement `backend/app/runner.py`**

The injected conftest is a module-level string constant `CONFTEST` (a plain string, NOT an f-string — it contains braces). Full file:

```python
"""Assemble a temp workspace and run pytest against the user's code."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

# Injected into every temp workspace. Records per-test outcome, trap label,
# and source file (for part attribution) to results.json.
CONFTEST = (
    "import json\n"
    "import pathlib\n"
    "\n"
    "import pytest\n"
    "\n"
    "_results = []\n"
    "\n"
    "\n"
    "def pytest_configure(config):\n"
    "    config.addinivalue_line('markers', 'sample: shown in statement; runs on Run')\n"
    "    config.addinivalue_line('markers', 'trap(label): hidden test for a known trap')\n"
    "\n"
    "\n"
    "@pytest.hookimpl(hookwrapper=True)\n"
    "def pytest_runtest_makereport(item, call):\n"
    "    outcome = yield\n"
    "    report = outcome.get_result()\n"
    "    failed_setup = report.when == 'setup' and report.outcome != 'passed'\n"
    "    if report.when != 'call' and not failed_setup:\n"
    "        return\n"
    "    trap = item.get_closest_marker('trap')\n"
    "    _results.append({\n"
    "        'name': item.name,\n"
    "        'file': item.location[0],\n"
    "        'outcome': 'error' if failed_setup else report.outcome,\n"
    "        'duration': round(report.duration, 4),\n"
    "        'trap': trap.args[0] if trap and trap.args else None,\n"
    "        'message': str(report.longrepr) if report.outcome == 'failed' else None,\n"
    "    })\n"
    "\n"
    "\n"
    "def pytest_collectreport(report):\n"
    "    if report.failed:\n"
    "        _results.append({\n"
    "            'name': report.nodeid or 'collection',\n"
    "            'file': report.nodeid,\n"
    "            'outcome': 'error',\n"
    "            'duration': 0.0,\n"
    "            'trap': None,\n"
    "            'message': str(report.longrepr),\n"
    "        })\n"
    "\n"
    "\n"
    "def pytest_sessionfinish(session, exitstatus):\n"
    "    pathlib.Path('results.json').write_text(json.dumps(_results), encoding='utf-8')\n"
)

_lock = threading.Lock()
_current_proc: subprocess.Popen | None = None


def _kill_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
        )
    else:
        proc.kill()


def cancel_current_run() -> None:
    """Kill any in-flight run. New runs call this first (one run at a time)."""
    global _current_proc
    with _lock:
        if _current_proc is not None:
            _kill_tree(_current_proc)
            _current_proc = None


def _part_number(filename: str) -> int:
    # "test_part_3.py" -> 3; anything else -> 0
    stem = Path(filename).stem
    try:
        return int(stem.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 0


def run_tests(
    problem_dir: Path, code: str, part: int, mode: str, timeout_s: int = 10
) -> dict:
    """Write `code` as solution.py, copy tests for parts 1..part, run pytest."""
    global _current_proc
    cancel_current_run()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        workdir = Path(td)
        (workdir / "solution.py").write_text(code, encoding="utf-8")
        (workdir / "conftest.py").write_text(CONFTEST, encoding="utf-8")
        for k in range(1, part + 1):
            src = problem_dir / f"part-{k}" / "tests.py"
            (workdir / f"test_part_{k}.py").write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )
        args = [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"]
        if mode == "run":
            args += ["-m", "sample"]
        with _lock:
            proc = subprocess.Popen(
                args,
                cwd=td,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            _current_proc = proc
        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            stdout, stderr = proc.communicate()
            timed_out = True
        with _lock:
            if _current_proc is proc:
                _current_proc = None
        results_file = workdir / "results.json"
        tests = []
        if results_file.exists():
            for entry in json.loads(results_file.read_text(encoding="utf-8")):
                entry["part"] = _part_number(entry.pop("file"))
                tests.append(entry)
        return {
            "tests": tests,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": timed_out,
            "exit_code": proc.returncode,
        }
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_runner.py -v`
Expected: 8 passed (the timeout test takes ~3s — that's the point).

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(backend): pytest runner with temp-dir isolation, traps, timeout"
```

---

### Task 4: Run/submit/snapshot endpoints + session logs

**Files:**
- Create: `backend/app/sessions.py`
- Modify: `backend/app/main.py` (imports, request models, two POST routes)
- Create: `backend/tests/test_sessions.py`
- Modify: `backend/tests/test_api.py` (append run/snapshot endpoint tests)

**Interfaces:**
- Consumes: `runner.run_tests`, `problems.problem_dir`, `problems.load_meta`.
- Produces: `POST /api/problems/{id}/run` body `{"part": int, "code": str, "mode": "run"|"submit", "client_stats": {...}}` → runner result dict (same shape as Task 3). `POST /api/problems/{id}/snapshot` body `{"code": str}` → `{"ok": true}`. `sessions.append_submit_log(sessions_dir: Path, problem_id: str, entry: dict) -> Path`, `sessions.write_snapshot(sessions_dir: Path, problem_id: str, code: str) -> Path`.
- Session log entry keys (spec): `problem_id, part, elapsed_total_s, elapsed_part_s, run_count, submit_count, traps_failed, regressions, skipped_parts, timed_out, final_code`.

- [ ] **Step 1: Write failing tests for sessions.py**

`backend/tests/test_sessions.py`:

```python
import json

from app import sessions


def test_append_submit_log_creates_file(tmp_path):
    entry = {"problem_id": "demo-problem", "part": 1, "final_code": "x = 1"}
    path = sessions.append_submit_log(tmp_path, "demo-problem", entry)
    assert path.parent == tmp_path / "demo-problem"
    assert json.loads(path.read_text(encoding="utf-8")) == entry
    assert ":" not in path.name  # Windows-safe timestamp


def test_write_snapshot(tmp_path):
    path = sessions.write_snapshot(tmp_path, "demo-problem", "print('hi')")
    assert path.parent == tmp_path / "demo-problem" / "keystrokes"
    assert path.suffix == ".py"
    assert path.read_text(encoding="utf-8") == "print('hi')"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_sessions.py -v`
Expected: FAIL — no `app.sessions`.

- [ ] **Step 3: Implement `backend/app/sessions.py`**

```python
"""Append-only session logs and editor snapshots."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

TS_FMT = "%Y-%m-%dT%H-%M-%S"  # ':' is illegal in Windows filenames


def _stamp() -> str:
    now = datetime.now()
    return f"{now.strftime(TS_FMT)}-{now.microsecond // 1000:03d}"


def append_submit_log(sessions_dir: Path, problem_id: str, entry: dict) -> Path:
    d = sessions_dir / problem_id
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{_stamp()}.json"
    path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return path


def write_snapshot(sessions_dir: Path, problem_id: str, code: str) -> Path:
    d = sessions_dir / problem_id / "keystrokes"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{_stamp()}.py"
    path.write_text(code, encoding="utf-8")
    return path
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_sessions.py -v`
Expected: 2 passed.

- [ ] **Step 5: Write failing endpoint tests**

Append to `backend/tests/test_api.py`:

```python
def test_run_endpoint_run_mode(client):
    resp = client.post(
        "/api/problems/demo-problem/run",
        json={"part": 1, "code": "def add(a, b):\n    return a + b\n", "mode": "run"},
    )
    assert resp.status_code == 200
    body = resp.json()
    names = {t["name"] for t in body["tests"]}
    assert names == {"test_add_small"}
    assert body["timed_out"] is False


def test_submit_writes_session_log(client, tmp_path):
    code = "def add(a, b):\n    return None\n"  # fails trap + regular tests
    resp = client.post(
        "/api/problems/demo-problem/run",
        json={
            "part": 1,
            "code": code,
            "mode": "submit",
            "client_stats": {
                "elapsed_total_s": 100,
                "elapsed_part_s": 50,
                "run_count": 3,
                "submit_count": 1,
                "skipped_parts": [],
            },
        },
    )
    assert resp.status_code == 200
    logs = list((tmp_path / "sessions" / "demo-problem").glob("*.json"))
    assert len(logs) == 1
    entry = json.loads(logs[0].read_text(encoding="utf-8"))
    assert entry["problem_id"] == "demo-problem"
    assert entry["part"] == 1
    assert entry["elapsed_total_s"] == 100
    assert entry["traps_failed"] == ["silent-none"]
    assert entry["regressions"] == []  # part 1: nothing earlier to regress
    assert entry["final_code"] == code


def test_submit_records_regressions(client, tmp_path):
    # part-2 submit where a PART-1 test fails -> regression in response AND log
    code = "def add(a, b):\n    return 0\n\ndef scale(a, factor):\n    return a * factor\n"
    resp = client.post(
        "/api/problems/demo-problem/run",
        json={"part": 2, "code": code, "mode": "submit"},
    )
    body = resp.json()
    failed_part1 = [
        t for t in body["tests"] if t["outcome"] != "passed" and t["part"] == 1
    ]
    assert failed_part1  # add(1,2)==3 broken
    logs = sorted((tmp_path / "sessions" / "demo-problem").glob("*.json"))
    entry = json.loads(logs[-1].read_text(encoding="utf-8"))
    assert "test_add_small" in entry["regressions"]


def test_run_rejects_out_of_range_part(client):
    resp = client.post(
        "/api/problems/demo-problem/run",
        json={"part": 99, "code": "x = 1", "mode": "run"},
    )
    assert resp.status_code == 422


def test_snapshot_endpoint(client, tmp_path):
    resp = client.post(
        "/api/problems/demo-problem/snapshot", json={"code": "wip = True"}
    )
    assert resp.status_code == 200
    snaps = list(
        (tmp_path / "sessions" / "demo-problem" / "keystrokes").glob("*.py")
    )
    assert len(snaps) == 1


def test_snapshot_unknown_problem_404s(client):
    assert (
        client.post("/api/problems/nope/snapshot", json={"code": "x"}).status_code
        == 404
    )
```

Also add `import json` to the imports at the top of `test_api.py`.

- [ ] **Step 6: Run to verify failure**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: new tests FAIL (404/405 — routes don't exist yet).

- [ ] **Step 7: Add routes to `backend/app/main.py`**

Replace the import block at the top of the file with:

```python
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import problems, runner, sessions
```

Append at the end of the file:

```python
class ClientStats(BaseModel):
    elapsed_total_s: int = 0
    elapsed_part_s: int = 0
    run_count: int = 0
    submit_count: int = 0
    skipped_parts: list[int] = Field(default_factory=list)


class RunRequest(BaseModel):
    part: int = Field(ge=1)
    code: str
    mode: Literal["run", "submit"]
    client_stats: ClientStats = Field(default_factory=ClientStats)


class SnapshotRequest(BaseModel):
    code: str


@app.post("/api/problems/{problem_id}/run")
def run(problem_id: str, req: RunRequest):
    try:
        pdir = problems.problem_dir(problems_dir(), problem_id)
        meta = problems.load_meta(problems_dir(), problem_id)
    except problems.ProblemNotFound:
        raise HTTPException(404)
    if req.part > meta["num_parts"]:
        raise HTTPException(422, "part out of range")
    result = runner.run_tests(pdir, req.code, req.part, req.mode)
    if req.mode == "submit":
        failed = [t for t in result["tests"] if t["outcome"] != "passed"]
        entry = {
            "problem_id": problem_id,
            "part": req.part,
            "elapsed_total_s": req.client_stats.elapsed_total_s,
            "elapsed_part_s": req.client_stats.elapsed_part_s,
            "run_count": req.client_stats.run_count,
            "submit_count": req.client_stats.submit_count,
            "traps_failed": sorted({t["trap"] for t in failed if t["trap"]}),
            "regressions": [t["name"] for t in failed if 0 < t["part"] < req.part],
            "skipped_parts": req.client_stats.skipped_parts,
            "timed_out": result["timed_out"],
            "final_code": req.code,
        }
        sessions.append_submit_log(sessions_dir(), problem_id, entry)
    return result


@app.post("/api/problems/{problem_id}/snapshot")
def snapshot(problem_id: str, req: SnapshotRequest):
    try:
        problems.problem_dir(problems_dir(), problem_id)
    except problems.ProblemNotFound:
        raise HTTPException(404)
    sessions.write_snapshot(sessions_dir(), problem_id, req.code)
    return {"ok": True}
```

- [ ] **Step 8: Run the whole backend suite**

Run: `cd backend && .venv/Scripts/python -m pytest -v`
Expected: all tests pass (8 problems + 10 api + 8 runner + 2 sessions = 28).

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat(backend): run/submit/snapshot endpoints with session logging"
```

---

### Task 5: Frontend scaffold + dev orchestration

**Files:**
- Create: `frontend/` (Vite react-ts scaffold + deps)
- Modify: `frontend/vite.config.ts` (proxy + tailwind plugin)
- Modify: `frontend/src/index.css` (tailwind import + statement styles)
- Create: `package.json` (root), `Makefile`, `.gitignore`, `README.md`

No TDD here — this is configuration. Verification = servers start and proxy works.

- [ ] **Step 1: Scaffold Vite app and install deps**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @monaco-editor/react react-markdown rehype-highlight highlight.js react-resizable-panels
npm install -D tailwindcss @tailwindcss/vite vitest
```

- [ ] **Step 2: Configure Vite — proxy + Tailwind v4**

Replace `frontend/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
```

Replace `frontend/src/index.css` entirely:

```css
@import "tailwindcss";

/* Rendered problem statements */
.statement {
  line-height: 1.6;
}
.statement h1, .statement h2, .statement h3 {
  font-weight: 700;
  margin: 1em 0 0.5em;
}
.statement h2 { font-size: 1.25rem; }
.statement h3 { font-size: 1.05rem; }
.statement p, .statement ul, .statement ol { margin: 0.5em 0; }
.statement ul { list-style: disc; padding-left: 1.5em; }
.statement ol { list-style: decimal; padding-left: 1.5em; }
.statement code {
  background: #1f2937;
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.9em;
}
.statement pre {
  background: #111827;
  padding: 0.75em;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}
.statement pre code { background: none; padding: 0; }
.statement table { border-collapse: collapse; margin: 0.5em 0; }
.statement th, .statement td { border: 1px solid #374151; padding: 0.3em 0.6em; }
```

Delete `frontend/src/App.css` and remove its import from `App.tsx` (we replace App.tsx in Task 7 anyway).

Add to `frontend/package.json` scripts: `"test": "vitest run"`.

- [ ] **Step 3: Root orchestration files**

`package.json` (repo root — note `cd backend` so the venv-relative path works from npm's cmd shell):

```json
{
  "name": "interview-platform",
  "private": true,
  "scripts": {
    "dev": "concurrently -n api,web -c blue,green \"npm run dev:api\" \"npm run dev:web\"",
    "dev:api": "cd backend && .venv\\Scripts\\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload",
    "dev:web": "npm --prefix frontend run dev",
    "test:api": "cd backend && .venv\\Scripts\\python -m pytest -q",
    "test:web": "npm --prefix frontend run test",
    "setup": "python -m venv backend/.venv && backend\\.venv\\Scripts\\pip install -r backend/requirements.txt && npm install && npm --prefix frontend install"
  },
  "devDependencies": {
    "concurrently": "^9.0.0"
  }
}
```

Run `npm install` at the repo root.

`Makefile`:

```makefile
dev:
	npm run dev

setup:
	npm run setup

test:
	npm run test:api && npm run test:web
```

`.gitignore`:

```
node_modules/
backend/.venv/
__pycache__/
.pytest_cache/
frontend/dist/
```

`README.md`:

```markdown
# Interview Practice Platform

Local practice harness for multi-part practical-coding interview rounds.
Statement left, Monaco editor right, pytest results below. Localhost only.

## Setup (once)

    npm run setup

## Run

    npm run dev        # or: make dev

Backend: http://127.0.0.1:8000 · Frontend: http://localhost:5173

## Adding a problem

Make a folder under `problems/` — see
`docs/superpowers/specs/2026-07-15-interview-platform-design.md` for the format.
No registration step; it appears in the list on refresh.

## Tests

    npm run test:api   # backend (pytest)
    npm run test:web   # frontend logic (vitest)
```

- [ ] **Step 4: Verify both servers start and proxy works**

```bash
npm run dev &
sleep 15
curl -s http://localhost:5173/api/problems   # through the Vite proxy
```

Expected: `[]` returned via the proxy (frontend port answering an /api route proves proxying). Then stop the dev servers.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: frontend scaffold, vite proxy, root dev orchestration"
```

---

### Task 6: Frontend core logic modules

**Files:**
- Create: `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/storage.ts`, `frontend/src/session.ts`
- Create: `frontend/src/session.test.ts`

**Interfaces:**
- Consumes: backend API shapes from Tasks 2/4.
- Produces (used by Tasks 7–9):
  - `types.ts`: `ProblemMeta`, `PartContent`, `TestResult`, `RunResponse`, `ClientStats`, `RunRequestBody`
  - `api.ts`: `api.listProblems()`, `api.getPart(id, n)`, `api.getSolution(id, n)`, `api.run(id, body)`, `api.snapshot(id, code)`
  - `storage.ts`: `SessionState`, `freshSession(now)`, `loadSession/saveSession`, `loadBuffer/saveBuffer`, `loadNotes/saveNotes`
  - `session.ts`: `findRegressions`, `allGreen`, `formatClock`, `budgetStatus`, `resolveBuffer`, `clientStats`

- [ ] **Step 1: `frontend/src/types.ts`** (mirror backend EXACTLY — snake_case)

```ts
export interface ProblemMeta {
  id: string;
  title: string;
  company: string;
  round: string;
  language: string;
  time_limit_min: number;
  part_budgets_min: number[];
  tags: string[];
  num_parts: number;
}

export interface PartContent {
  statement: string;
  starter: string | null;
  sample_tests: string;
}

export interface TestResult {
  name: string;
  part: number;
  outcome: "passed" | "failed" | "error";
  duration: number;
  trap: string | null;
  message: string | null;
}

export interface RunResponse {
  tests: TestResult[];
  stdout: string;
  stderr: string;
  timed_out: boolean;
  exit_code: number;
}

export interface ClientStats {
  elapsed_total_s: number;
  elapsed_part_s: number;
  run_count: number;
  submit_count: number;
  skipped_parts: number[];
}

export interface RunRequestBody {
  part: number;
  code: string;
  mode: "run" | "submit";
  client_stats: ClientStats;
}
```

- [ ] **Step 2: `frontend/src/api.ts`**

```ts
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
```

- [ ] **Step 3: `frontend/src/storage.ts`**

```ts
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
  return raw ? (JSON.parse(raw) as SessionState) : null;
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
```

- [ ] **Step 4: Write failing tests `frontend/src/session.test.ts`**

```ts
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
```

- [ ] **Step 5: Run to verify failure**

Run: `cd frontend && npm run test`
Expected: FAIL — `./session` doesn't exist.

- [ ] **Step 6: Implement `frontend/src/session.ts`**

```ts
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
```

- [ ] **Step 7: Run to verify pass**

Run: `cd frontend && npm run test`
Expected: all vitest tests pass. Also run `npx tsc -b` — no type errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): typed api client, storage, session logic with tests"
```

---

### Task 7: Single-part harness UI — SHIP POINT

Three-pane shell, Monaco, statement rendering, Run → results, output tab,
keyboard shortcuts, reset-to-starter. After this task the platform is usable
for single-part problems end to end.

**Files:**
- Replace: `frontend/src/App.tsx`
- Create: `frontend/src/ProblemView.tsx`
- Create: `frontend/src/components/ProblemPane.tsx`, `frontend/src/components/EditorPane.tsx`, `frontend/src/components/ResultsPane.tsx`
- Modify: `frontend/src/main.tsx` (drop StrictMode double-mount only if it causes duplicate snapshot posts; otherwise leave as scaffolded)
- Create: `problems/scratch-fizzbuzz/` (tiny 1-part problem to develop against, deleted in Task 10)

**Interfaces:**
- Consumes: everything from Task 6.
- Produces: `<ProblemView meta={ProblemMeta} />`; `ProblemPane({meta, viewedPart, unlockedPart, content, onSelectPart, onReveal, timer})`, `EditorPane({code, onChange, onRun, onSubmit, onReset, running})`, `ResultsPane({results, currentPart, error, notes, onNotesChange})`. `onReveal` and `timer` are wired in Tasks 8/9 — props exist now, pass no-ops/null.

- [ ] **Step 1: Temporary dev problem `problems/scratch-fizzbuzz/`**

`problems/scratch-fizzbuzz/meta.yaml`:

```yaml
id: scratch-fizzbuzz
title: Scratch FizzBuzz
company: Dev
round: scratch
language: python
time_limit_min: 10
part_budgets_min: [10]
tags: [scratch]
```

`problems/scratch-fizzbuzz/part-1/statement.md`:

```markdown
## FizzBuzz

Return `"fizz"` for multiples of 3, `"buzz"` for 5, `"fizzbuzz"` for both,
else the number as a string.

### Example

    fizzbuzz(3) == "fizz"
```

`problems/scratch-fizzbuzz/part-1/starter.py`:

```python
def fizzbuzz(n):
    pass
```

`problems/scratch-fizzbuzz/part-1/tests.py`:

```python
import pytest
from solution import fizzbuzz


@pytest.mark.sample
def test_three():
    assert fizzbuzz(3) == "fizz"


@pytest.mark.sample
def test_plain():
    assert fizzbuzz(7) == "7"


def test_fifteen():
    assert fizzbuzz(15) == "fizzbuzz"


@pytest.mark.trap("string-vs-int")
def test_returns_string_not_int():
    assert fizzbuzz(1) == "1"
```

`problems/scratch-fizzbuzz/part-1/solution.py`:

```python
def fizzbuzz(n):
    out = ""
    if n % 3 == 0:
        out += "fizz"
    if n % 5 == 0:
        out += "buzz"
    return out or str(n)
```

- [ ] **Step 2: Replace `frontend/src/App.tsx`** (problem list + hash routing)

```tsx
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
```

Also set the dark base: in `frontend/index.html`, add `class="bg-gray-900 text-gray-100"` to `<body>` and set `<title>Interview Practice</title>`.

- [ ] **Step 3: Create `frontend/src/ProblemView.tsx`** (state owner)

```tsx
import { useCallback, useEffect, useRef, useState } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { api } from "./api";
import { allGreen, clientStats, resolveBuffer } from "./session";
import * as store from "./storage";
import type { PartContent, ProblemMeta, RunResponse } from "./types";
import { EditorPane } from "./components/EditorPane";
import { ProblemPane } from "./components/ProblemPane";
import { ResultsPane } from "./components/ResultsPane";

export function ProblemView({ meta }: { meta: ProblemMeta }) {
  const id = meta.id;
  const [session, setSession] = useState(
    () => store.loadSession(id) ?? store.freshSession(Date.now()),
  );
  useEffect(() => store.saveSession(id, session), [id, session]);

  const activePart = Math.min(session.unlockedPart, meta.num_parts);
  const [viewedPart, setViewedPart] = useState(activePart);
  const [parts, setParts] = useState<Record<number, PartContent>>({});
  const [code, setCode] = useState<string | null>(null);
  const [results, setResults] = useState<RunResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState(() => store.loadNotes(id));
  const runSeq = useRef(0);

  // fetch viewed part + part 1 (for the starter) lazily
  useEffect(() => {
    for (const n of new Set([viewedPart, 1])) {
      if (!parts[n]) {
        api.getPart(id, n).then((p) => setParts((prev) => ({ ...prev, [n]: p })));
      }
    }
  }, [id, viewedPart, parts]);

  // initialize the buffer once part 1 (starter) is available
  const starter = parts[1]?.starter ?? null;
  useEffect(() => {
    if (code === null && starter !== null) {
      setCode(resolveBuffer(activePart, (p) => store.loadBuffer(id, p), starter));
    }
  }, [code, starter, activePart, id]);

  const onCodeChange = useCallback(
    (value: string) => {
      setCode(value);
      store.saveBuffer(id, activePart, value);
    },
    [id, activePart],
  );

  const doRun = useCallback(
    async (mode: "run" | "submit") => {
      if (code === null) return;
      const seq = ++runSeq.current;
      setRunning(true);
      setError(null);
      const stats = clientStats(session, activePart, Date.now());
      setSession((s) =>
        mode === "run"
          ? { ...s, runCount: s.runCount + 1 }
          : { ...s, submitCount: s.submitCount + 1 },
      );
      try {
        const resp = await api.run(id, {
          part: activePart,
          code,
          mode,
          client_stats: stats,
        });
        if (seq !== runSeq.current) return; // stale — a newer run superseded us
        setResults(resp);
        if (mode === "submit" && allGreen(resp)) {
          // unlock flow lands in Task 8
        }
      } catch (e) {
        if (seq === runSeq.current) setError(String(e));
      } finally {
        if (seq === runSeq.current) setRunning(false);
      }
    },
    [id, activePart, code, session],
  );

  const onReset = useCallback(() => {
    const target =
      activePart === 1 ? (starter ?? "") : (store.loadBuffer(id, activePart - 1) ?? starter ?? "");
    if (window.confirm("Reset editor to starting state for this part?")) {
      setCode(target);
      store.saveBuffer(id, activePart, target);
    }
  }, [id, activePart, starter]);

  const onNotesChange = useCallback(
    (v: string) => {
      setNotes(v);
      store.saveNotes(id, v);
    },
    [id],
  );

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-4 border-b border-gray-700 px-4 py-2">
        <a href="#/" className="text-sm text-gray-400 hover:text-gray-200">
          ← Problems
        </a>
        <span className="font-semibold">{meta.title}</span>
        <span className="text-sm text-gray-500">{meta.company}</span>
      </header>
      <PanelGroup direction="vertical" className="flex-1">
        <Panel defaultSize={70} minSize={30}>
          <PanelGroup direction="horizontal">
            <Panel defaultSize={40} minSize={20}>
              <ProblemPane
                meta={meta}
                viewedPart={viewedPart}
                unlockedPart={session.unlockedPart}
                content={parts[viewedPart] ?? null}
                onSelectPart={setViewedPart}
                onReveal={() => {}}
                timer={null}
              />
            </Panel>
            <PanelResizeHandle className="w-1 bg-gray-700 hover:bg-gray-500" />
            <Panel minSize={30}>
              <EditorPane
                code={code ?? "# loading…"}
                onChange={onCodeChange}
                onRun={() => doRun("run")}
                onSubmit={() => doRun("submit")}
                onReset={onReset}
                running={running}
              />
            </Panel>
          </PanelGroup>
        </Panel>
        <PanelResizeHandle className="h-1 bg-gray-700 hover:bg-gray-500" />
        <Panel defaultSize={30} minSize={10}>
          <ResultsPane
            results={results}
            currentPart={activePart}
            error={error}
            notes={notes}
            onNotesChange={onNotesChange}
          />
        </Panel>
      </PanelGroup>
    </div>
  );
}
```

- [ ] **Step 4: Create `frontend/src/components/ProblemPane.tsx`**

```tsx
import Markdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import type { PartContent, ProblemMeta } from "../types";
import type { TimerInfo } from "./TimerBar";
import { TimerBar } from "./TimerBar";

interface Props {
  meta: ProblemMeta;
  viewedPart: number;
  unlockedPart: number;
  content: PartContent | null;
  onSelectPart: (n: number) => void;
  onReveal: (n: number) => void;
  timer: TimerInfo | null;
}

export function ProblemPane({
  meta,
  viewedPart,
  unlockedPart,
  content,
  onSelectPart,
  onReveal,
  timer,
}: Props) {
  const partNums = Array.from({ length: meta.num_parts }, (_, i) => i + 1);
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-1 border-b border-gray-700 px-2 py-1">
        {partNums.map((n) => {
          const unlocked = n <= unlockedPart;
          const revealable = n === unlockedPart + 1;
          return (
            <button
              key={n}
              onClick={() => (unlocked ? onSelectPart(n) : revealable ? onReveal(n) : undefined)}
              disabled={!unlocked && !revealable}
              className={
                "rounded px-3 py-1 text-sm " +
                (n === viewedPart
                  ? "bg-gray-700 font-semibold"
                  : unlocked
                    ? "hover:bg-gray-800"
                    : revealable
                      ? "text-gray-500 hover:bg-gray-800"
                      : "cursor-not-allowed text-gray-600")
              }
              title={!unlocked ? (revealable ? "Reveal anyway" : "Locked") : undefined}
            >
              {unlocked ? `Part ${n}` : `🔒 Part ${n}`}
            </button>
          );
        })}
        <div className="ml-auto">{timer && <TimerBar info={timer} />}</div>
      </div>
      <div className="statement flex-1 overflow-y-auto p-4 text-sm">
        {content ? (
          <>
            <Markdown rehypePlugins={[rehypeHighlight]}>{content.statement}</Markdown>
            {content.sample_tests && (
              <>
                <h3 className="mt-4 font-bold">Sample tests</h3>
                <pre>
                  <code>{content.sample_tests}</code>
                </pre>
              </>
            )}
          </>
        ) : (
          <span className="text-gray-500">Loading…</span>
        )}
      </div>
    </div>
  );
}
```

Create a minimal `frontend/src/components/TimerBar.tsx` now so imports resolve (real logic in Task 9):

```tsx
export interface TimerInfo {
  totalElapsedS: number;
  totalLimitMin: number;
  part: number;
  partElapsedS: number;
  partBudgetMin: number;
}

export function TimerBar({ info: _info }: { info: TimerInfo }) {
  return null; // implemented in Task 9
}
```

- [ ] **Step 5: Create `frontend/src/components/EditorPane.tsx`**

```tsx
import Editor, { type OnMount } from "@monaco-editor/react";
import { useRef } from "react";

interface Props {
  code: string;
  onChange: (v: string) => void;
  onRun: () => void;
  onSubmit: () => void;
  onReset: () => void;
  running: boolean;
}

export function EditorPane({ code, onChange, onRun, onSubmit, onReset, running }: Props) {
  // keep latest handlers so Monaco commands (bound once) never go stale
  const handlers = useRef({ onRun, onSubmit });
  handlers.current = { onRun, onSubmit };

  const onMount: OnMount = (editor, monaco) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () =>
      handlers.current.onRun(),
    );
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter,
      () => handlers.current.onSubmit(),
    );
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-gray-700 px-2 py-1">
        <button
          onClick={onRun}
          disabled={running}
          className="rounded bg-blue-600 px-3 py-1 text-sm font-semibold hover:bg-blue-500 disabled:opacity-50"
        >
          {running ? "Running…" : "Run"}
        </button>
        <button
          onClick={onSubmit}
          disabled={running}
          className="rounded bg-green-600 px-3 py-1 text-sm font-semibold hover:bg-green-500 disabled:opacity-50"
        >
          Submit
        </button>
        <span className="text-xs text-gray-500">Ctrl+Enter · Ctrl+Shift+Enter</span>
        <button
          onClick={onReset}
          className="ml-auto rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-800"
        >
          Reset to starter
        </button>
      </div>
      <div className="flex-1">
        <Editor
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(v) => onChange(v ?? "")}
          onMount={onMount}
          options={{
            tabSize: 4,
            insertSpaces: true,
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false,
            matchBrackets: "always",
          }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Create `frontend/src/components/ResultsPane.tsx`**

```tsx
import { useState } from "react";
import { findRegressions } from "../session";
import type { RunResponse, TestResult } from "../types";

interface Props {
  results: RunResponse | null;
  currentPart: number;
  error: string | null;
  notes: string;
  onNotesChange: (v: string) => void;
}

type Tab = "tests" | "output" | "notes";

function Row({ t }: { t: TestResult }) {
  const [open, setOpen] = useState(false);
  const color =
    t.outcome === "passed" ? "text-green-400" : t.outcome === "failed" ? "text-red-400" : "text-orange-400";
  return (
    <div className="border-b border-gray-800 py-1">
      <button className="flex w-full items-center gap-2 text-left" onClick={() => setOpen(!open)}>
        <span className={color}>{t.outcome === "passed" ? "✓" : "✗"}</span>
        <span className="font-mono text-sm">{t.name}</span>
        <span className="text-xs text-gray-500">part {t.part}</span>
        {t.trap && t.outcome !== "passed" && (
          <span className="rounded bg-yellow-900 px-2 py-0.5 text-xs text-yellow-300">
            trap: {t.trap}
          </span>
        )}
        <span className="ml-auto text-xs text-gray-500">{(t.duration * 1000).toFixed(0)}ms</span>
      </button>
      {open && t.message && (
        <pre className="mt-1 overflow-x-auto rounded bg-gray-950 p-2 text-xs text-red-300">
          {t.message}
        </pre>
      )}
    </div>
  );
}

export function ResultsPane({ results, currentPart, error, notes, onNotesChange }: Props) {
  const [tab, setTab] = useState<Tab>("tests");
  const regressions = results ? findRegressions(results.tests, currentPart) : [];
  const tabs: Tab[] = ["tests", "output", "notes"];
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex gap-1 border-b border-gray-700 px-2 py-1">
        {tabs.map((name) => (
          <button
            key={name}
            onClick={() => setTab(name)}
            className={
              "rounded px-3 py-0.5 text-sm capitalize " +
              (tab === name ? "bg-gray-700 font-semibold" : "hover:bg-gray-800")
            }
          >
            {name}
          </button>
        ))}
        {results && (
          <span className="ml-auto self-center text-xs text-gray-500">
            {results.tests.filter((t) => t.outcome === "passed").length}/{results.tests.length} passed
          </span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {tab === "tests" && (
          <>
            {regressions.length > 0 && (
              <div className="mb-2 rounded border-2 border-red-500 bg-red-950 p-3 font-semibold text-red-200">
                ⚠ REGRESSION — {regressions.length} previously-passing earlier-part test
                {regressions.length > 1 ? "s" : ""} now failing:{" "}
                {regressions.map((r) => r.name).join(", ")}
              </div>
            )}
            {error && <div className="mb-2 rounded bg-red-950 p-2 text-red-300">{error}</div>}
            {results?.timed_out && (
              <div className="mb-2 rounded bg-orange-950 p-2 text-orange-300">
                Timed out after 10s — infinite loop? Process was killed.
              </div>
            )}
            {results === null && !error && (
              <span className="text-sm text-gray-500">Run tests to see results.</span>
            )}
            {results !== null && results.tests.length === 0 && !results.timed_out && (
              <pre className="overflow-x-auto text-xs text-gray-400">
                {results.stdout || results.stderr || "No tests collected."}
              </pre>
            )}
            {results?.tests.map((t) => <Row key={`${t.part}:${t.name}`} t={t} />)}
          </>
        )}
        {tab === "output" && (
          <pre className="overflow-x-auto text-xs text-gray-300">
            {results ? (results.stdout || "(no stdout)") + "\n\n--- stderr ---\n" + (results.stderr || "(no stderr)") : "No run yet."}
          </pre>
        )}
        {tab === "notes" && (
          <textarea
            value={notes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Assumptions you'd state out loud…"
            className="h-full w-full resize-none bg-transparent font-mono text-sm outline-none"
          />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 7: Type-check, then manual verification**

Run: `cd frontend && npx tsc -b`
Expected: no errors.

Run `npm run dev` (repo root). In the browser at `http://localhost:5173`:

1. Problem list shows "Scratch FizzBuzz". Click it.
2. Statement renders left with sample tests; Monaco shows starter code right.
3. Ctrl+Enter → 2 sample tests fail (starter returns None). Results rows expand to show assertion messages.
4. Implement fizzbuzz (paste the solution), Ctrl+Enter → samples pass.
5. Ctrl+Shift+Enter → all 4 tests pass, including the labeled trap row.
6. Break the code with `while True: pass` inside the function, Run → timeout banner after ~10s.
7. `print("hello")` in code → visible in Output tab.
8. Refresh browser → editor buffer survives. Reset to starter works (with confirm).
9. Panes resize by dragging dividers.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(frontend): working single-part harness (shell, monaco, run, results)"
```

---

### Task 8: Submit gating, unlock flow, reveal-anyway, reference solution

**Files:**
- Modify: `frontend/src/ProblemView.tsx` (unlock + reveal handlers, wire UnlockPanel)
- Create: `frontend/src/components/UnlockPanel.tsx`

**Interfaces:**
- Consumes: Task 7 components; `api.getSolution`; `store.saveBuffer`; `allGreen`, `findRegressions`.
- Produces: `UnlockPanel({info, meta, onClose})` where `info = {part: number, resp: RunResponse, elapsedPartS: number}`.

- [ ] **Step 1: Create `frontend/src/components/UnlockPanel.tsx`**

```tsx
import { useState } from "react";
import { api } from "../api";
import { formatClock } from "../session";
import type { ProblemMeta, RunResponse } from "../types";

export interface UnlockInfo {
  part: number;
  resp: RunResponse;
  elapsedPartS: number;
}

interface Props {
  info: UnlockInfo;
  meta: ProblemMeta;
  onClose: () => void;
}

export function UnlockPanel({ info, meta, onClose }: Props) {
  const [solution, setSolution] = useState<string | null>(null);
  const last = info.part >= meta.num_parts;
  const traps = info.resp.tests.filter((t) => t.trap);
  return (
    <div className="fixed inset-y-0 right-0 z-50 w-96 overflow-y-auto border-l border-gray-600 bg-gray-800 p-5 shadow-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-green-400">
          {last ? "All parts complete 🎉" : `Part ${info.part} passed`}
        </h2>
        <button onClick={onClose} className="rounded px-2 text-gray-400 hover:bg-gray-700">
          ✕
        </button>
      </div>
      <dl className="mt-4 space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-gray-400">Time on part</dt>
          <dd>
            {formatClock(info.elapsedPartS)} / {meta.part_budgets_min[info.part - 1]}:00
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-400">Tests passed</dt>
          <dd>
            {info.resp.tests.filter((t) => t.outcome === "passed").length}/{info.resp.tests.length}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-400">Traps</dt>
          <dd>
            {traps.length === 0
              ? "none in this run"
              : traps.map((t) => `${t.trap} ${t.outcome === "passed" ? "✓" : "✗"}`).join(", ")}
          </dd>
        </div>
      </dl>
      {!last && <p className="mt-4 text-sm text-gray-300">Part {info.part + 1} is unlocked. Your code carries forward.</p>}
      <div className="mt-6">
        {solution === null ? (
          <button
            onClick={() => api.getSolution(meta.id, info.part).then((r) => setSolution(r.solution))}
            className="rounded border border-gray-600 px-3 py-1 text-sm text-gray-300 hover:bg-gray-700"
          >
            Show reference solution
          </button>
        ) : (
          <pre className="overflow-x-auto rounded bg-gray-950 p-3 text-xs">{solution}</pre>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Wire unlock + reveal into `ProblemView.tsx`**

Add imports:

```tsx
import { UnlockPanel, type UnlockInfo } from "./components/UnlockPanel";
```

Add state below the other `useState` calls:

```tsx
const [unlockInfo, setUnlockInfo] = useState<UnlockInfo | null>(null);
```

Replace the `// unlock flow lands in Task 8` branch inside `doRun` with:

```tsx
        if (mode === "submit" && allGreen(resp)) {
          const elapsedPartS = clientStats(session, activePart, Date.now()).elapsed_part_s;
          setUnlockInfo({ part: activePart, resp, elapsedPartS });
          if (activePart < meta.num_parts) {
            store.saveBuffer(id, activePart + 1, code); // carry forward
            setSession((s) => ({
              ...s,
              unlockedPart: activePart + 1,
              partStartedAt: { ...s.partStartedAt, [activePart + 1]: Date.now() },
            }));
            setViewedPart(activePart + 1);
          }
        }
```

Add a reveal handler after `onReset` (spec: escape hatch marks the prior part skipped):

```tsx
  const onReveal = useCallback(
    (nextPart: number) => {
      if (
        !window.confirm(
          `Reveal Part ${nextPart} without passing Part ${activePart}? ` +
            `Part ${activePart} will be logged as skipped.`,
        )
      )
        return;
      if (code !== null) store.saveBuffer(id, nextPart, code);
      setSession((s) => ({
        ...s,
        unlockedPart: nextPart,
        skippedParts: [...new Set([...s.skippedParts, activePart])],
        partStartedAt: { ...s.partStartedAt, [nextPart]: Date.now() },
      }));
      setViewedPart(nextPart);
    },
    [id, code, activePart],
  );
```

Pass it to `ProblemPane` (replace `onReveal={() => {}}` with `onReveal={onReveal}`).

Render the panel just inside the root `<div className="flex h-screen flex-col">`, before `<header>`:

```tsx
      {unlockInfo && (
        <UnlockPanel info={unlockInfo} meta={meta} onClose={() => setUnlockInfo(null)} />
      )}
```

One subtlety: when the part advances, `activePart` changes, and the buffer-init
effect from Task 7 only runs while `code === null`. Add an effect that re-resolves
the buffer when `activePart` changes (keeps carry-forward + per-part buffers correct):

```tsx
  // when the active part changes (unlock/reveal), load that part's buffer
  const prevPart = useRef(activePart);
  useEffect(() => {
    if (prevPart.current !== activePart) {
      prevPart.current = activePart;
      setCode(resolveBuffer(activePart, (p) => store.loadBuffer(id, p), starter ?? ""));
    }
  }, [activePart, id, starter]);
```

- [ ] **Step 3: Add a 2-part dev problem to exercise gating**

Add `problems/scratch-fizzbuzz/part-2/statement.md`:

```markdown
## Part 2

Add `fizzbuzz_range(start, stop)` returning the list of fizzbuzz strings for
`range(start, stop)`. `fizzbuzz` itself must keep working — part 1 tests still run.
```

`problems/scratch-fizzbuzz/part-2/tests.py`:

```python
from solution import fizzbuzz_range


def test_range():
    assert fizzbuzz_range(1, 4) == ["1", "2", "fizz"]
```

`problems/scratch-fizzbuzz/part-2/solution.py`:

```python
def fizzbuzz(n):
    out = ""
    if n % 3 == 0:
        out += "fizz"
    if n % 5 == 0:
        out += "buzz"
    return out or str(n)


def fizzbuzz_range(start, stop):
    return [fizzbuzz(n) for n in range(start, stop)]
```

Update `problems/scratch-fizzbuzz/meta.yaml`: `part_budgets_min: [10, 10]`.

- [ ] **Step 4: Type-check + manual verification**

Run: `cd frontend && npx tsc -b` — no errors.

With `npm run dev` (clear localStorage first — DevTools → Application → Local Storage → clear):

1. Open scratch-fizzbuzz. Part 2 tab shows 🔒.
2. Solve part 1, Submit → slide-in panel: time, tests, trap status. Part 2 tab unlocks; editor keeps your code; statement pane switches to Part 2.
3. "Show reference solution" reveals only after click.
4. Part 1 tab still clickable to re-read.
5. Implement `fizzbuzz_range` but break `fizzbuzz` (e.g., return `n` not `str(n)`), Submit → loud red REGRESSION banner naming part-1 tests; part stays locked… (nothing new unlocks).
6. Fix, Submit → "All parts complete 🎉".
7. Clear localStorage again, reload: click 🔒 Part 2 directly → confirm dialog → reveals; sessions log for the next submit shows `"skipped_parts": [1]`.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(frontend): submit gating, unlock panel, reveal-anyway, solution reveal"
```

---

### Task 9: Timer, regression polish, session stats, snapshots, notes

**Files:**
- Modify: `frontend/src/components/TimerBar.tsx` (real implementation)
- Modify: `frontend/src/ProblemView.tsx` (tick, timer wiring, 30s snapshots)

**Interfaces:**
- Consumes: `budgetStatus`, `formatClock` from session.ts; `api.snapshot`.
- Produces: complete `TimerBar({info: TimerInfo})` rendering `24:31 / 60:00 · Part 2: 9:31 / 15:00` with amber/red coloring.

- [ ] **Step 1: Implement `frontend/src/components/TimerBar.tsx`** (replace stub)

```tsx
import { budgetStatus, formatClock, type BudgetStatus } from "../session";

export interface TimerInfo {
  totalElapsedS: number;
  totalLimitMin: number;
  part: number;
  partElapsedS: number;
  partBudgetMin: number;
}

const COLORS: Record<BudgetStatus, string> = {
  ok: "text-gray-300",
  amber: "text-amber-400",
  red: "text-red-400 font-semibold",
};

export function TimerBar({ info }: { info: TimerInfo }) {
  const totalStatus = budgetStatus(info.totalElapsedS, info.totalLimitMin);
  const partStatus = budgetStatus(info.partElapsedS, info.partBudgetMin);
  return (
    <span className="font-mono text-sm" title="Pressure, not enforcement">
      <span className={COLORS[totalStatus]}>
        {formatClock(info.totalElapsedS)} / {formatClock(info.totalLimitMin * 60)}
      </span>
      <span className="text-gray-600"> · </span>
      <span className={COLORS[partStatus]}>
        Part {info.part}: {formatClock(info.partElapsedS)} / {formatClock(info.partBudgetMin * 60)}
      </span>
    </span>
  );
}
```

- [ ] **Step 2: Wire ticking clock + snapshots into `ProblemView.tsx`**

Add a 1-second tick near the top of the component:

```tsx
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
```

Build the timer info (after `activePart` is computed):

```tsx
  const timer = {
    totalElapsedS: Math.floor((now - session.startedAt) / 1000),
    totalLimitMin: meta.time_limit_min,
    part: activePart,
    partElapsedS: Math.floor(
      (now - (session.partStartedAt[activePart] ?? session.startedAt)) / 1000,
    ),
    partBudgetMin: meta.part_budgets_min[activePart - 1] ?? meta.time_limit_min,
  };
```

Replace `timer={null}` with `timer={timer}` in the `ProblemPane` props.

Add the 30-second snapshot loop (spec: reconstruct code-at-minute-15). Uses a
ref so the interval isn't reset on each keystroke, and skips posting until the
buffer has loaded:

```tsx
  const codeRef = useRef(code);
  codeRef.current = code;
  useEffect(() => {
    const t = setInterval(() => {
      if (codeRef.current !== null) {
        void api.snapshot(id, codeRef.current);
      }
    }, 30_000);
    return () => clearInterval(t);
  }, [id]);
```

- [ ] **Step 3: Type-check + frontend tests still green**

Run: `cd frontend && npx tsc -b && npm run test`
Expected: no type errors, vitest green.

- [ ] **Step 4: Manual verification**

With `npm run dev`:

1. Timer ticks in the problem pane header: `0:05 / 10:00 · Part 1: 0:05 / 10:00`.
2. Refresh — elapsed time survives (localStorage timestamps, not reset).
3. To see amber/red without waiting: temporarily edit meta.yaml budgets to `[1, 1]` and `time_limit_min: 1` → amber at 48s, red at 60s. Revert after.
4. After 30+ seconds on the problem, check `sessions/scratch-fizzbuzz/keystrokes/` — snapshot .py files appear, content matches the editor.
5. Submit once, inspect `sessions/scratch-fizzbuzz/<ts>.json`: elapsed fields nonzero, run/submit counts match what you did, `final_code` present.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(frontend): live timer with budgets, 30s keystroke snapshots"
```

---

### Task 10: Seed problem — affirm-payment-allocator

The reference implementation of the problem format. Starter uses floats on
purpose; trap tests catch the drift. All solutions are integer-cents based.
The float traps are the single most valuable thing in the platform — Step 6
verifies each one actually fires.

**Files:**
- Create: `problems/affirm-payment-allocator/` (meta.yaml + 3 parts)
- Delete: `problems/scratch-fizzbuzz/` (dev scaffold, superseded)

**Design invariants (make the parts test forward-compatibly):**
- `allocate_payment` always returns a dict — part 1 `{"balances": [...]}`, part 2 adds `"credit"`, part 3 adds per-installment `"fee_remaining"`/`"principal_remaining"`.
- Earlier parts' tests assert only the keys they know (`(id, remaining)` tuples, `credit` scalar) — never whole-dict equality — so part-3 code still passes part-1 tests.
- Part-3 input may be `{"id", "fee", "principal"}` OR legacy `{"id", "due"}` (treated as principal-only). This keeps parts 1–2 tests running unchanged.

- [ ] **Step 1: meta.yaml and Part 1**

`problems/affirm-payment-allocator/meta.yaml`:

```yaml
id: affirm-payment-allocator
title: Installment Payment Allocator
company: Affirm
round: practical-coding
language: python
time_limit_min: 60
part_budgets_min: [15, 15, 15]
tags: [ledger, money, allocation]
```

`problems/affirm-payment-allocator/part-1/statement.md`:

```markdown
## Installment Payment Allocator

You're on the servicing team. A customer's purchase is split into fixed
installments. When a payment arrives, apply it to installments **oldest
first** and report what's still owed.

### Part 1

Implement `allocate_payment(installments, payment)`.

- `installments`: list of dicts, oldest first. Each has an `"id"` (string)
  and `"due"` (dollars): `{"id": "inst-1", "due": 25.00}`
- `payment`: dollars. In this part, upstream billing guarantees every payment
  exactly covers a whole number of installments, oldest first. Don't validate
  that; it's guaranteed.
- Return `{"balances": [...]}` — one entry per installment, **original
  order**, each `{"id": ..., "remaining": ...}`. (The servicing API returns
  an object so we can extend it later.)

### Example

    allocate_payment(
        [{"id": "a", "due": 25.00}, {"id": "b", "due": 25.00}],
        25.00,
    )
    == {"balances": [{"id": "a", "remaining": 0.0}, {"id": "b", "remaining": 25.0}]}
```

`problems/affirm-payment-allocator/part-1/starter.py` (floats on purpose — never flag it):

```python
def allocate_payment(installments, payment):
    # apply oldest first
    balances = []
    for item in installments:
        pay = min(item["due"], payment)
        payment = payment - pay
        balances.append({"id": item["id"], "remaining": item["due"] - pay})
    return {"balances": balances}
```

`problems/affirm-payment-allocator/part-1/tests.py`:

```python
import pytest
from solution import allocate_payment


def slim(result):
    return [(b["id"], b["remaining"]) for b in result["balances"]]


@pytest.mark.sample
def test_payment_clears_oldest_installment():
    result = allocate_payment(
        [{"id": "a", "due": 25.00}, {"id": "b", "due": 25.00}], 25.00
    )
    assert [(b["id"], b["remaining"]) for b in result["balances"]] == [
        ("a", 0.0),
        ("b", 25.0),
    ]


@pytest.mark.sample
def test_zero_payment_changes_nothing():
    result = allocate_payment([{"id": "a", "due": 10.00}], 0.0)
    assert [(b["id"], b["remaining"]) for b in result["balances"]] == [("a", 10.0)]


def test_payment_covers_everything():
    result = allocate_payment(
        [{"id": "a", "due": 10.00}, {"id": "b", "due": 20.00}], 30.00
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0)]


def test_result_preserves_input_order():
    result = allocate_payment(
        [{"id": "z", "due": 5.00}, {"id": "a", "due": 5.00}, {"id": "m", "due": 5.00}],
        5.00,
    )
    assert [b["id"] for b in result["balances"]] == ["z", "a", "m"]


@pytest.mark.trap("float-precision")
def test_dime_installments_leave_exact_zero():
    # 0.30 exactly covers the first two installments (0.10 + 0.20).
    # Float arithmetic leaves ~2.8e-17 on installment b. Cents don't.
    result = allocate_payment(
        [{"id": "a", "due": 0.10}, {"id": "b", "due": 0.20}, {"id": "c", "due": 0.30}],
        0.30,
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0), ("c", 0.30)]
```

`problems/affirm-payment-allocator/part-1/solution.py`:

```python
def allocate_payment(installments, payment):
    """Allocate oldest-first. All arithmetic in integer cents."""
    remaining_cents = round(payment * 100)
    balances = []
    for installment in installments:
        due_cents = round(installment["due"] * 100)
        paid = min(due_cents, remaining_cents)
        remaining_cents -= paid
        balances.append({"id": installment["id"], "remaining": (due_cents - paid) / 100})
    return {"balances": balances}
```

- [ ] **Step 2: Part 2 — partial payments and overpayment**

`problems/affirm-payment-allocator/part-2/statement.md`:

```markdown
### Part 2 — Partial payments and overpayment

The exact-cover guarantee is gone. Real payments are any amount.

- A payment may **partially** cover an installment: pay it down, and any
  leftover cascades to the next-oldest installment.
- A payment may exceed everything owed. Whatever is left after all
  installments are cleared is returned to the customer as **credit**.
- Add a `"credit"` key to the result: dollars left over (`0.0` when the
  payment was fully absorbed).

Part 1 behavior must not change — those tests still run.

### Example

    allocate_payment([{"id": "a", "due": 10.00}], 12.50)
    == {"balances": [{"id": "a", "remaining": 0.0}], "credit": 2.50}
```

`problems/affirm-payment-allocator/part-2/tests.py`:

```python
import pytest
from solution import allocate_payment


def slim(result):
    return [(b["id"], b["remaining"]) for b in result["balances"]]


@pytest.mark.sample
def test_partial_payment_cascades_oldest_first():
    result = allocate_payment(
        [{"id": "a", "due": 10.00}, {"id": "b", "due": 10.00}], 15.00
    )
    assert [(b["id"], b["remaining"]) for b in result["balances"]] == [
        ("a", 0.0),
        ("b", 5.0),
    ]
    assert result["credit"] == 0.0


@pytest.mark.sample
def test_overpayment_returned_as_credit():
    result = allocate_payment([{"id": "a", "due": 10.00}], 12.50)
    assert result["credit"] == 2.50


def test_no_installments_full_credit():
    result = allocate_payment([], 7.00)
    assert result["balances"] == []
    assert result["credit"] == 7.00


def test_exact_payoff_zero_credit():
    result = allocate_payment(
        [{"id": "a", "due": 3.00}, {"id": "b", "due": 4.00}], 7.00
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0)]
    assert result["credit"] == 0.0


@pytest.mark.trap("remainder-distribution")
def test_credit_is_exact_after_cascading():
    # float: 0.40 - 0.10 - 0.20 = 0.10000000000000003, not 0.10
    result = allocate_payment(
        [{"id": "a", "due": 0.10}, {"id": "b", "due": 0.20}], 0.40
    )
    assert result["credit"] == 0.10


@pytest.mark.trap("remainder-distribution")
def test_boundary_installment_balance_is_exact():
    # float: the third dime ends up owing 0.050000000000000017, not 0.05
    result = allocate_payment(
        [{"id": "a", "due": 0.10}, {"id": "b", "due": 0.10}, {"id": "c", "due": 0.10}],
        0.25,
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0), ("c", 0.05)]
    assert result["credit"] == 0.0
```

`problems/affirm-payment-allocator/part-2/solution.py`:

```python
def allocate_payment(installments, payment):
    """Allocate oldest-first; leftover cascades; surplus becomes credit.

    All arithmetic in integer cents.
    """
    remaining_cents = round(payment * 100)
    balances = []
    for installment in installments:
        due_cents = round(installment["due"] * 100)
        paid = min(due_cents, remaining_cents)
        remaining_cents -= paid
        balances.append({"id": installment["id"], "remaining": (due_cents - paid) / 100})
    return {"balances": balances, "credit": remaining_cents / 100}
```

- [ ] **Step 3: Part 3 — fees before principal**

`problems/affirm-payment-allocator/part-3/statement.md`:

```markdown
### Part 3 — Fees and principal

Finance now splits each installment into a **fee** and **principal**.
Within an installment, money pays the fee first, then principal.

- New installment shape: `{"id": "a", "fee": 2.00, "principal": 23.00}`
- The old billing service still sends `{"id": "a", "due": 25.00}` — treat
  those as principal-only (`fee = 0`). Both shapes can appear in one call.
- Each balance entry now also reports `"fee_remaining"` and
  `"principal_remaining"`. Keep `"remaining"` (their sum) — dashboards
  depend on it. Keep `"credit"`.

Parts 1 and 2 must keep passing.

### Example

    allocate_payment([{"id": "a", "fee": 2.00, "principal": 8.00}], 5.00)
    == {
        "balances": [
            {"id": "a", "fee_remaining": 0.0, "principal_remaining": 5.0, "remaining": 5.0}
        ],
        "credit": 0.0,
    }
```

`problems/affirm-payment-allocator/part-3/tests.py`:

```python
import pytest
from solution import allocate_payment


@pytest.mark.sample
def test_fee_paid_before_principal():
    result = allocate_payment([{"id": "a", "fee": 2.00, "principal": 8.00}], 5.00)
    balance = result["balances"][0]
    assert balance["fee_remaining"] == 0.0
    assert balance["principal_remaining"] == 5.0
    assert balance["remaining"] == 5.0
    assert result["credit"] == 0.0


def test_payment_smaller_than_fee():
    result = allocate_payment([{"id": "a", "fee": 3.00, "principal": 7.00}], 1.00)
    balance = result["balances"][0]
    assert balance["fee_remaining"] == 2.00
    assert balance["principal_remaining"] == 7.00


def test_legacy_due_shape_still_works():
    result = allocate_payment([{"id": "a", "due": 10.00}], 4.00)
    balance = result["balances"][0]
    assert balance["remaining"] == 6.00
    assert balance["fee_remaining"] == 0.0


def test_mixed_shapes_cascade_and_credit():
    result = allocate_payment(
        [{"id": "a", "fee": 1.00, "principal": 4.00}, {"id": "b", "due": 3.00}],
        9.00,
    )
    assert [b["remaining"] for b in result["balances"]] == [0.0, 0.0]
    assert result["credit"] == 1.00


@pytest.mark.trap("float-precision")
def test_fee_principal_split_is_exact():
    # float: principal_remaining comes out 0.050000000000000017, not 0.05
    result = allocate_payment([{"id": "a", "fee": 0.10, "principal": 0.20}], 0.25)
    balance = result["balances"][0]
    assert balance["fee_remaining"] == 0.0
    assert balance["principal_remaining"] == 0.05
    assert balance["remaining"] == 0.05
```

`problems/affirm-payment-allocator/part-3/solution.py`:

```python
def _to_cents(dollars):
    return round(dollars * 100)


def allocate_payment(installments, payment):
    """Oldest-first; within an installment fees before principal.

    Accepts {"fee", "principal"} or legacy {"due"} (principal-only).
    All arithmetic in integer cents.
    """
    remaining_cents = _to_cents(payment)
    balances = []
    for installment in installments:
        fee_cents = _to_cents(installment.get("fee", 0.0))
        if "principal" in installment:
            principal_cents = _to_cents(installment["principal"])
        else:
            principal_cents = _to_cents(installment["due"])

        fee_paid = min(fee_cents, remaining_cents)
        remaining_cents -= fee_paid
        principal_paid = min(principal_cents, remaining_cents)
        remaining_cents -= principal_paid

        fee_left = fee_cents - fee_paid
        principal_left = principal_cents - principal_paid
        balances.append({
            "id": installment["id"],
            "fee_remaining": fee_left / 100,
            "principal_remaining": principal_left / 100,
            "remaining": (fee_left + principal_left) / 100,
        })
    return {"balances": balances, "credit": remaining_cents / 100}
```

- [ ] **Step 4: Delete the dev scaffold problem**

```bash
git rm -r problems/scratch-fizzbuzz
```

- [ ] **Step 5: Write a verification script**

`backend/tests/verify_seed.py` — NOT a pytest file; a script that exercises the
seed problem through the real runner exactly as the platform would:

```python
"""Verify the seed problem: solutions pass, starter fails ONLY the traps,
and every part-N solution still passes parts 1..N (forward compatibility)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app import runner  # noqa: E402

SEED = Path(__file__).parent.parent.parent / "problems" / "affirm-payment-allocator"


def check(label, ok):
    print(("PASS " if ok else "FAIL ") + label)
    return ok


def outcomes(result):
    return {t["name"]: t["outcome"] for t in result["tests"]}


def main():
    all_ok = True

    # 1. Each part's solution passes ALL tests up to and including its part.
    for n in (1, 2, 3):
        code = (SEED / f"part-{n}" / "solution.py").read_text(encoding="utf-8")
        result = runner.run_tests(SEED, code, part=n, mode="submit")
        ok = result["exit_code"] == 0 and all(
            o == "passed" for o in outcomes(result).values()
        )
        all_ok &= check(f"part-{n} solution green through part {n}", ok)

    # 2. Final solution passes EVERYTHING (the abstraction survived).
    final = (SEED / "part-3" / "solution.py").read_text(encoding="utf-8")
    result = runner.run_tests(SEED, final, part=3, mode="submit")
    all_ok &= check(
        "part-3 solution green on all parts",
        all(o == "passed" for o in outcomes(result).values()),
    )

    # 3. Starter passes both part-1 samples but fails the part-1 trap.
    starter = (SEED / "part-1" / "starter.py").read_text(encoding="utf-8")
    result = runner.run_tests(SEED, starter, part=1, mode="submit")
    out = outcomes(result)
    all_ok &= check(
        "starter passes samples",
        out["test_payment_clears_oldest_installment"] == "passed"
        and out["test_zero_payment_changes_nothing"] == "passed",
    )
    all_ok &= check(
        "starter FAILS float-precision trap",
        out["test_dime_installments_leave_exact_zero"] == "failed",
    )
    trap = [t for t in result["tests"] if t["name"] == "test_dime_installments_leave_exact_zero"][0]
    all_ok &= check("trap carries its label", trap["trap"] == "float-precision")

    # 4. A float-based part-2 attempt trips the remainder-distribution traps.
    float_v2 = '''
def allocate_payment(installments, payment):
    balances = []
    for item in installments:
        pay = min(item["due"], payment)
        payment = payment - pay
        balances.append({"id": item["id"], "remaining": item["due"] - pay})
    return {"balances": balances, "credit": payment}
'''
    result = runner.run_tests(SEED, float_v2, part=2, mode="submit")
    out = outcomes(result)
    all_ok &= check(
        "float part-2 impl FAILS credit-exactness trap",
        out["test_credit_is_exact_after_cascading"] == "failed",
    )
    all_ok &= check(
        "float part-2 impl FAILS boundary-balance trap",
        out["test_boundary_installment_balance_is_exact"] == "failed",
    )

    # 5. A float-based part-3 attempt trips the fee-split trap.
    float_v3 = '''
def allocate_payment(installments, payment):
    balances = []
    for item in installments:
        fee = item.get("fee", 0.0)
        principal = item.get("principal", item.get("due", 0.0))
        fee_paid = min(fee, payment)
        payment -= fee_paid
        pr_paid = min(principal, payment)
        payment -= pr_paid
        balances.append({
            "id": item["id"],
            "fee_remaining": fee - fee_paid,
            "principal_remaining": principal - pr_paid,
            "remaining": (fee - fee_paid) + (principal - pr_paid),
        })
    return {"balances": balances, "credit": payment}
'''
    result = runner.run_tests(SEED, float_v3, part=3, mode="submit")
    out = outcomes(result)
    all_ok &= check(
        "float part-3 impl FAILS fee-split trap",
        out["test_fee_principal_split_is_exact"] == "failed",
    )

    print("\nALL CHECKS PASSED" if all_ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the verification script**

Run: `cd backend && .venv/Scripts/python tests/verify_seed.py`
Expected: every line `PASS`, final line `ALL CHECKS PASSED`, exit 0.

If any trap check FAILS with "passed" (i.e., the float code accidentally
produces exact results on this platform), adjust that trap's dollar amounts
until the drift reproduces, and re-run. The chosen values (0.10/0.20/0.30
chains) are known-bad in IEEE-754 double math, so this should not trigger.

- [ ] **Step 7: Full-suite check + manual smoke**

Run: `cd backend && .venv/Scripts/python -m pytest -q` — still green.

With `npm run dev`: open the Affirm problem, submit the part-1 starter
unchanged → the trap fails and shows its `float-precision` label. That's the
core loop of the whole platform, seen end to end.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: seed problem affirm-payment-allocator with float-precision traps"
```

---

### Task 11: End-to-end verification + README truth check

**Files:**
- Modify: `README.md` (only if verification reveals it's wrong)

- [ ] **Step 1: Clean-clone simulation**

```bash
git status --porcelain   # must be empty (everything committed)
rm -rf backend/.venv node_modules frontend/node_modules
npm run setup
```

Expected: setup completes with no manual intervention.

- [ ] **Step 2: Full test suites**

```bash
npm run test:api
npm run test:web
cd backend && .venv/Scripts/python tests/verify_seed.py
```

Expected: all green.

- [ ] **Step 3: Full manual pass on the seed problem**

`npm run dev`, clear localStorage, then play the Affirm problem for real:

1. Part 1: starter → Run (samples pass) → Submit → trap fails with label. Fix with cents → Submit → unlock panel.
2. Part 2: code carries forward; extend for credit → Submit; check regression banner by deliberately breaking part-1 shape once.
3. Part 3: fees; verify legacy-shape test passes; finish → "All parts complete".
4. Check `sessions/affirm-payment-allocator/`: submit logs with traps_failed populated from the failed submit, keystroke snapshots present.
5. Timer read `~X:XX / 60:00 · Part N: …` throughout, amber/red never blocked anything.

- [ ] **Step 4: Final commit + push**

```bash
git add -A
git commit -m "chore: final verification pass"   # only if anything changed
git push origin main
```

---

## Execution notes

- Tasks 1–4 are backend-only and independent of 5–6 up front; but execute in
  order — later backend tasks modify files earlier ones create.
- Task 7 is the ship point the spec demands: a working single-part harness
  before any gating work starts.
- The manual verification steps in Tasks 7–9 are not optional; UI wiring has
  no automated coverage by design (logic is unit-tested, wiring is eyeballed).
- If `npm create vite` scaffolding differs from what Task 7 expects (file
  names, strict mode), adapt — the components given here are the contract,
  the scaffold is incidental.
