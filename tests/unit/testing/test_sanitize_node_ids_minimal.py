import pytest

from devsynth.testing.run_tests import _sanitize_node_ids


@pytest.mark.fast
def test_sanitize_node_ids_strips_line_when_no_function():
    raw = [
        "tests/unit/foo_test.py:17",
        "tests/unit/bar_test.py::TestClass::test_method",
        "tests/unit/foo_test.py:17",  # duplicate
    ]
    cleaned = _sanitize_node_ids(raw)
    # First entry should have :17 stripped because there is no '::'
    assert cleaned[0] == "tests/unit/foo_test.py"
    # Entry with function should be preserved as-is
    assert cleaned[1] == "tests/unit/bar_test.py::TestClass::test_method"
    # Duplicate should be removed, resulting length 2
    assert len(cleaned) == 2
