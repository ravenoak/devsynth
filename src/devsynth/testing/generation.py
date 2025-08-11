"""Integration test scaffolding utilities.

This module provides helpers for creating placeholder integration test
modules. Generated tests include ``pytest`` skip markers so missing
coverage is highlighted during review without breaking the suite.
"""

from __future__ import annotations

from pathlib import Path
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

__all__ = ["scaffold_integration_tests", "write_scaffolded_tests"]


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


def write_scaffolded_tests(directory: Path, names: Iterable[str]) -> Dict[Path, str]:
    """Write placeholder integration tests to ``directory``.

    This helper builds on :func:`scaffold_integration_tests` by emitting the
    generated placeholder test files to disk. Each file is created with a
    ``pytest.mark.skip`` marker so the suite remains green until the
    placeholder is replaced.

    Args:
        directory: Destination folder for the scaffolded tests.
        names: Iterable of base names for the tests.

    Returns:
        Mapping of file paths to the content written.
    """

    directory.mkdir(parents=True, exist_ok=True)
    generated = scaffold_integration_tests(names)
    written: Dict[Path, str] = {}
    for filename, content in generated.items():
        path = directory / filename
        path.write_text(content)
        written[path] = content
    return written
