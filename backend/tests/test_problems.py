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


def test_list_problems_skips_misnamed_dir(tmp_path):
    good = tmp_path / "valid-problem"
    good.mkdir()
    (good / "meta.yaml").write_text(
        "id: valid-problem\ntitle: Valid Problem\ncompany: TestCo\n"
        "round: practical-coding\nlanguage: python\ntime_limit_min: 30\n"
        "part_budgets_min: [10]\ntags: [demo]\n",
        encoding="utf-8",
    )

    bad = tmp_path / "Bad Name"
    bad.mkdir()
    (bad / "meta.yaml").write_text(
        "id: bad-name\ntitle: Bad Name\ncompany: TestCo\n"
        "round: practical-coding\nlanguage: python\ntime_limit_min: 30\n"
        "part_budgets_min: [10]\ntags: [demo]\n",
        encoding="utf-8",
    )

    result = problems.list_problems(tmp_path)
    assert len(result) == 1
    assert result[0]["id"] == "valid-problem"


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
