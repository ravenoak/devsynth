import sys

sys.path.append("scripts")

from commit_linter import lint_commit_message  # type: ignore

VALID_MESSAGE = (
    "feat: add example\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "MVUU-0001"\n'
    "}\n"
    "```\n"
)

INVALID_MESSAGE = "feat: missing block"


def test_lint_commit_message_valid():
    """Valid commit messages should produce no errors."""
    assert lint_commit_message(VALID_MESSAGE) == []


def test_lint_commit_message_missing_block():
    """Missing MVUU block should produce an error."""
    errors = lint_commit_message(INVALID_MESSAGE)
    assert any("Missing MVUU" in e for e in errors)
