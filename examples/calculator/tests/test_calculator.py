import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from calculator import Calculator

pytestmark = [pytest.mark.fast]


def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5


def test_subtract():
    calc = Calculator()
    assert calc.subtract(5, 2) == 3


def test_multiply():
    calc = Calculator()
    assert calc.multiply(4, 3) == 12


def test_divide():
    calc = Calculator()
    assert calc.divide(10, 2) == 5


def test_divide_by_zero():
    calc = Calculator()
    with pytest.raises(ZeroDivisionError):
        calc.divide(1, 0)
