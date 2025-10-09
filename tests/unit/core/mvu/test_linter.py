import pytest

from devsynth.core.mvu.linter import lint_commit_message

pytestmark = [pytest.mark.fast]

VALID_MESSAGE = (
    "feat: add example\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "DSY-0001",\n'
    '  "mvuu": true,\n'
    '  "issue": "#1",\n'
    '  "notes": "demo"\n'
    "}\n"
    "```\n"
)

INVALID_MESSAGE = "feat: missing block"

INVALID_TRACEID_MESSAGE = (
    "feat: bad trace\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "BAD-0001",\n'
    '  "mvuu": true,\n'
    '  "issue": "#1"\n'
    "}\n"
    "```\n"
)

MISSING_ISSUE_MESSAGE = (
    "feat: no issue\n\n"
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
    "feat: no mvuu\n\n"
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

MVUU_FALSE_MESSAGE = (
    "feat: mvuu false\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "DSY-0001",\n'
    '  "mvuu": false,\n'
    '  "issue": "#1"\n'
    "}\n"
    "```\n"
)


def test_lint_commit_message_valid():
    """Valid commit messages should produce no errors."""
    assert lint_commit_message(VALID_MESSAGE) == []


def test_lint_commit_message_missing_block():
    """Missing MVUU block should produce an error."""
    errors = lint_commit_message(INVALID_MESSAGE)
    assert any("Missing MVUU" in e for e in errors)


def test_lint_commit_message_bad_traceid():
    """Invalid TraceID pattern should produce an error."""
    errors = lint_commit_message(INVALID_TRACEID_MESSAGE)
    assert any("TraceID" in e for e in errors)


def test_lint_commit_message_missing_issue():
    """Missing issue field should produce an error."""
    errors = lint_commit_message(MISSING_ISSUE_MESSAGE)
    assert any("issue" in e for e in errors)


def test_lint_commit_message_mvuu_false():
    """mvuu field set to false should produce an error."""
    errors = lint_commit_message(MVUU_FALSE_MESSAGE)
    assert any("mvuu" in e for e in errors)


def test_lint_commit_message_missing_mvuu():
    """Missing mvuu field should produce an error."""
    errors = lint_commit_message(MISSING_MVUU_MESSAGE)
    assert any("mvuu" in e for e in errors)
