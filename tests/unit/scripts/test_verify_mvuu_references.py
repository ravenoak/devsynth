import sys

sys.path.append("scripts")

from verify_mvuu_references import verify_mvuu_affected_files

VALID_MESSAGE = (
    "feat: example\n\n"
    "```json\n"
    "{\n"
    '  "utility_statement": "Example",\n'
    '  "affected_files": ["file.txt"],\n'
    '  "tests": ["pytest tests/example.py"],\n'
    '  "TraceID": "MVUU-0001"\n'
    "}\n"
    "```\n"
)


def test_verify_mvuu_affected_files_valid():
    """Changed files listed in MVUU JSON should yield no errors."""
    assert verify_mvuu_affected_files(VALID_MESSAGE, ["file.txt"]) == []


def test_verify_mvuu_affected_files_missing():
    """Missing affected file should produce an error."""
    errors = verify_mvuu_affected_files(VALID_MESSAGE, ["other.txt"])
    assert any("missing entries" in e for e in errors)
