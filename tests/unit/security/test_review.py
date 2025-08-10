from datetime import date

import pytest

from devsynth.security import is_review_due, next_review_date


def test_review_due_when_interval_elapsed():
    last = date(2024, 1, 1)
    assert is_review_due(last, today=date(2024, 3, 31))


def test_review_not_due_before_interval():
    last = date(2024, 1, 1)
    assert not is_review_due(last, today=date(2024, 2, 1))


def test_next_review_date_calculation():
    last = date(2024, 1, 1)
    assert next_review_date(last) == date(2024, 3, 31)
