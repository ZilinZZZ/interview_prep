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
