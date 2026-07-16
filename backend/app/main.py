from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import problems, runner, sessions

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
