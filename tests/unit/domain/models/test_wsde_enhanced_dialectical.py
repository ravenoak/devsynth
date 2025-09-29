import pytest

from devsynth.domain.models.wsde_enhanced_dialectical import (
    _categorize_critiques_by_domain,
    _identify_domain_conflicts,
)


@pytest.mark.fast
def test_categorize_critiques_by_domain_groups_terms():
    """ReqID: WSDE-ENHANCED-01 — groups critiques by domain keywords."""
    critiques = [
        "Possible SQL injection",
        "Slow performance",
        "Needs example",
    ]
    categories = _categorize_critiques_by_domain(critiques)
    assert "Possible SQL injection" in categories["security"]
    assert "Slow performance" in categories["performance"]
    assert "Needs example" in categories["examples"]


@pytest.mark.fast
def test_identify_domain_conflicts_finds_performance_security():
    """ReqID: WSDE-ENHANCED-02 — detects performance vs security conflicts."""
    domain_critiques = {"performance": ["slow"], "security": ["injection"]}
    conflicts = _identify_domain_conflicts(domain_critiques)
    assert {"domain1": "performance", "domain2": "security"} in conflicts


@pytest.mark.fast
def test_apply_enhanced_dialectical_reasoning_generates_synthesis(
    wsde_team_factory, stub_agent_factory
):
    """ReqID: WSDE-ENHANCED-05 — synthesizes multi-domain critiques into output."""

    critic = stub_agent_factory(
        "dialectic-critic",
        critique_response={
            "critiques": ["Performance suffers", "Security controls are weak"],
            "improvement_suggestions": ["Document trade-offs"],
            "domain_specific_feedback": {
                "performance": ["Slow data processing"],
                "security": ["Encryption missing"],
                "code_quality": ["Functions too long"],
            },
        },
    )
    team = wsde_team_factory(agents=[critic])

    task = {
        "id": "dialectic-task",
        "solution": {
            "id": "sol-1",
            "content": "The API handles requests with minimal guidance.",
            "code": "def run():\n    return True\n",
        },
    }

    result = team.apply_enhanced_dialectical_reasoning(task, critic)

    assert result["status"] == "completed"
    synthesis = result["synthesis"]
    assert "security" in synthesis["domain_improvements"]
    assert "code_quality" in synthesis["domain_improvements"]
    resolutions = {entry["resolution"] for entry in synthesis["resolved_conflicts"]}
    assert "balanced code trade-off" in resolutions
    assert "clarified documentation" in resolutions


@pytest.mark.fast
def test_apply_enhanced_dialectical_reasoning_requires_solution(wsde_team_factory):
    """ReqID: WSDE-ENHANCED-06 — fails gracefully when task lacks a solution."""

    team = wsde_team_factory()

    result = team.apply_enhanced_dialectical_reasoning({}, critic_agent=None)

    assert result == {"error": "No solution found in task for dialectical reasoning"}
