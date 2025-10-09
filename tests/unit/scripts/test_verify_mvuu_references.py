import sys

import pytest

pytestmark = [pytest.mark.fast]

sys.path.append("scripts")

from verify_mvuu_references import verify_mvuu_affected_files

VALID_MESSAGE = (
    "feat: example\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "DSY-0001",\n'
    '  "mvuu": true,\n'
    '  "issue": "#1"\n'
    "}\n"
    "```\n"
)

MISSING_ISSUE_MESSAGE = (
    "feat: example\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "DSY-0001",\n'
    '  "mvuu": true\n'
    "}\n"
    "```\n"
)

MISSING_MVUU_MESSAGE = (
    "feat: example\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "DSY-0001",\n'
    '  "issue": "#1"\n'
    "}\n"
    "```\n"
)


def test_verify_mvuu_affected_files_valid():
    """Changed files listed in MVUU JSON should yield no errors."""
    assert verify_mvuu_affected_files(VALID_MESSAGE, ["file.txt"]) == []


def test_verify_mvuu_affected_files_missing():
    """Missing affected file should produce an error."""
    errors = verify_mvuu_affected_files(VALID_MESSAGE, ["other.txt"])
    assert any("missing files" in e for e in errors)


def test_verify_mvuu_affected_files_missing_issue():
    """Missing issue field should produce an error."""
    errors = verify_mvuu_affected_files(MISSING_ISSUE_MESSAGE, ["file.txt"])
    assert any("issue" in e for e in errors)


def test_verify_mvuu_affected_files_missing_mvuu():
    """Missing mvuu flag should produce an error."""
    errors = verify_mvuu_affected_files(MISSING_MVUU_MESSAGE, ["file.txt"])
    assert any("mvuu" in e for e in errors)
