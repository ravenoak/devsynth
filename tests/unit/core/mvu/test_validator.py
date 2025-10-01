from __future__ import annotations

import json

import pytest

from devsynth.core.mvu.models import MVUU
from devsynth.core.mvu.validator import validate_affected_files, validate_commit_message

pytestmark = [pytest.mark.fast]


def _sample_data() -> dict:
    return {
        "utility_statement": "do something",
        "affected_files": ["a.py"],
        "tests": ["test_a.py"],
        "TraceID": "DSY-0001",
        "mvuu": True,
        "issue": "ISSUE-1",
    }


def _sample_commit() -> str:
    payload = json.dumps(_sample_data(), indent=2)
    return f"feat: add feature\n\n```json\n{payload}\n```"


def test_validate_commit_message_accepts_valid() -> None:
    msg = _sample_commit()
    mvuu = validate_commit_message(msg)
    assert mvuu.TraceID == "DSY-0001"


def test_validate_commit_message_rejects_bad_header() -> None:
    bad = "bad header\n\n```json\n{}\n```"
    with pytest.raises(ValueError):
        validate_commit_message(bad)


def test_validate_affected_files_reports_mismatches() -> None:
    mvuu = MVUU(**_sample_data())
    errors = validate_affected_files(mvuu, ["b.py"])
    assert errors
    assert "missing files" in errors[0] or "extra files" in errors[0]
