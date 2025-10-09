"""Final coverage tests to reach >90% for devsynth.utils.serialization module.

ReqID: UT-UTILS-SER-FINAL
"""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from devsynth.utils.serialization import (
    dump_to_file,
    dumps_deterministic,
    load_from_file,
    loads,
)


@pytest.mark.fast
def test_dumps_deterministic_direct_line_coverage():
    """Test dumps_deterministic to ensure lines 28-32 are covered.

    ReqID: UT-UTILS-SER-FINAL-01
    """
    # Test simple object - should hit line 28
    obj = {"key": "value"}
    result = dumps_deterministic(obj)

    # Verify line 28 (json.dumps call) was executed
    assert isinstance(result, str)

    # Verify lines 30-32 (newline logic) were executed
    assert result.endswith("\n")

    # Test that the result can be parsed back
    parsed = json.loads(result.rstrip("\n"))
    assert parsed == obj


@pytest.mark.fast
def test_dumps_deterministic_with_string_that_might_have_newline():
    """Test dumps_deterministic with edge case to ensure line 30-31 coverage.

    ReqID: UT-UTILS-SER-FINAL-02
    """
    # Test with object that might produce a string with newline
    obj = {"multiline": "line1\nline2"}
    result = dumps_deterministic(obj)

    # Should always end with exactly one newline (lines 30-31)
    assert result.endswith("\n")
    assert not result.endswith("\n\n")

    # Verify the content is correct
    parsed = loads(result)
    assert parsed == obj


@pytest.mark.fast
def test_loads_direct_line_coverage():
    """Test loads function to ensure lines 41-43 are covered.

    ReqID: UT-UTILS-SER-FINAL-03
    """
    obj = {"test": "data"}

    # Test with string that has newline - should hit lines 41-42
    json_with_newline = json.dumps(obj) + "\n"
    result = loads(json_with_newline)
    assert result == obj

    # Test with string that doesn't have newline - should skip line 42, hit line 43
    json_without_newline = json.dumps(obj)
    result = loads(json_without_newline)
    assert result == obj


@pytest.mark.fast
def test_dump_to_file_direct_line_coverage(tmp_path: Path):
    """Test dump_to_file to ensure lines 48-50 are covered.

    ReqID: UT-UTILS-SER-FINAL-04
    """
    test_file = tmp_path / "test.json"
    test_obj = {"file": "test"}

    # Call dump_to_file - should hit lines 48-50
    dump_to_file(str(test_file), test_obj)

    # Verify the file was created and has correct content
    assert test_file.exists()
    content = test_file.read_text(encoding="utf-8")
    assert content.endswith("\n")

    # Verify content can be parsed back
    parsed = json.loads(content.rstrip("\n"))
    assert parsed == test_obj


@pytest.mark.fast
def test_load_from_file_direct_line_coverage(tmp_path: Path):
    """Test load_from_file to ensure lines 55-56 are covered.

    ReqID: UT-UTILS-SER-FINAL-05
    """
    test_file = tmp_path / "load_test.json"
    test_obj = {"load": "test"}

    # First create the file
    dump_to_file(str(test_file), test_obj)

    # Call load_from_file - should hit lines 55-56
    result = load_from_file(str(test_file))

    assert result == test_obj


@pytest.mark.fast
def test_serialization_functions_with_mock_to_ensure_coverage():
    """Test serialization functions with mocking to ensure all lines are hit.

    ReqID: UT-UTILS-SER-FINAL-06
    """
    test_obj = {"mock": "test"}

    # Test dumps_deterministic with mock to ensure line coverage
    with patch("json.dumps") as mock_dumps:
        mock_dumps.return_value = '{"mock":"test"}'  # No newline
        result = dumps_deterministic(test_obj)

        # Should have added newline (line 31)
        assert result == '{"mock":"test"}\n'
        mock_dumps.assert_called_once_with(
            test_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )


@pytest.mark.fast
def test_loads_with_various_newline_scenarios():
    """Test loads with different newline scenarios to ensure complete coverage.

    ReqID: UT-UTILS-SER-FINAL-07
    """
    obj = {"newline": "test"}
    base_json = json.dumps(obj)

    # Test with no newline (should skip lines 41-42)
    result = loads(base_json)
    assert result == obj

    # Test with single newline (should hit lines 41-42)
    result = loads(base_json + "\n")
    assert result == obj

    # Test with multiple newlines (should hit lines 41-42, strip only last one)
    result = loads(base_json + "\n\n\n")
    assert result == obj


@pytest.mark.fast
def test_file_operations_with_explicit_paths():
    """Test file operations with explicit path handling to ensure coverage.

    ReqID: UT-UTILS-SER-FINAL-08
    """
    import os
    import tempfile

    # Use explicit file operations to ensure lines are covered
    test_obj = {"explicit": "path", "test": True}

    # Create a temporary file path
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name

    try:
        # Test dump_to_file with explicit path
        dump_to_file(temp_path, test_obj)

        # Verify file exists and has content
        assert os.path.exists(temp_path)

        # Test load_from_file with explicit path
        loaded_obj = load_from_file(temp_path)
        assert loaded_obj == test_obj

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.fast
def test_dumps_deterministic_return_path():
    """Test dumps_deterministic return path to ensure line 32 is covered.

    ReqID: UT-UTILS-SER-FINAL-09
    """
    # Test with various objects to ensure line 32 (return s) is always hit
    test_objects = [
        {},
        {"a": 1},
        [1, 2, 3],
        "string",
        42,
        True,
        None,
    ]

    for obj in test_objects:
        result = dumps_deterministic(obj)
        # Every call should return a string (line 32)
        assert isinstance(result, str)
        assert result.endswith("\n")
        # Should be able to parse back
        assert loads(result) == obj


@pytest.mark.fast
def test_loads_return_path():
    """Test loads return path to ensure line 43 is covered.

    ReqID: UT-UTILS-SER-FINAL-10
    """
    # Test various JSON strings to ensure line 43 (return json.loads(s)) is hit
    test_cases = [
        ("{}", {}),
        ('{"a":1}', {"a": 1}),
        ("[1,2,3]", [1, 2, 3]),
        ('"string"', "string"),
        ("42", 42),
        ("true", True),
        ("null", None),
    ]

    for json_str, expected in test_cases:
        # Test without newline
        result = loads(json_str)
        assert result == expected

        # Test with newline
        result = loads(json_str + "\n")
        assert result == expected
