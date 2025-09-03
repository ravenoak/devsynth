import pytest

from devsynth.simple_addition import add


@pytest.mark.fast
def test_add_returns_sum():
    """ReqID: DEMO-ADD-1 | Add returns the arithmetic sum of two numbers."""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0


@pytest.mark.fast
def test_add_raises_type_error_on_non_numeric():
    """ReqID: DEMO-ADD-2 | Non-numeric inputs raise a TypeError."""
    with pytest.raises(TypeError):
        add("1", 2)
