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
