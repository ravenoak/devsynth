import os
from pathlib import Path
from typing import Any, Dict

import pytest

from devsynth.application.code_analysis.project_state_analyzer import (
    ProjectStateAnalyzer,
)


@pytest.mark.fast
def test_project_state_analyzer_analyze_graceful_fallback(monkeypatch, tmp_path: Path):
    """ReqID: T-ANALYZER-ERR-002
    When any internal step raises, ProjectStateAnalyzer.analyze should not raise
    and must return a safe dictionary shape with default values.
    It must also avoid creating files outside the provided environment.
    """

    # Force an early method to raise to cover the error path
    def boom(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        raise RuntimeError("boom")

    monkeypatch.setattr(ProjectStateAnalyzer, "_index_files", boom)

    before = set(os.listdir(tmp_path))

    analyzer = ProjectStateAnalyzer(str(tmp_path))

    # Act
    result: dict[str, Any] = analyzer.analyze()

    after = set(os.listdir(tmp_path))

    # Assert: safe shape
    assert set(result.keys()) == {
        "files",
        "languages",
        "architecture",
        "components",
        "health_report",
    }

    assert result["files"] == {}
    assert result["languages"] == {}
    assert isinstance(result["architecture"], dict)
    assert result["architecture"].get("components", []) == []
    assert result["components"] == []

    hr = result["health_report"]
    assert isinstance(hr, dict)
    assert hr.get("status") == "unknown"
    assert "requirements_spec_alignment" in hr and isinstance(
        hr["requirements_spec_alignment"], dict
    )
    assert "spec_code_alignment" in hr and isinstance(hr["spec_code_alignment"], dict)
    assert "issues" in hr and isinstance(hr["issues"], list)
    assert "recommendations" in hr and isinstance(hr["recommendations"], list)

    # Assert: no unexpected files created
    assert before == after
