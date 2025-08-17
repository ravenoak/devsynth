import pytest

from devsynth.simple_addition import add


@pytest.mark.fast
def test_add_returns_sum():
    """Add returns the arithmetic sum of two numbers."""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
