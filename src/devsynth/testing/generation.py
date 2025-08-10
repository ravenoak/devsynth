"""Integration test scaffolding utilities.

This module provides helpers for creating placeholder integration test
modules. Generated tests include ``pytest`` skip markers so missing
coverage is highlighted during review without breaking the suite.
"""

from __future__ import annotations

from typing import Dict, Iterable

PLACEHOLDER_TEMPLATE = (
    '"""Scaffolded integration test for {name}.\n\n'
    'Replace this file with real tests and remove the skip marker.\n"""\n'
    "import pytest\n\n"
    'pytestmark = pytest.mark.skip(reason="scaffold placeholder for {name}")\n\n'
    "def test_{name}() -> None:\n"
    '    """Integration test placeholder for {name}."""\n'
    '    raise NotImplementedError("Add integration test for {name}")\n'
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
