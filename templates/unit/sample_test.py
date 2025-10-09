"""Sample unit test for DevSynth projects."""

import pytest

pytestmark = [pytest.mark.fast]


def add(a: int, b: int) -> int:
    """Return the sum of two numbers."""
    return a + b


def test_add():
    """Verify that ``add`` returns the correct sum."""
    assert add(2, 3) == 5
