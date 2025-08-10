"""Utilities for scheduling periodic security reviews."""

from __future__ import annotations

from datetime import date, timedelta

DEFAULT_INTERVAL_DAYS = 90


def next_review_date(
    last_review: date, interval_days: int = DEFAULT_INTERVAL_DAYS
) -> date:
    """Return the next scheduled review date.

    Parameters
    ----------
    last_review:
        Date when the last review occurred.
    interval_days:
        Number of days between reviews. Defaults to ``90``.
    """
    return last_review + timedelta(days=interval_days)


def is_review_due(
    last_review: date,
    *,
    today: date | None = None,
    interval_days: int = DEFAULT_INTERVAL_DAYS,
) -> bool:
    """Check whether a security review is due.

    Parameters
    ----------
    last_review:
        Date of the previous review.
    today:
        Reference date. Defaults to ``date.today()``.
    interval_days:
        Review interval in days. Defaults to ``90``.
    """
    if today is None:
        today = date.today()
    return today >= next_review_date(last_review, interval_days)
