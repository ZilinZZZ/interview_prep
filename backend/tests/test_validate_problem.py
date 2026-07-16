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
