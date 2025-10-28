from __future__ import annotations

"""High level interface for project state analysis.

This module exposes a convenience function ``analyze_project_state`` that wraps
:class:`ProjectStateAnalyzer` and returns a summary of a project's artifacts and
health.
"""

from typing import Any, Dict

from .project_state_analyzer import ProjectStateAnalyzer


def analyze_project_state(project_path: str) -> dict[str, Any]:
    """Analyze the state of a project located at ``project_path``.

    Args:
        project_path: Path to the project root.

    Returns:
        Dictionary describing the project. Keys include:

        ``requirements_count``: number of requirements files
        ``specifications_count``: number of specification files
        ``test_count``: number of test files
        ``code_count``: number of code files
        ``health_score``: project health score between 0 and 10
    """

    analyzer = ProjectStateAnalyzer(project_path)
    result = analyzer.analyze()["health_report"]
    return {
        "requirements_count": result["requirements_count"],
        "specifications_count": result["specifications_count"],
        "test_count": result["test_count"],
        "code_count": result["code_count"],
        "health_score": result["health_score"],
    }
