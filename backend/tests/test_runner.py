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
