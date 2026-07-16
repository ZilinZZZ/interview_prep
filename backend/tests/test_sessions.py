import json

from app import sessions


def test_append_submit_log_creates_file(tmp_path):
    entry = {"problem_id": "demo-problem", "part": 1, "final_code": "x = 1"}
    path = sessions.append_submit_log(tmp_path, "demo-problem", entry)
    assert path.parent == tmp_path / "demo-problem"
    assert json.loads(path.read_text(encoding="utf-8")) == entry
    assert ":" not in path.name  # Windows-safe timestamp


def test_write_snapshot(tmp_path):
    path = sessions.write_snapshot(tmp_path, "demo-problem", "print('hi')")
    assert path.parent == tmp_path / "demo-problem" / "keystrokes"
    assert path.suffix == ".py"
    assert path.read_text(encoding="utf-8") == "print('hi')"


def test_append_submit_log_never_overwrites_on_same_stamp(tmp_path, monkeypatch):
    monkeypatch.setattr(sessions, "_stamp", lambda: "2026-07-15T12-00-00-000")
    first = sessions.append_submit_log(tmp_path, "demo-problem", {"n": 1})
    second = sessions.append_submit_log(tmp_path, "demo-problem", {"n": 2})
    assert first != second
    assert json.loads(first.read_text(encoding="utf-8")) == {"n": 1}
    assert json.loads(second.read_text(encoding="utf-8")) == {"n": 2}


def test_write_snapshot_never_overwrites_on_same_stamp(tmp_path, monkeypatch):
    monkeypatch.setattr(sessions, "_stamp", lambda: "2026-07-15T12-00-00-000")
    first = sessions.write_snapshot(tmp_path, "demo-problem", "a = 1")
    second = sessions.write_snapshot(tmp_path, "demo-problem", "a = 2")
    assert first != second
    assert first.read_text(encoding="utf-8") == "a = 1"
    assert second.read_text(encoding="utf-8") == "a = 2"
