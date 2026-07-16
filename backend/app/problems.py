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
