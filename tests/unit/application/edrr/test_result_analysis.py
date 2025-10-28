from unittest.mock import MagicMock

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam


@pytest.fixture
def coordinator():
    memory_manager = MagicMock(spec=MemoryManager)
    memory_manager.stored_items = {}
    memory_manager.store_with_edrr_phase.side_effect = (
        lambda item, item_type, phase, metadata: memory_manager.stored_items.update(
            {item_type: {"item": item, "phase": phase, "metadata": metadata}}
        )
    )
    memory_manager.retrieve_with_edrr_phase.side_effect = (
        lambda item_type, phase, metadata: memory_manager.stored_items.get(
            item_type, {}
        ).get("item", {})
    )
    wsde_team = MagicMock(spec=WSDETeam)
    code_analyzer = MagicMock(spec=CodeAnalyzer)
    ast_transformer = MagicMock(spec=AstTransformer)
    prompt_manager = MagicMock(spec=PromptManager)
    documentation_manager = MagicMock(spec=DocumentationManager)
    return EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
    )


@pytest.fixture
def coordinator_with_values(tmp_path):
    memory_manager = MagicMock(spec=MemoryManager)
    memory_manager.stored_items = {}
    memory_manager.store_with_edrr_phase.side_effect = (
        lambda item, item_type, phase, metadata: memory_manager.stored_items.update(
            {item_type: {"item": item, "phase": phase, "metadata": metadata}}
        )
    )
    memory_manager.retrieve_with_edrr_phase.side_effect = (
        lambda item_type, phase, metadata: memory_manager.stored_items.get(
            item_type, {}
        ).get("item", {})
    )
    wsde_team = MagicMock(spec=WSDETeam)
    code_analyzer = MagicMock(spec=CodeAnalyzer)
    ast_transformer = MagicMock(spec=AstTransformer)
    prompt_manager = MagicMock(spec=PromptManager)
    documentation_manager = MagicMock(spec=DocumentationManager)
    values_dir = tmp_path / ".devsynth"
    values_dir.mkdir()
    (values_dir / "values.yml").write_text("- honesty\n")
    return EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        config={"project_root": str(tmp_path)},
    )


@pytest.mark.medium
def test_extract_key_insights_succeeds(coordinator):
    """Test that extract key insights succeeds.

    ReqID: N/A"""
    expand_results = {
        "ideas": [{"idea": "A"}, {"idea": "B"}],
        "knowledge": [1, 2, 3],
        "code_elements": {"files": 5, "functions": 2},
    }
    insights = coordinator._extract_key_insights(expand_results)
    assert insights
    assert any("A" in i for i in insights)
    assert any("5" in i for i in insights)


@pytest.mark.medium
def test_summarize_implementation_succeeds(coordinator):
    """Test that summarize implementation succeeds.

    ReqID: N/A"""
    plan = [{"component": "X"}, {"component": "Y"}]
    summary = coordinator._summarize_implementation(plan)
    assert summary["steps"] == 2
    assert "X" in summary["primary_components"]
    assert summary["estimated_complexity"] == "Low"


@pytest.mark.medium
def test_summarize_quality_checks_succeeds(coordinator):
    """Test that summarize quality checks succeeds.

    ReqID: N/A"""
    checks = {
        "issues": [
            {"severity": "critical", "area": "security"},
            {"severity": "minor", "area": "style"},
        ]
    }
    summary = coordinator._summarize_quality_checks(checks)
    assert summary["issues_found"] == 2
    assert summary["critical_issues"] == 1
    assert "security" in summary["areas_of_concern"]


@pytest.mark.medium
def test_extract_key_learnings_succeeds(coordinator):
    """Test that extract key learnings succeeds.

    ReqID: N/A"""
    learnings = [
        {"learning": "L1"},
        {"learning": "L2"},
        {"learning": "L3"},
        {"learning": "L4"},
    ]
    result = coordinator._extract_key_learnings(learnings)
    assert result == ["L1", "L2", "L3"]


@pytest.mark.medium
def test_generate_next_steps_succeeds(coordinator):
    """Test that generate next steps succeeds.

    ReqID: N/A"""
    cycle_data = {
        "refine": {"implementation_plan": [1]},
        "retrospect": {"improvement_suggestions": ["a"]},
    }
    steps = coordinator._generate_next_steps(cycle_data)
    assert steps
    assert any("Implement" in s for s in steps)
    assert any("improvement" in s for s in steps)


@pytest.mark.medium
def test_extract_future_considerations_succeeds(coordinator):
    """Test that extract future considerations succeeds.

    ReqID: N/A"""
    retrospect_results = {"patterns": [1, 2], "improvement_suggestions": [1]}
    considerations = coordinator._extract_future_considerations(retrospect_results)
    assert considerations
    assert any("pattern" in c for c in considerations)
    assert any("improvement" in c for c in considerations)


@pytest.mark.medium
def test_final_report_includes_value_conflicts_succeeds(coordinator_with_values):
    """Test that final report includes value conflicts succeeds.

    ReqID: N/A"""
    coordinator_with_values.cycle_id = "cid"
    cycle_data = {
        "task": {"description": "This will violate honesty."},
        "expand": {},
        "differentiate": {},
        "refine": {},
        "retrospect": {},
    }
    report = coordinator_with_values.generate_final_report(cycle_data)
    assert "value_conflicts" in report
    assert report["value_conflicts"] == ["honesty"]
