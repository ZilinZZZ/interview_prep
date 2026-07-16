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
