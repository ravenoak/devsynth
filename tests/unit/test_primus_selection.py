import pytest
from unittest.mock import MagicMock

from devsynth.domain.models.wsde import WSDETeam


def create_agent(name: str, expertise: list[str]):
    agent = MagicMock()
    agent.name = name
    agent.expertise = expertise
    agent.current_role = None
    agent.has_been_primus = False
    return agent


def test_highest_expertise_score_becomes_primus():
    team = WSDETeam()
    python_agent = create_agent("Python", ["python", "backend"])
    js_agent = create_agent("JS", ["javascript", "frontend"])
    tester = create_agent("Tester", ["testing"])
    team.add_agents([python_agent, js_agent, tester])

    task = {"type": "coding", "language": "python", "domain": "backend"}
    team.select_primus_by_expertise(task)

    assert team.get_primus() is python_agent
    assert python_agent.has_been_primus


def test_prioritizes_agents_who_have_not_served_as_primus():
    team = WSDETeam()
    python_agent = create_agent("Python", ["python"])
    doc_agent = create_agent("Doc", ["documentation", "markdown"])
    team.add_agents([python_agent, doc_agent])

    task = {"type": "coding", "language": "python"}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is python_agent

    team.select_primus_by_expertise(task)
    assert team.get_primus() is doc_agent
    assert doc_agent.has_been_primus


def test_documentation_tasks_prefer_documentation_experts():
    team = WSDETeam()
    coder = create_agent("Coder", ["python"])
    doc_agent = create_agent("Doc", ["documentation", "markdown"])
    team.add_agents([coder, doc_agent])

    task = {"type": "documentation", "description": "Update docs"}
    team.select_primus_by_expertise(task)

    assert team.get_primus() is doc_agent
    assert doc_agent.has_been_primus
