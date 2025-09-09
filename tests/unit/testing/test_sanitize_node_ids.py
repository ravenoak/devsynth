import pytest

from devsynth.testing.run_tests import _sanitize_node_ids


@pytest.mark.fast
def test_sanitize_node_ids_strips_line_numbers_without_function_selector():
    raw = [
        "tests/unit/pkg/test_mod.py:123",  # no ::, should strip :123
        "tests/unit/pkg/test_mod.py::TestClass::test_func:456",  # has ::, must keep :456
        "tests/unit/other/test_file.py:9",
        "tests/unit/pkg/test_mod.py",  # duplicate after stripping should dedupe
    ]
    cleaned = _sanitize_node_ids(raw)
    assert "tests/unit/pkg/test_mod.py" in cleaned
    assert "tests/unit/other/test_file.py" in cleaned
    # Ensure duplicate (after stripping) is removed
    assert cleaned.count("tests/unit/pkg/test_mod.py") == 1
    # Ensure function selector retains trailing :line if present after ::
    assert "tests/unit/pkg/test_mod.py::TestClass::test_func:456" in cleaned, cleaned


@pytest.mark.fast
def test_sanitize_node_ids_preserves_order():
    raw = [
        "tests/a.py:1",
        "tests/b.py:2",
        "tests/c.py::t::x:3",
    ]
    cleaned = _sanitize_node_ids(raw)
    assert cleaned == [
        "tests/a.py",
        "tests/b.py",
        "tests/c.py::t::x:3",
    ]
