"""Validate a problem folder: structure, meta, test markers, and behavior.

Usage: python scripts/validate_problem.py <problem-id> [--problems-dir DIR]

Exit 0 if valid; exit 1 with a readable list of every failed check.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "backend"))

from app.runner import run_tests  # noqa: E402

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
