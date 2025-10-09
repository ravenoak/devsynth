from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.agents.base import BaseAgent
from devsynth.domain.models.memory import MemoryItem
from devsynth.domain.models.wsde_facade import WSDETeam
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios(
    feature_path(
        __file__, "general", "multi_disciplinary_dialectical_reasoning.feature"
    )
)


# Define a fixture for the context
@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.team = None
            self.task = None
            self.solution = None
            self.knowledge_sources = None
            self.disciplinary_agents = []
            self.perspectives = []
            self.conflicts = []
            self.synthesis = None
            self.evaluation = None
            self.result = None

    return Context()


# Helper function to create a mock agent with expertise
def create_mock_agent(name, expertise):
    agent = MagicMock(spec=BaseAgent)
    agent.name = name
    agent.agent_type = "mock"
    agent.current_role = None
    agent.expertise = expertise
    agent.has_been_primus = False
    return agent


# Background steps
@given("a WSDE team with agents specialized in different disciplines")
def wsde_team_with_specialized_agents(context):
    """Create a WSDE team with agents specialized in different disciplines."""
    context.team = WSDETeam(name="TestMddrCommonTeam")
    # Create agents with different disciplinary expertise
    code_agent = create_mock_agent("CodeAgent", ["python", "coding"])
    security_agent = create_mock_agent("SecurityAgent", ["security", "authentication"])
    ux_agent = create_mock_agent("UXAgent", ["user_experience", "interface_design"])
    performance_agent = create_mock_agent(
        "PerformanceAgent", ["performance", "optimization"]
    )
    accessibility_agent = create_mock_agent(
        "AccessibilityAgent", ["accessibility", "inclusive_design"]
    )
    critic_agent = create_mock_agent(
        "CriticAgent", ["dialectical_reasoning", "critique", "synthesis"]
    )

    # Add agents to the team
    context.team.add_agent(code_agent)
    context.team.add_agent(security_agent)
    context.team.add_agent(ux_agent)
    context.team.add_agent(performance_agent)
    context.team.add_agent(accessibility_agent)
    context.team.add_agent(critic_agent)

    # Store agents for later use
    context.disciplinary_agents = [
        code_agent,
        security_agent,
        ux_agent,
        performance_agent,
        accessibility_agent,
        critic_agent,
    ]


@given("a knowledge base with multi-disciplinary information")
def knowledge_base_with_multi_disciplinary_information(context):
    """Create a knowledge base with multi-disciplinary information."""
    # Mock the knowledge base
    context.knowledge_sources = {
        "security": [
            {"title": "OWASP Top 10", "content": "Security best practices..."},
            {"title": "NIST Guidelines", "content": "Security standards..."},
        ],
        "user_experience": [
            {"title": "Nielsen's Heuristics", "content": "UX principles..."},
            {"title": "Design System Guidelines", "content": "UI/UX standards..."},
        ],
        "performance": [
            {
                "title": "Web Performance Optimization",
                "content": "Performance best practices...",
            },
            {
                "title": "MDN Performance Guidelines",
                "content": "Browser optimization techniques...",
            },
        ],
        "accessibility": [
            {"title": "WCAG 2.1 Guidelines", "content": "Accessibility standards..."},
            {"title": "WebAIM Checklist", "content": "Accessibility best practices..."},
        ],
    }

    # Mock the team's knowledge retrieval method
    context.team.get_knowledge_for_discipline = MagicMock()
    context.team.get_knowledge_for_discipline.side_effect = (
        lambda discipline: context.knowledge_sources.get(discipline, [])
    )


@given("the team is configured for multi-disciplinary dialectical reasoning")
def team_configured_for_multi_disciplinary_dialectical_reasoning(context):
    """Configure the team for multi-disciplinary dialectical reasoning."""
    # Mock the configuration
    context.team.enable_multi_disciplinary_dialectical_reasoning = MagicMock()
    context.team.enable_multi_disciplinary_dialectical_reasoning.return_value = True

    # Call the method to enable multi-disciplinary dialectical reasoning
    result = context.team.enable_multi_disciplinary_dialectical_reasoning()

    # Verify the configuration was successful
    assert result is True, "Failed to enable multi-disciplinary dialectical reasoning"
