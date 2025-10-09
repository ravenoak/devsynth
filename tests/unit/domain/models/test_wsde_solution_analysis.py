"""Unit tests for wsde_solution_analysis helper methods."""

import pytest


@pytest.mark.fast
def test_analyze_solution_scores_requirements(wsde_module_team):
    """ReqID: WSDE-SOLUTION-01 — tallies addressed requirements and strengths."""

    team, _ = wsde_module_team
    task = {
        "id": "solution-task",
        "requirements": ["logging", "monitoring"],
        "constraints": ["budget"],
    }
    solution = {
        "id": "sol-1",
        "content": """
            This solution enables logging and monitoring through a shared platform.
            The budget considerations are documented to ensure stakeholder alignment.
            Additionally, it provides playbooks for on-call teams with actionable insights.
        """.strip(),
        "code": "def implement():\n    return 'logging monitoring'\n",
    }

    analysis = team._analyze_solution(solution, task, solution_number=1)

    assert analysis["requirements_addressed"] == 2
    assert "Includes code implementation" in analysis["strengths"]
    assert analysis["constraints_respected"] == 1


@pytest.mark.fast
def test_analyze_solution_highlights_gaps(wsde_module_team):
    """ReqID: WSDE-SOLUTION-02 — flags weak submissions for remediation."""

    team, _ = wsde_module_team
    task = {
        "id": "solution-gap",
        "requirements": ["audit trail"],
        "constraints": ["latency"],
    }
    solution = {
        "id": "sol-2",
        "content": "Short answer.",
        "code": "",
    }

    analysis = team._analyze_solution(solution, task, solution_number=1)

    assert "Limited explanation" in analysis["weaknesses"]
    assert "No code implementation" in analysis["weaknesses"]
    assert analysis["requirements_addressed"] == 0
    assert analysis["constraints_respected"] == 0


@pytest.mark.fast
def test_generate_comparative_analysis_identifies_best_solution(wsde_module_team):
    """ReqID: WSDE-SOLUTION-03 — ranks solutions by requirement coverage."""

    team, _ = wsde_module_team
    task = {"id": "compare", "requirements": ["encryption"], "constraints": []}

    solutions = [
        {
            "id": "sol-1",
            "content": "Implements encryption",
            "code": "def enc():\n    pass\n",
        },
        {"id": "sol-2", "content": "No mention", "code": ""},
    ]

    analyses = [
        team._analyze_solution(solution, task, index + 1)
        for index, solution in enumerate(solutions)
    ]

    comparative = team._generate_comparative_analysis(analyses, task)

    requirement_summary = comparative["requirement_comparisons"]["encryption"]
    assert requirement_summary["best_solution"] == 1
    assert requirement_summary["solution_scores"][1] == 1
    assert requirement_summary["solution_scores"].get(2, 0) == 0
    assert comparative["best_solution"] == 1


@pytest.mark.fast
def test_generate_comparative_analysis_handles_empty(wsde_module_team):
    """ReqID: WSDE-SOLUTION-04 — returns default comparison when analyses missing."""

    team, _ = wsde_module_team

    comparative = team._generate_comparative_analysis(
        [], {"id": "empty", "requirements": [], "constraints": []}
    )

    assert comparative["requirement_comparisons"] == {}
    assert comparative["constraint_comparisons"] == {}
    assert comparative["overall_scores"] == {}
    assert comparative["best_solution"] is None
    assert comparative["task_id"] == "empty"
