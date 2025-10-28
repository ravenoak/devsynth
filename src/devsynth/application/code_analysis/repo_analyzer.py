"""Repository analyzer for mapping dependencies and structure.

This module provides a lightweight utility for examining a Python project
directory.  It walks the file tree, builds a simple representation of the
directory structure, and parses Python files to determine their import
dependencies.  The intent is to give a quick overview of how modules relate to
one another without requiring a full build or runtime environment.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass(slots=True)
class RepositoryAnalysis:
    """Structured result produced by :class:`RepoAnalyzer`."""

    dependencies: dict[str, list[str]]
    structure: dict[str, list[str]]


class RepoAnalyzer:
    """Analyze repository structure and dependencies.

    The analyzer focuses on Python source files.  It recursively searches the
    provided root directory for ``.py`` files, extracts their import statements
    and records a basic directory structure.  The resulting data can be used to
    understand how modules are organised and which top level dependencies each
    file relies on.
    """

    def __init__(self, root_path: str) -> None:
        """Initialise the analyzer.

        Args:
            root_path: Path to the repository root that should be analysed.
        """

        # ``os`` and ``pathlib`` functions require matching path types on some
        # Python versions.  Converting to ``Path`` and resolving eagerly avoids
        # surprises when ``os.walk`` or ``os.path.relpath`` receive mixed
        # ``str``/``Path`` inputs, which became stricter in Python 3.12.
        self.root_path = Path(root_path).resolve()

    # ------------------------------------------------------------------
    def analyze(self) -> RepositoryAnalysis:
        """Run the analysis and return structure and dependency maps."""

        logger.debug("Starting repository analysis at %s", self.root_path)
        result = RepositoryAnalysis(
            dependencies=self._map_dependencies(),
            structure=self._build_structure(),
        )
        logger.debug("Finished repository analysis")
        return result

    # ------------------------------------------------------------------
    def _map_dependencies(self) -> dict[str, list[str]]:
        """Map Python file dependencies based on import statements."""

        dependencies: dict[str, list[str]] = {}
        for file_path in self._find_python_files():
            imports = self._parse_imports(file_path)
            rel_path = os.path.relpath(os.fspath(file_path), os.fspath(self.root_path))
            dependencies[rel_path] = sorted(imports)
            logger.debug("%s depends on %s", rel_path, dependencies[rel_path])
        return dependencies

    # ------------------------------------------------------------------
    def _build_structure(self) -> dict[str, list[str]]:
        """Build a simple representation of the directory structure."""

        structure: dict[str, list[str]] = {}
        root_str = os.fspath(self.root_path)
        for dirpath, dirnames, filenames in os.walk(root_str):
            rel = os.path.relpath(dirpath, root_str)
            structure[rel] = sorted(dirnames + filenames)
            logger.debug("Indexed directory %s: %s", rel, structure[rel])
        return structure

    # ------------------------------------------------------------------
    def _find_python_files(self) -> list[Path]:
        """Return a list of all Python files under the root path."""

        files: list[Path] = []
        root_str = os.fspath(self.root_path)
        for dirpath, _, filenames in os.walk(root_str):
            for name in filenames:
                if name.endswith(".py"):
                    files.append(Path(dirpath) / name)
        return files

    # ------------------------------------------------------------------
    def _parse_imports(self, file_path: Path) -> set[str]:
        """Parse import statements from a Python file.

        Only the top level module name is recorded for each import.
        """

        imports: set[str] = set()
        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
                    else:
                        for alias in node.names:
                            imports.add(alias.name.split(".")[0])
        except (OSError, SyntaxError) as exc:  # pragma: no cover - logging
            logger.debug("Failed to parse %s: %s", file_path, exc)

        return imports


__all__ = ["RepoAnalyzer", "RepositoryAnalysis"]
