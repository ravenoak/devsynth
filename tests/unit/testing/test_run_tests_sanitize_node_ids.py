import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_sanitize_strips_trailing_line_numbers_without_function_sep() -> None:
    """ReqID: RT-05 — strip trailing :<digits> when no '::' present."""

    # No '::' present, so trailing :<digits> should be removed
    ids = [
        "tests/unit/test_mod.py:12",
        "tests/unit/test_mod_subdir/test_file.py:101",
    ]
    sanitized = rt._sanitize_node_ids(ids)
    assert sanitized == [
        "tests/unit/test_mod.py",
        "tests/unit/test_mod_subdir/test_file.py",
    ]


@pytest.mark.fast
def test_sanitize_keeps_ids_with_function_sep() -> None:
    """ReqID: RT-06 — keep IDs with '::' intact including any line refs."""

    # When '::' present, do not strip trailing line numbers
    ids = [
        "tests/unit/test_mod.py::TestClass::test_func",
        "tests/unit/test_other.py::test_func",
    ]
    sanitized = rt._sanitize_node_ids(ids)
    assert sanitized == ids


@pytest.mark.fast
def test_sanitize_deduplicates_preserving_order() -> None:
    """ReqID: RT-07 — de-duplicate normalized IDs preserving first occurrence order."""

    ids = [
        "tests/unit/test_a.py::t1",
        "tests/unit/test_b.py",
        # duplicate
        "tests/unit/test_a.py::t1",
        # duplicate path differing by line number; should normalize and dedupe
        "tests/unit/test_b.py:33",
    ]
    sanitized = rt._sanitize_node_ids(ids)
    # After normalization, duplicates should collapse preserving first occurrence
    assert sanitized == [
        "tests/unit/test_a.py::t1",
        "tests/unit/test_b.py",
    ]
