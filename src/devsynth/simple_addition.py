"""Utility for a basic addition example.

Type hints are intentionally concrete (int|float) to satisfy strict mypy and
avoid `numbers.Number` arithmetic ambiguities.
"""

# Feature: Simple addition input validation

from typing import Union

Numeric = Union[int, float]


def add(a: Numeric, b: Numeric) -> float:
    """Return the sum of two numbers after validating their types.

    Args:
        a: The first addend, expected to be numeric (int or float).
        b: The second addend, expected to be numeric (int or float).

    Returns:
        The arithmetic sum of ``a`` and ``b`` as a float.

    Raises:
        TypeError: If either ``a`` or ``b`` is not a numeric type.
    """

    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numeric")  # pragma: no cover
    return float(a) + float(b)
