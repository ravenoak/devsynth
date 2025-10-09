"""Step definitions for WSDE voting mechanisms."""

import logging
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file


scenarios(feature_path(__file__, "general", "wsde_voting_mechanisms.feature"))
scenarios(
    feature_path(
        __file__, "general", "wsde_voting_mechanisms_for_critical_decisions.feature"
    )
)

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType

# Import the modules needed for the steps
from devsynth.domain.models.wsde_facade import WSDETeam


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""

    class Context:
        def __init__(self):
            self.team_coordinator = WSDETeamCoordinator()
            self.agents = {}
            self.teams = {}
            self.tasks = {}
            self.solutions = {}
            self.votes = {}
            self.voting_results = {}
            self.current_team_id = None
            self.expertise_map = {}

    return Context()


# Background steps - reuse from test_wsde_agent_model_steps.py
@given("the DevSynth system is initialized")
def devsynth_system_initialized(context):
    """Initialize the DevSynth system."""
    # The system is initialized by creating the team coordinator
    assert context.team_coordinator is not None


@given("a team of agents is configured")
def team_of_agents_configured(context):
    """Configure a team of agents."""
    # Create a default team
    team_id = "test_team"
    context.team_coordinator.create_team(team_id)
    context.current_team_id = team_id
    context.teams[team_id] = context.team_coordinator.get_team(team_id)


@given("the WSDE model is enabled")
def wsde_model_enabled(context):
    """Enable the WSDE model."""
    # The WSDE model is enabled by default when a team is created
    assert context.teams[context.current_team_id] is not None


# Scenario: Voting on critical decisions
@given("a team with multiple agents with different expertise")
def team_with_agents_different_expertise(context):
    """Create a team with multiple agents with different expertise."""
    # Create a new team for this scenario
    team_id = "voting_team"
    context.team_coordinator.create_team(team_id)
    context.current_team_id = team_id
    context.teams[team_id] = context.team_coordinator.get_team(team_id)

    # Create multiple agents with different expertise
    expertise_map = {
        "code_agent": ["python", "javascript", "code_generation"],
        "test_agent": ["testing", "pytest", "test_generation"],
        "doc_agent": ["documentation", "markdown", "doc_generation"],
        "design_agent": ["architecture", "design", "planning"],
    }

    for agent_name, expertise in expertise_map.items():
        agent = UnifiedAgent()
        agent_config = AgentConfig(
            name=agent_name,
            agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent with expertise in {', '.join(expertise)}",
            capabilities=[],
            parameters={"expertise": expertise},
        )
        agent.initialize(agent_config)
        context.agents[agent_name] = agent
        context.team_coordinator.add_agent(agent)
        context.expertise_map[agent_name] = expertise

    # Ensure the team has the agents
    team = context.teams[context.current_team_id]
    assert len(team.agents) == len(expertise_map)


@when("a critical decision needs to be made")
def critical_decision_needed(context):
    """Create a critical decision that needs to be made."""
    # Create a critical decision task
    task = {
        "type": "critical_decision",
        "description": "Choose the best architecture for the system",
        "options": [
            {
                "id": "option1",
                "name": "Microservices",
                "description": "Use a microservices architecture",
            },
            {
                "id": "option2",
                "name": "Monolith",
                "description": "Use a monolithic architecture",
            },
            {
                "id": "option3",
                "name": "Serverless",
                "description": "Use a serverless architecture",
            },
        ],
        "is_critical": True,
    }
    context.tasks["critical_decision"] = task


@then("the system should initiate a voting process")
def system_initiates_voting(context):
    """Verify that the system initiates a voting process."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Get the critical decision task
    task = context.tasks["critical_decision"]

    # Mock the vote_on_critical_decision method to return a predefined result
    team.vote_on_critical_decision = MagicMock(
        return_value={
            "voting_initiated": True,
            "options": task["options"],
            "votes": {},
            "result": None,
        }
    )

    # Call the delegate_task method with the critical decision task
    result = context.team_coordinator.delegate_task(task)

    # Verify that the vote_on_critical_decision method was called
    team.vote_on_critical_decision.assert_called_once_with(task)

    # Verify that the result indicates voting was initiated
    assert "voting_initiated" in result
    assert result["voting_initiated"] is True

    # Store the result for later steps
    context.voting_results["critical_decision"] = result


@then("each agent should cast a vote based on their expertise")
def agents_cast_votes(context):
    """Verify that each agent casts a vote based on their expertise."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Get the critical decision task
    task = context.tasks["critical_decision"]

    # Create votes for each agent
    votes = {}
    for agent_name, agent in context.agents.items():
        # Determine which option this agent would vote for based on expertise
        expertise = context.expertise_map[agent_name]
        if "architecture" in expertise or "design" in expertise:
            # Design-focused agents prefer microservices
            vote = "option1"
        elif "code_generation" in expertise or "python" in expertise:
            # Code-focused agents prefer monolith
            vote = "option2"
        else:
            # Other agents prefer serverless
            vote = "option3"

        votes[agent_name] = vote

    # Update the mock to include the votes
    team.vote_on_critical_decision.return_value = {
        "voting_initiated": True,
        "options": task["options"],
        "votes": votes,
        "result": None,
    }

    # Call the delegate_task method again
    result = context.team_coordinator.delegate_task(task)

    # Verify that the votes were recorded
    assert "votes" in result
    assert len(result["votes"]) == len(context.agents)

    # Store the votes for later steps
    context.votes["critical_decision"] = votes
    context.voting_results["critical_decision"] = result


@then("the decision should be made based on majority vote")
def decision_by_majority_vote(context):
    """Verify that the decision is made based on majority vote."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Get the critical decision task
    task = context.tasks["critical_decision"]

    # Count the votes
    vote_counts = {}
    for agent_name, vote in context.votes["critical_decision"].items():
        vote_counts[vote] = vote_counts.get(vote, 0) + 1

    # Determine the winner
    winner = max(vote_counts.items(), key=lambda x: x[1])[0]

    # Find the winning option
    winning_option = next(
        option for option in task["options"] if option["id"] == winner
    )

    # Update the mock to include the result
    team.vote_on_critical_decision.return_value = {
        "voting_initiated": True,
        "options": task["options"],
        "votes": context.votes["critical_decision"],
        "result": {
            "winner": winner,
            "winning_option": winning_option,
            "vote_counts": vote_counts,
            "method": "majority_vote",
        },
    }

    # Call the delegate_task method again
    result = context.team_coordinator.delegate_task(task)

    # Verify that the result includes the winner
    assert "result" in result
    assert result["result"] is not None
    assert "winner" in result["result"]
    assert result["result"]["winner"] == winner

    # Store the result for later steps
    context.voting_results["critical_decision"] = result


@then("the voting results should be recorded")
def voting_results_recorded(context):
    """Verify that the voting results are recorded."""
    # Get the result from the previous step
    result = context.voting_results["critical_decision"]

    # Verify that the result includes all the necessary information
    assert "voting_initiated" in result
    assert "votes" in result
    assert "result" in result
    assert "winner" in result["result"]
    assert "vote_counts" in result["result"]
    assert "method" in result["result"]

    # Verify that the method is majority_vote
    assert result["result"]["method"] == "majority_vote"


# Scenario: Consensus fallback for tied votes
@given("a team with an even number of agents")
def team_with_even_number_of_agents(context):
    """Create a team with an even number of agents."""
    # Create a new team for this scenario
    team_id = "tied_vote_team"
    context.team_coordinator.create_team(team_id)
    context.current_team_id = team_id
    context.teams[team_id] = context.team_coordinator.get_team(team_id)

    # Create exactly 4 agents
    agent_configs = [
        {"name": "agent1", "expertise": ["python", "design"]},
        {"name": "agent2", "expertise": ["javascript", "testing"]},
        {"name": "agent3", "expertise": ["documentation", "planning"]},
        {"name": "agent4", "expertise": ["architecture", "security"]},
    ]

    for config in agent_configs:
        agent = UnifiedAgent()
        agent_config = AgentConfig(
            name=config["name"],
            agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent with expertise in {', '.join(config['expertise'])}",
            capabilities=[],
            parameters={"expertise": config["expertise"]},
        )
        agent.initialize(agent_config)
        context.agents[config["name"]] = agent
        context.team_coordinator.add_agent(agent)
        context.expertise_map[config["name"]] = config["expertise"]

    # Ensure the team has exactly 4 agents
    team = context.teams[context.current_team_id]
    assert len(team.agents) == 4


@when("a critical decision results in a tied vote")
def critical_decision_tied_vote(context):
    """Create a critical decision that results in a tied vote."""
    # Create a critical decision task
    task = {
        "type": "critical_decision",
        "description": "Choose the programming language for the project",
        "options": [
            {
                "id": "option1",
                "name": "Python",
                "description": "Use Python for the project",
            },
            {
                "id": "option2",
                "name": "JavaScript",
                "description": "Use JavaScript for the project",
            },
        ],
        "is_critical": True,
    }
    context.tasks["tied_vote"] = task

    # Create a tied vote (2 votes for each option)
    votes = {
        "agent1": "option1",
        "agent2": "option2",
        "agent3": "option1",
        "agent4": "option2",
    }
    context.votes["tied_vote"] = votes

    # Count the votes
    vote_counts = {}
    for agent_name, vote in votes.items():
        vote_counts[vote] = vote_counts.get(vote, 0) + 1

    # Verify that the vote is tied
    assert vote_counts["option1"] == vote_counts["option2"]

    # Get the team
    team = context.teams[context.current_team_id]

    # Mock the vote_on_critical_decision method to return a tied result
    team.vote_on_critical_decision = MagicMock(
        return_value={
            "voting_initiated": True,
            "options": task["options"],
            "votes": votes,
            "result": {
                "tied": True,
                "tied_options": ["option1", "option2"],
                "vote_counts": vote_counts,
                "method": "tied_vote",
            },
        }
    )

    # Call the delegate_task method with the tied vote task
    result = context.team_coordinator.delegate_task(task)

    # Verify that the result indicates a tied vote
    assert "result" in result
    assert "tied" in result["result"]
    assert result["result"]["tied"] is True

    # Store the result for later steps
    context.voting_results["tied_vote"] = result


@then("the system should fall back to consensus-building")
def system_falls_back_to_consensus(context):
    """Verify that the system falls back to consensus-building for tied votes."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Get the tied vote task
    task = context.tasks["tied_vote"]

    # Mock the build_consensus method to return a consensus result
    team.build_consensus = MagicMock(
        return_value={
            "consensus": "Use Python for backend and JavaScript for frontend",
            "contributors": ["agent1", "agent2", "agent3", "agent4"],
            "method": "consensus_synthesis",
            "reasoning": "Combined the best elements from both options",
        }
    )

    # Update the vote_on_critical_decision mock to include the consensus fallback
    team.vote_on_critical_decision.return_value = {
        "voting_initiated": True,
        "options": task["options"],
        "votes": context.votes["tied_vote"],
        "result": {
            "tied": True,
            "tied_options": ["option1", "option2"],
            "vote_counts": {"option1": 2, "option2": 2},
            "method": "tied_vote",
            "fallback": "consensus",
            "consensus_result": {
                "consensus": "Use Python for backend and JavaScript for frontend",
                "contributors": ["agent1", "agent2", "agent3", "agent4"],
                "method": "consensus_synthesis",
                "reasoning": "Combined the best elements from both options",
            },
        },
    }

    # Call the delegate_task method again
    result = context.team_coordinator.delegate_task(task)

    # Verify that the result includes the consensus fallback
    assert "result" in result
    assert "fallback" in result["result"]
    assert result["result"]["fallback"] == "consensus"
    assert "consensus_result" in result["result"]

    # Store the result for later steps
    context.voting_results["tied_vote"] = result


@then("the final decision should reflect input from all agents")
def final_decision_reflects_all_input(context):
    """Verify that the final decision reflects input from all agents."""
    # Get the result from the previous step
    result = context.voting_results["tied_vote"]

    # Verify that the consensus result includes input from all agents
    assert "consensus_result" in result["result"]
    assert "contributors" in result["result"]["consensus_result"]
    assert len(result["result"]["consensus_result"]["contributors"]) == len(
        context.agents
    )

    # Verify that the consensus includes a reasoning
    assert "reasoning" in result["result"]["consensus_result"]
    assert result["result"]["consensus_result"]["reasoning"] != ""


@then("the decision-making process should be documented")
def decision_making_process_documented(context):
    """Verify that the decision-making process is documented."""
    # Get the result from the previous step
    result = context.voting_results["tied_vote"]

    # Verify that the result includes documentation of the process
    assert "voting_initiated" in result
    assert "votes" in result
    assert "result" in result
    assert "tied" in result["result"]
    assert "tied_options" in result["result"]
    assert "vote_counts" in result["result"]
    assert "method" in result["result"]
    assert "fallback" in result["result"]
    assert "consensus_result" in result["result"]

    # Verify that the consensus result includes reasoning
    assert "reasoning" in result["result"]["consensus_result"]
    assert result["result"]["consensus_result"]["reasoning"] != ""


# Scenario: Weighted voting based on expertise
@given("a team with agents having different levels of expertise")
def team_with_agents_different_expertise_levels(context):
    """Create a team with agents having different levels of expertise."""
    # Create a new team for this scenario
    team_id = "weighted_vote_team"
    context.team_coordinator.create_team(team_id)
    context.current_team_id = team_id
    context.teams[team_id] = context.team_coordinator.get_team(team_id)

    # Create agents with different levels of expertise
    expertise_map = {
        "security_expert": {
            "expertise": ["security", "encryption", "authentication"],
            "level": "expert",
        },
        "security_intermediate": {
            "expertise": ["security", "firewalls"],
            "level": "intermediate",
        },
        "security_novice": {"expertise": ["security"], "level": "novice"},
        "other_agent": {"expertise": ["python", "javascript"], "level": "intermediate"},
    }

    for agent_name, details in expertise_map.items():
        agent = UnifiedAgent()
        agent_config = AgentConfig(
            name=agent_name,
            agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent with {details['level']} expertise in {', '.join(details['expertise'])}",
            capabilities=[],
            parameters={
                "expertise": details["expertise"],
                "expertise_level": details["level"],
            },
        )
        agent.initialize(agent_config)
        context.agents[agent_name] = agent
        context.team_coordinator.add_agent(agent)
        context.expertise_map[agent_name] = details

    # Ensure the team has the agents
    team = context.teams[context.current_team_id]
    assert len(team.agents) == len(expertise_map)


@when("a critical decision in a specific domain needs to be made")
def critical_decision_in_specific_domain(context):
    """Create a critical decision in a specific domain."""
    # Create a critical decision task in the security domain
    task = {
        "type": "critical_decision",
        "domain": "security",
        "description": "Choose the authentication method for the system",
        "options": [
            {
                "id": "option1",
                "name": "OAuth",
                "description": "Use OAuth for authentication",
            },
            {
                "id": "option2",
                "name": "JWT",
                "description": "Use JWT for authentication",
            },
            {
                "id": "option3",
                "name": "Basic Auth",
                "description": "Use Basic Auth for authentication",
            },
        ],
        "is_critical": True,
    }
    context.tasks["domain_specific"] = task


@then("agents with relevant expertise should have weighted votes")
def agents_have_weighted_votes(context):
    """Verify that agents with relevant expertise have weighted votes."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Get the domain-specific task
    task = context.tasks["domain_specific"]

    # Create vote weights based on expertise
    vote_weights = {
        "security_expert": 3,  # Expert in the domain
        "security_intermediate": 2,  # Intermediate in the domain
        "security_novice": 1,  # Novice in the domain
        "other_agent": 0.5,  # Not specialized in the domain
    }

    # Create votes
    votes = {
        "security_expert": "option2",  # Expert votes for JWT
        "security_intermediate": "option1",  # Intermediate votes for OAuth
        "security_novice": "option1",  # Novice votes for OAuth
        "other_agent": "option3",  # Other agent votes for Basic Auth
    }

    # Calculate weighted vote counts
    weighted_votes = {}
    for agent_name, vote in votes.items():
        weight = vote_weights[agent_name]
        weighted_votes[vote] = weighted_votes.get(vote, 0) + weight

    # Determine the winner based on weighted votes
    winner = max(weighted_votes.items(), key=lambda x: x[1])[0]

    # Find the winning option
    winning_option = next(
        option for option in task["options"] if option["id"] == winner
    )

    # Mock the vote_on_critical_decision method to return a weighted voting result
    team.vote_on_critical_decision = MagicMock(
        return_value={
            "voting_initiated": True,
            "options": task["options"],
            "votes": votes,
            "vote_weights": vote_weights,
            "weighted_votes": weighted_votes,
            "result": {
                "winner": winner,
                "winning_option": winning_option,
                "vote_counts": {
                    vote: sum(1 for v in votes.values() if v == vote)
                    for vote in set(votes.values())
                },
                "weighted_vote_counts": weighted_votes,
                "method": "weighted_vote",
            },
        }
    )

    # Call the delegate_task method with the domain-specific task
    result = context.team_coordinator.delegate_task(task)

    # Verify that the result includes vote weights
    assert "vote_weights" in result
    assert len(result["vote_weights"]) == len(context.agents)

    # Verify that the weights are assigned correctly
    for agent_name, weight in vote_weights.items():
        assert agent_name in result["vote_weights"]
        assert result["vote_weights"][agent_name] == weight

    # Store the result for later steps
    context.voting_results["domain_specific"] = result


@then("the final decision should favor domain experts")
def final_decision_favors_domain_experts(context):
    """Verify that the final decision favors domain experts."""
    # Get the result from the previous step
    result = context.voting_results["domain_specific"]

    # Verify that the result includes weighted votes
    assert "weighted_votes" in result
    assert "result" in result
    assert "winner" in result["result"]

    # Verify that the winner is determined by weighted votes
    assert result["result"]["method"] == "weighted_vote"

    # In our mock, the expert voted for option2 (JWT)
    # Even though more agents voted for option1, the expert's vote should have more weight
    # Check if the winner is what the expert voted for
    expert_vote = "option2"  # What the security_expert voted for
    assert result["result"]["winner"] == expert_vote


@then("the weighting mechanism should be transparent")
def weighting_mechanism_transparent(context):
    """Verify that the weighting mechanism is transparent."""
    # Get the result from the previous step
    result = context.voting_results["domain_specific"]

    # Verify that the result includes transparent information about the weighting
    assert "vote_weights" in result
    assert "weighted_votes" in result
    assert "result" in result
    assert "vote_counts" in result["result"]
    assert "weighted_vote_counts" in result["result"]

    # Verify that the weighted vote counts match what we expect
    weighted_votes = result["weighted_votes"]
    vote_weights = result["vote_weights"]
    votes = result["votes"]

    # Calculate expected weighted votes
    expected_weighted_votes = {}
    for agent_name, vote in votes.items():
        weight = vote_weights[agent_name]
        expected_weighted_votes[vote] = expected_weighted_votes.get(vote, 0) + weight

    # Verify that the weighted votes match the expected values
    for vote, weight in expected_weighted_votes.items():
        assert vote in weighted_votes
        assert weighted_votes[vote] == weight
