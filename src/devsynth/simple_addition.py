"""Utility for a basic addition example."""

# Feature: Simple addition input validation

from numbers import Number


def add(a: Number, b: Number) -> Number:
    """Return the sum of two numbers after validating their types.

    Args:
        a: The first addend, expected to be numeric.
        b: The second addend, expected to be numeric.

    Returns:
        The arithmetic sum of ``a`` and ``b``.

    Raises:
        TypeError: If either ``a`` or ``b`` is not a numeric type.
    """

    if not isinstance(a, Number) or not isinstance(b, Number):
        raise TypeError("Both arguments must be numeric")
    return a + b
