"""Sample integration test for DevSynth projects."""

import pytest

pytestmark = [pytest.mark.fast]


def add(a: int, b: int) -> int:
    """Return the sum of two numbers."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Return the product of two numbers."""
    return a * b


def test_workflow():
    """Combine simple operations in a workflow."""
    total = add(2, 3)
    product = multiply(total, 4)
    assert product == 20
