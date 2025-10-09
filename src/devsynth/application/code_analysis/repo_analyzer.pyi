"""Type hints for devsynth.application.code_analysis.repo_analyzer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class RepositoryAnalysis:
    """Structured result produced by :class:`RepoAnalyzer`."""

    dependencies: dict[str, list[str]]
    structure: dict[str, list[str]]

class RepoAnalyzer:
    """Analyze repository structure and dependencies."""

    root_path: Path

    def __init__(self, root_path: str) -> None: ...
    def analyze(self) -> RepositoryAnalysis: ...
    def _map_dependencies(self) -> dict[str, list[str]]: ...
    def _build_structure(self) -> dict[str, list[str]]: ...
    def _find_python_files(self) -> list[Path]: ...
    def _parse_imports(self, file_path: Path) -> set[str]: ...
