from types import SimpleNamespace

import pytest

from devsynth.domain.models.wsde_knowledge import (
    KnowledgeGraphInsights,
    _get_task_id,
    _identify_relevant_knowledge,
)


@pytest.mark.fast
def test_get_task_id_uses_existing_id():
    """ReqID: WSDE-KNOW-01 — uses existing task id when provided."""
    task = {"id": "task-123", "description": "Do something"}
    assert _get_task_id(SimpleNamespace(), task) == "task-123"


@pytest.mark.fast
def test_identify_relevant_knowledge_matches_keywords():
    """ReqID: WSDE-KNOW-02 — matches external knowledge by keywords."""
    task = {"description": "Build web api"}
    solution = {"content": "Use Flask"}
    external = {
        "standards": [{"name": "Flask Standard", "keywords": ["flask"]}],
        "best_practices": [{"name": "API Guide", "keywords": ["api"]}],
        "patterns": [{"name": "MVC", "keywords": ["flask"]}],
        "domains": {"web": {"keywords": ["web"]}},
    }
    result = _identify_relevant_knowledge(SimpleNamespace(), task, solution, external)
    assert external["standards"][0] in result["standards"]
    assert external["best_practices"][0] in result["best_practices"]
    assert external["patterns"][0] in result["patterns"]
    assert "web" in result["domain_specific"]


@pytest.mark.fast
def test_knowledge_graph_insights_parses_payload():
    """ReqID: WSDE-KNOW-03 — structures knowledge graph payloads via DTOs."""

    payload = {
        "similar_solutions": [
            {
                "approach": "Test Driven",
                "strengths": ["coverage"],
                "key_insights": ["write tests"],
            },
            "invalid-entry",
        ],
        "best_practices": [
            {
                "name": "Logging",
                "description": "Use structured logs",
                "keywords": ["logging", "structured"],
            },
            42,
        ],
    }

    insights = KnowledgeGraphInsights.from_payload(payload)

    assert len(insights.similar_solutions) == 1
    assert insights.similar_solutions[0].approach == "Test Driven"
    assert insights.similar_solutions[0].strengths == ("coverage",)
    assert insights.similar_solutions[0].key_insights == ("write tests",)

    assert len(insights.best_practices) == 1
    assert insights.best_practices[0].name == "Logging"
    assert insights.best_practices[0].description == "Use structured logs"
    assert insights.best_practices[0].keywords == ("logging", "structured")

    # round-trip serialization retains structured data
    serialized = insights.to_dict()
    assert serialized["similar_solutions"][0]["approach"] == "Test Driven"
    assert serialized["best_practices"][0]["keywords"] == ["logging", "structured"]


@pytest.mark.fast
def test_integrate_knowledge_builds_summary(wsde_module_team):
    """ReqID: WSDE-KNOW-04 — aggregates learnings and patterns into knowledge snapshot."""

    team, _ = wsde_module_team
    learnings = [
        {"summary": "Encrypt data stores", "phase": "build"},
        {"summary": "Document audit workflows", "phase": "deploy"},
    ]
    patterns = [
        {
            "name": "Encryption gap",
            "occurrences": 2,
            "evidence": ["Lack of envelope encryption"],
            "source_phases": ["build"],
        }
    ]

    knowledge = team.integrate_knowledge(learnings, patterns)

    assert knowledge["summary"].startswith("Top pattern: Encryption gap")
    assert len(knowledge["learnings"]) == 2
    assert len(knowledge["patterns"]) == 1


@pytest.mark.fast
def test_generate_improvement_suggestions_deduplicates_entries(wsde_module_team):
    """ReqID: WSDE-KNOW-05 — consolidates overlapping learnings and QA issues."""

    team, _ = wsde_module_team
    learnings = [
        {"summary": "Encrypt data stores", "phase": "build"},
        {"summary": "Encrypt data stores", "phase": "build"},
    ]
    patterns = [
        {
            "name": "Audit trail gap",
            "occurrences": 1,
            "evidence": ["No retention policy"],
            "source_phases": ["deploy"],
        }
    ]
    quality_checks = {
        "issues": [
            {"description": "Missing encryption test", "category": "test"},
            "Missing encryption test",
        ]
    }

    suggestions = team.generate_improvement_suggestions(
        learnings,
        patterns,
        quality_checks,
        categorize_by_phase=True,
    )

    suggestions_by_text = {item["suggestion"]: item for item in suggestions}
    assert "Revisit learning: Encrypt data stores" in suggestions_by_text
    assert (
        suggestions_by_text["Revisit learning: Encrypt data stores"]["category"]
        == "build"
    )
    assert "Resolve QA issue: Missing encryption test" in suggestions_by_text
