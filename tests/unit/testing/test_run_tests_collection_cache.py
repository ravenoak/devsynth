import pytest

from devsynth.testing.run_tests import _sanitize_node_ids

pytestmark = [pytest.mark.fast]


def test_sanitize_node_ids_strips_trailing_line_without_function_delimiter():
    """ReqID: SANITIZE-1"""
    ids = [
        "tests/unit/foo_test.py:123",  # should strip :123
        "tests/unit/bar_test.py::test_case:45",  # has ::, should keep :45
        "tests/unit/baz_test.py",  # unchanged
    ]
    out = _sanitize_node_ids(ids)
    assert "tests/unit/foo_test.py" in out
    assert "tests/unit/bar_test.py::test_case:45" in out
    assert "tests/unit/baz_test.py" in out
    assert all(
        s != "tests/unit/foo_test.py:123" for s in out
    ), "line suffix should be stripped when no :: present"
