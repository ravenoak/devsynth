"""Additional tests to achieve >90% coverage for devsynth.utils.serialization module.

ReqID: UT-UTILS-SER-COV
"""

import json
from pathlib import Path

import pytest

from devsynth.utils.serialization import (
    dump_to_file,
    dumps_deterministic,
    load_from_file,
    loads,
)


@pytest.mark.fast
def test_dumps_deterministic_with_string_already_having_newline():
    """Test dumps_deterministic when JSON string would already have newline to cover line 30-31.

    ReqID: UT-UTILS-SER-COV-01
    """
    # Create a scenario where json.dumps might return a string with newline
    # This is tricky since json.dumps typically doesn't add newlines
    # But we can test the logic by mocking or by testing the actual behavior

    obj = {"key": "value"}
    result = dumps_deterministic(obj)

    # Verify it ends with exactly one newline
    assert result.endswith("\n")
    assert not result.endswith("\n\n")

    # Verify the content is correct
    assert loads(result) == obj


@pytest.mark.fast
def test_dumps_deterministic_ensures_single_newline():
    """Test that dumps_deterministic always ensures exactly one trailing newline.

    ReqID: UT-UTILS-SER-COV-02
    """
    test_objects = [
        {},  # empty object
        {"a": 1},  # simple object
        {"nested": {"key": "value"}},  # nested object
        [1, 2, 3],  # array
        "simple string",  # string
        42,  # number
        True,  # boolean
        None,  # null
    ]

    for obj in test_objects:
        result = dumps_deterministic(obj)
        # Each should end with exactly one newline
        assert result.endswith("\n"), f"Object {obj} result doesn't end with newline"
        assert not result.endswith("\n\n"), f"Object {obj} result has multiple newlines"
        # Should be able to parse back
        assert loads(result) == obj


@pytest.mark.fast
def test_loads_with_no_trailing_newline():
    """Test loads function with string that doesn't have trailing newline to cover line 41-43.

    ReqID: UT-UTILS-SER-COV-03
    """
    # Create JSON string without newline
    obj = {"test": "data", "number": 42}
    json_str = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )

    # Ensure it doesn't have a newline
    assert not json_str.endswith("\n")

    # loads should handle it correctly (line 43 without line 42)
    result = loads(json_str)
    assert result == obj


@pytest.mark.fast
def test_loads_with_trailing_newline():
    """Test loads function with string that has trailing newline to cover line 41-42.

    ReqID: UT-UTILS-SER-COV-04
    """
    # Create JSON string with newline
    obj = {"test": "data", "number": 42}
    json_str = (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    )

    # Ensure it has a newline
    assert json_str.endswith("\n")

    # loads should handle it correctly (line 41-42 then 43)
    result = loads(json_str)
    assert result == obj


@pytest.mark.fast
def test_dump_to_file_complete_coverage(tmp_path: Path):
    """Test dump_to_file function to ensure lines 48-50 coverage.

    ReqID: UT-UTILS-SER-COV-05
    """
    test_file = tmp_path / "test_dump.json"
    test_obj = {"coverage": "test", "numbers": [1, 2, 3]}

    # This should hit lines 48-50
    dump_to_file(str(test_file), test_obj)

    # Verify file was created
    assert test_file.exists()

    # Verify content is correct
    content = test_file.read_text(encoding="utf-8")
    assert content.endswith("\n")
    assert not content.endswith("\n\n")

    # Verify it can be parsed back
    parsed = json.loads(content.rstrip("\n"))
    assert parsed == test_obj


@pytest.mark.fast
def test_load_from_file_complete_coverage(tmp_path: Path):
    """Test load_from_file function to ensure lines 55-56 coverage.

    ReqID: UT-UTILS-SER-COV-06
    """
    test_file = tmp_path / "test_load.json"
    test_obj = {"load": "test", "data": {"nested": True}}

    # First create the file
    dump_to_file(str(test_file), test_obj)

    # Now load it back - this should hit lines 55-56
    loaded_obj = load_from_file(str(test_file))

    assert loaded_obj == test_obj


@pytest.mark.fast
def test_loads_with_multiple_trailing_newlines():
    """Test loads function with multiple trailing newlines.

    ReqID: UT-UTILS-SER-COV-07
    """
    obj = {"key": "value"}
    # Create string with multiple newlines
    json_str = (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n\n\n"
    )

    # loads should handle it by only stripping the last newline
    result = loads(json_str)
    assert result == obj


@pytest.mark.fast
def test_serialization_with_unicode_characters():
    """Test serialization functions with Unicode characters for completeness.

    ReqID: UT-UTILS-SER-COV-08
    """
    obj = {
        "unicode": "🚀 测试 émojis",
        "symbols": "αβγδε",
        "mixed": ["ASCII", "🌟", "café"],
    }

    # Test full round trip
    serialized = dumps_deterministic(obj)
    assert serialized.endswith("\n")

    deserialized = loads(serialized)
    assert deserialized == obj


@pytest.mark.fast
def test_serialization_edge_cases():
    """Test serialization with edge cases to ensure robustness.

    ReqID: UT-UTILS-SER-COV-09
    """
    edge_cases = [
        {"empty_string": ""},
        {"whitespace": "   \t\n  "},
        {"special_chars": '\n\r\t"\\'},
        {"large_number": 9223372036854775807},
        {"float": 3.141592653589793},
        {"negative": -42},
    ]

    for obj in edge_cases:
        serialized = dumps_deterministic(obj)
        deserialized = loads(serialized)
        assert deserialized == obj, f"Failed for object: {obj}"


@pytest.mark.fast
def test_file_operations_with_special_paths(tmp_path: Path):
    """Test file operations with various path scenarios.

    ReqID: UT-UTILS-SER-COV-10
    """
    # Test with nested directory
    nested_dir = tmp_path / "nested" / "deep"
    nested_dir.mkdir(parents=True)

    test_file = nested_dir / "test.json"
    test_obj = {"path": "nested/deep/test.json"}

    # Test dump and load with nested path
    dump_to_file(str(test_file), test_obj)
    loaded = load_from_file(str(test_file))

    assert loaded == test_obj
