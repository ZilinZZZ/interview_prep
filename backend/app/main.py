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
