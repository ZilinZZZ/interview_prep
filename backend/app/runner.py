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
        args = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-s",
            "--tb=short",
            "-p",
            "no:cacheprovider",
        ]
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
