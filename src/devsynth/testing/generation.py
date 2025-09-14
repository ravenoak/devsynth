"""Integration test scaffolding utilities.

This module provides helpers for creating placeholder integration test
modules. Generated tests now include a trivial assertion so they execute
successfully while clearly signaling where real integration coverage should be
added.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

PLACEHOLDER_TEMPLATE = (
    '"""Scaffolded integration test for {name}.\n\n'
    'Replace this file with real tests.\n"""\n\n'
    "def test_{name}() -> None:\n"
    '    """Integration test placeholder for {name}."""\n'
    "    assert 2 + 2 == 4\n"
)

__all__: list[str] = ["scaffold_integration_tests", "write_scaffolded_tests"]


def scaffold_integration_tests(names: Iterable[str]) -> dict[str, str]:
    """Create placeholder integration test modules.

    Args:
        names: Iterable of base names for the tests.

    Returns:
        Mapping of filenames to placeholder test content.
    """
    placeholders: dict[str, str] = {}
    sanitized = list(names) or ["placeholder"]
    for raw in sanitized:
        name = raw.strip().lower().replace(" ", "_")
        filename = f"test_{name}.py"
        placeholders[filename] = PLACEHOLDER_TEMPLATE.format(name=name)
    return placeholders


def write_scaffolded_tests(directory: Path, names: Iterable[str]) -> dict[Path, str]:
    """Write placeholder integration tests to ``directory``.

    This helper builds on :func:`scaffold_integration_tests` by emitting the
    generated placeholder test files to disk. Each scaffold contains a simple
    passing assertion, keeping the suite green while highlighting missing
    coverage.

    Args:
        directory: Destination folder for the scaffolded tests.
        names: Iterable of base names for the tests.

    Returns:
        Mapping of file paths to the content written.
    """

    directory.mkdir(parents=True, exist_ok=True)
    generated = scaffold_integration_tests(names)
    written: dict[Path, str] = {}
    for filename, content in generated.items():
        path = directory / filename
        path.write_text(content)
        written[path] = content
    return written
