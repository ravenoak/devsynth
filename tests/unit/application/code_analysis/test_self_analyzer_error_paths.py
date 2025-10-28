import os
from pathlib import Path
from typing import Any, Dict

import pytest

from devsynth.application.code_analysis.self_analyzer import SelfAnalyzer


@pytest.mark.fast
def test_self_analyzer_analyze_graceful_fallback(monkeypatch, tmp_path: Path):
    """ReqID: T-ANALYZER-ERR-001
    When the underlying CodeAnalyzer raises, SelfAnalyzer.analyze should not raise
    and must return a safe dictionary shape with default values.
    It must also avoid creating files outside the provided environment.
    """
    # Arrange: prepare a minimal project root recognized by SelfAnalyzer
    (tmp_path / "pyproject.toml").write_text(
        "[tool.poetry]\nname = 'dummy'\nversion = '0.0.0'\n"
    )

    # Force the CodeAnalyzer dependency to raise
    from devsynth.application.code_analysis import self_analyzer as sa_mod

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(sa_mod.CodeAnalyzer, "analyze_directory", staticmethod(boom))

    before = set(os.listdir(tmp_path))

    # Act
    analyzer = SelfAnalyzer(project_root=str(tmp_path))
    result: dict[str, Any] = analyzer.analyze()

    after = set(os.listdir(tmp_path))

    # Assert: safe shape
    assert "code_analysis" in result
    assert "insights" in result

    ca = result["code_analysis"]
    assert isinstance(ca, dict)
    assert "files" in ca and isinstance(ca["files"], dict)
    assert "dependencies" in ca and isinstance(ca["dependencies"], dict)
    assert "metrics" in ca and isinstance(ca["metrics"], dict)

    insights = result["insights"]
    assert isinstance(insights, dict)
    for key in (
        "metrics_summary",
        "architecture",
        "code_quality",
        "test_coverage",
        "improvement_opportunities",
    ):
        assert key in insights

    arch = insights["architecture"]
    assert arch.get("type") == "unknown"
    assert arch.get("confidence") == 0.0
    assert isinstance(arch.get("layers"), dict)
    assert isinstance(arch.get("layer_dependencies"), dict)
    assert isinstance(arch.get("architecture_violations"), list)

    cq = insights["code_quality"]
    assert cq.get("total_files") == 0
    assert cq.get("total_classes") == 0
    assert cq.get("total_functions") == 0
    assert isinstance(cq.get("docstring_coverage"), dict)

    tc = insights["test_coverage"]
    assert tc.get("total_symbols") == 0
    assert tc.get("tested_symbols") == 0
    assert tc.get("coverage_percentage") == 0.0

    # Assert: no unexpected files created
    assert before == after
