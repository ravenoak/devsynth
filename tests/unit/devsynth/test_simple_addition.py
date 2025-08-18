import pytest

from devsynth.simple_addition import add

pytestmark = pytest.mark.fast


def test_add_returns_sum():
    """Add returns the arithmetic sum of two numbers."""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0


def test_add_raises_type_error_on_non_numeric():
    """Non-numeric inputs raise a TypeError."""
    with pytest.raises(TypeError):
        add("1", 2)
