import json

import pytest

from scripts import verify_release_state as vrs


@pytest.mark.fast
def test_fails_when_unresolved_questions(tmp_path, monkeypatch):
    """ReqID: dialectical_audit_gating-1"""
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
    log = tmp_path / "dialectical_audit.log"
    log.write_text(
        json.dumps({"questions": ["Unresolved"], "resolved": []}), encoding="utf-8"
    )
    monkeypatch.setattr(vrs, "LOG_PATH", log)
    assert vrs.main() == 1


@pytest.mark.fast
def test_succeeds_when_no_questions(tmp_path, monkeypatch):
    """ReqID: dialectical_audit_gating-2"""
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
    log = tmp_path / "dialectical_audit.log"
    log.write_text(
        json.dumps({"questions": [], "resolved": ["done"]}), encoding="utf-8"
    )
    monkeypatch.setattr(vrs, "LOG_PATH", log)
    assert vrs.main() == 0
