"""Shared fixtures for CLI unit tests."""

from __future__ import annotations

import pytest
from rich.console import Console


@pytest.fixture
def rich_console() -> Console:
    """Return a Rich console configured for capturing output in tests."""

    return Console(record=True, width=120)
