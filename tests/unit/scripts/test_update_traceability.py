import json
import sys
from types import SimpleNamespace

import pytest

sys.path.append("scripts")

from update_traceability import update_traceability  # type: ignore


def _fake_run_factory(message: str, commit: str, timestamp: str):
    def _fake_run(cmd, check, capture_output=True, text=True):
        if cmd[:2] == ["git", "log"]:
            return SimpleNamespace(stdout=message)
        if cmd[:2] == ["git", "rev-parse"]:
            return SimpleNamespace(stdout=f"{commit}\n")
        if cmd[:3] == ["git", "show", "-s"]:
            return SimpleNamespace(stdout=f"{timestamp}\n")
        raise AssertionError(f"Unexpected command: {cmd}")

    return _fake_run


def test_update_traceability_writes_commit_and_timestamp(tmp_path, monkeypatch):
    trace_file = tmp_path / "traceability.json"
    issues_dir = tmp_path / "issues"
    issues_dir.mkdir()
    (issues_dir / "5.md").write_text("issue")

    message = (
        "feat: example\n\n"
        "```json\n"
        "{\n"
        '  "utility_statement": "Example",\n'
        '  "affected_files": ["file.txt"],\n'
        '  "tests": ["pytest"],\n'
        '  "TraceID": "DSY-0005",\n'
        '  "mvuu": true,\n'
        '  "issue": "#5",\n'
        '  "notes": "note"\n'
        "}\n"
        "```\n"
    )
    monkeypatch.setattr(
        "subprocess.run",
        _fake_run_factory(message, "deadbeef", "2025-01-01T00:00:00+00:00"),
    )

    update_traceability(trace_file, "HEAD")

    data = json.loads(trace_file.read_text())
    entry = data["DSY-0005"]
    assert entry["commit"] == "deadbeef"
    assert entry["timestamp"] == "2025-01-01T00:00:00+00:00"
    assert entry["mvuu"] is True
    assert entry["notes"] == "note"


def test_update_traceability_unknown_issue(tmp_path, monkeypatch):
    trace_file = tmp_path / "traceability.json"
    message = (
        "feat: example\n\n"
        "```json\n"
        "{\n"
        '  "utility_statement": "Example",\n'
        '  "affected_files": ["file.txt"],\n'
        '  "tests": ["pytest"],\n'
        '  "TraceID": "DSY-0006",\n'
        '  "mvuu": true,\n'
        '  "issue": "#6"\n'
        "}\n"
        "```\n"
    )
    monkeypatch.setattr(
        "subprocess.run",
        _fake_run_factory(message, "feedface", "2025-01-01T00:00:00+00:00"),
    )
    with pytest.raises(ValueError):
        update_traceability(trace_file, "HEAD")
