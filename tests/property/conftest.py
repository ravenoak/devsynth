"""Pytest configuration for property-based tests.

This module gates the collection and execution of tests in this directory
behind the environment variable DEVSYNTH_PROPERTY_TESTING.

Rationale:
- Property-based tests can be expensive and occasionally flaky if run
  unintentionally in minimal CI jobs. We default to disabling them unless
  explicitly enabled by the contributor or CI job that intends to run them.

Enable by setting any of the following values:
- DEVSYNTH_PROPERTY_TESTING=1 | true | yes | on (case-insensitive)

This aligns with docs/guidelines to keep fast, stable CI by default while
still allowing full validation in scheduled or explicit runs.
"""

from __future__ import annotations

import os

import pytest

_TRUTHY = {"1", "true", "yes", "on"}


def _property_tests_enabled() -> bool:
    value = os.getenv("DEVSYNTH_PROPERTY_TESTING", "").strip().lower()
    return value in _TRUTHY


def pytest_ignore_collect(path, config):  # type: ignore[override]
    """Prevent collection of this directory when property tests are disabled.

    Using pytest_ignore_collect at the directory-level (via this conftest.py)
    ensures we avoid importing heavy dependencies (e.g., hypothesis) unless
    explicitly requested by the environment.
    """
    if not _property_tests_enabled():
        # Returning True tells pytest to ignore collection for this path
        return True
    return False


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Extra safety: if items are collected anyway, mark them skipped.

    This is a defensive layer in case a different collection path bypasses
    pytest_ignore_collect. It keeps behavior deterministic.
    """
    if _property_tests_enabled():
        return
    skip_marker = pytest.mark.skip(
        reason=(
            "Property tests are disabled by default. Set DEVSYNTH_PROPERTY_TESTING=1 "
            "(or true/yes/on) to enable."
        )
    )
    for item in items:
        item.add_marker(skip_marker)
