import json
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
