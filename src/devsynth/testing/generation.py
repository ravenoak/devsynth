"""Integration test scaffolding utilities.

This module provides helpers for creating placeholder integration test
modules. The generated tests include failing assertions so missing
coverage is obvious during review.
"""

from __future__ import annotations

from typing import Dict, Iterable

PLACEHOLDER_TEMPLATE = (
    '"""Placeholder integration test for {name}."""\n\n'
    "def test_{name}():\n"
    '    """TODO: implement integration test for {name}."""\n'
    '    assert False, "Integration test not yet implemented"\n'
)


def scaffold_integration_tests(names: Iterable[str]) -> Dict[str, str]:
    """Create placeholder integration test modules.

    Args:
        names: Iterable of base names for the tests.

    Returns:
        Mapping of filenames to placeholder test content.
    """
    placeholders: Dict[str, str] = {}
    sanitized = list(names) or ["placeholder"]
    for raw in sanitized:
        name = raw.strip().lower().replace(" ", "_")
        filename = f"test_{name}.py"
        placeholders[filename] = PLACEHOLDER_TEMPLATE.format(name=name)
    return placeholders
