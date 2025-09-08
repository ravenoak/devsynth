import pathlib

import pytest

from scripts import verify_issue_references


@pytest.mark.fast
def test_scan_file_reports_missing_issue(tmp_path, monkeypatch):
    """Report missing issue reference.
    Issue: issues/reqid_traceability_gap.md ReqID: FR-03"""
    path = tmp_path / "test_missing_issue.py"
    path.write_text(
        "def test_sample():\n" '    """No issue here. ReqID: FR-99"""\n' "    pass\n"
    )
    monkeypatch.chdir(pathlib.Path(__file__).resolve().parent.parent)
    missing = verify_issue_references.scan_file(path)
    assert missing == [("test_sample", "Missing Issue reference in docstring")]


@pytest.mark.fast
def test_scan_file_accepts_valid_issue(tmp_path, monkeypatch):
    """Accept docstrings with issue and ReqID.
    Issue: issues/reqid_traceability_gap.md ReqID: FR-04"""
    path = tmp_path / "test_good_issue.py"
    path.write_text(
        "def test_sample():\n"
        '    """Doc. Issue: issues/reqid_traceability_gap.md ReqID: FR-98"""\n'
        "    pass\n"
    )
    monkeypatch.chdir(pathlib.Path(__file__).resolve().parent.parent)
    missing = verify_issue_references.scan_file(path)
    assert missing == []
