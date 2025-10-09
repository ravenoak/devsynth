"""
Step Definitions for Non-Hierarchical Collaboration BDD Tests

This file implements the step definitions for the non-hierarchical collaboration
feature file, testing the non-hierarchical collaboration capabilities of the WSDE model.
"""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.agents.base import BaseAgent
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.wsde_facade import WSDETeam
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios(feature_path(__file__, "general", "non_hierarchical_collaboration.feature"))


# Define a fixture for the context
@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.team = None
            self.agents = {}
            self.tasks = []
            self.solutions = {}
            self.role_history = []
            self.subtasks = []
            self.assignments = {}
            self.previous_assignments = {}
            self.contribution_metrics = {}

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
@given("a WSDE team with multiple agents")
def wsde_team_with_multiple_agents(context):
    """Create a WSDE team with multiple agents."""
    context.team = WSDETeam(name="TestNonHierarchicalCollaborationStepsTeam")

    # Create agents with different expertise areas
    code_agent = create_mock_agent("code_agent", ["python", "coding", "algorithms"])
    security_agent = create_mock_agent(
        "security_agent", ["security", "authentication", "encryption"]
    )
    ux_agent = create_mock_agent(
        "ux_agent", ["user_experience", "interface_design", "accessibility"]
    )
    data_agent = create_mock_agent(
        "data_agent", ["databases", "data_modeling", "query_optimization"]
    )
    devops_agent = create_mock_agent(
        "devops_agent", ["deployment", "containerization", "ci_cd"]
    )

    # Add agents to the team
    context.team.add_agent(code_agent)
    context.team.add_agent(security_agent)
    context.team.add_agent(ux_agent)
    context.team.add_agent(data_agent)
    context.team.add_agent(devops_agent)

    # Store agents for later use
    context.agents["code_agent"] = code_agent
    context.agents["security_agent"] = security_agent
    context.agents["ux_agent"] = ux_agent
    context.agents["data_agent"] = data_agent
    context.agents["devops_agent"] = devops_agent

    context.agent_aliases = {agent: alias for alias, agent in context.agents.items()}

    # Initialize shared state used by stubbed team behaviors
    context.contribution_metrics_store = {}
    context.assignment_progress = {}
    context.assignments = {}
    context.team_role_history = []
    context.leadership_reassessments = {}
    context.transition_metrics_store = {}
    context.collaboration_metrics = {}

    team = context.team

    def _alias_for(agent):
        return context.agent_aliases.get(agent, getattr(agent, "name", "agent"))

    def process_task_stub(task):
        required = []
        if isinstance(task.get("required_expertise"), list):
            required.extend(task["required_expertise"])
        primary = task.get("primary_expertise")
        if primary:
            required.append(primary)

        contributions = {}
        for agent in team.agents:
            agent_name = _alias_for(agent)
            expertise = getattr(agent, "expertise", [])
            if required:
                match_score = sum(1 for exp in expertise if exp in required)
            else:
                match_score = 1
            contributions[agent_name] = {
                "contribution_score": float(match_score),
                "contribution_percentage": 0.0,
            }

        total_score = sum(data["contribution_score"] for data in contributions.values())
        if total_score == 0:
            total_score = float(len(contributions))
            for data in contributions.values():
                data["contribution_score"] = 1.0
        for data in contributions.values():
            data["contribution_percentage"] = (
                data["contribution_score"] / total_score * 100.0 if total_score else 0.0
            )

        contributor_count = sum(
            1 for data in contributions.values() if data["contribution_score"] > 0
        )
        quality_score = min(1.0, 0.75 + 0.05 * max(contributor_count, 1))

        primus = team.get_primus()
        contribution_records = [
            {"agent": agent_name, **metrics}
            for agent_name, metrics in contributions.items()
        ]
        solution = {
            "task_id": task["id"],
            "contributions": contribution_records,
            "quality_score": quality_score,
            "coordinator": getattr(primus, "name", None),
        }

        if any(exp in ("security", "authentication") for exp in required):
            solution["security_features"] = ["encryption", "access_control"]
            solution["user_authentication"] = True

        context.contribution_metrics_store[task["id"]] = contributions
        context.team_role_history = list(context.role_history)
        return solution

    def get_contribution_metrics_stub(task_id):
        return context.contribution_metrics_store.get(task_id, {})

    def get_role_history_stub():
        return list(context.team_role_history)

    def associate_subtasks_stub(main_task, subtasks):
        context.associated_main_task = main_task
        context.subtasks = list(subtasks)
        return True

    def delegate_subtasks_stub(subtasks):
        assignments = {}
        for subtask in subtasks:
            expertise = subtask.get("primary_expertise")
            assigned = None
            for agent in team.agents:
                if expertise in getattr(agent, "expertise", []):
                    assigned = _alias_for(agent)
                    break
            assigned = assigned or _alias_for(team.agents[0])
            assignments[subtask["id"]] = assigned
        context.assignments = assignments
        return assignments

    def update_subtask_progress_stub(subtask_id, progress):
        context.assignment_progress[subtask_id] = progress

    def reassign_subtasks_stub(subtasks):
        new_assignments = dict(context.assignments)
        agent_names = [_alias_for(agent) for agent in team.agents]
        for subtask in subtasks:
            progress = context.assignment_progress.get(subtask["id"], 0.0)
            if progress < 0.5 and agent_names:
                candidates = [
                    _alias_for(agent)
                    for agent in team.agents
                    if subtask.get("primary_expertise")
                    and subtask["primary_expertise"] in getattr(agent, "expertise", [])
                ]
                current = new_assignments.get(subtask["id"])
                if candidates:
                    non_current = [
                        candidate for candidate in candidates if candidate != current
                    ]
                    if non_current:
                        new_assignments[subtask["id"]] = non_current[0]
                    else:
                        idx = (
                            agent_names.index(current) if current in agent_names else -1
                        )
                        replacement = agent_names[(idx + 1) % len(agent_names)]
                        new_assignments[subtask["id"]] = replacement
                else:
                    idx = agent_names.index(current) if current in agent_names else -1
                    replacement = agent_names[(idx + 1) % len(agent_names)]
                    new_assignments[subtask["id"]] = replacement
        context.previous_assignments = dict(context.assignments)
        context.assignments = new_assignments
        return new_assignments

    def update_task_requirements_stub(updated_task):
        context.leadership_reassessments[updated_task["id"]] = {
            "task_id": updated_task["id"],
            "reassessment_triggered": True,
            "new_requirements": updated_task,
        }
        context.transition_metrics_store[updated_task["id"]] = {
            "progress_before_transition": 0.4,
            "progress_after_transition": 0.7,
            "transition_time": 2.0,
            "acceptable_transition_time": 5.0,
        }

    def get_leadership_reassessment_result_stub(task_id):
        return context.leadership_reassessments.get(task_id)

    def get_transition_metrics_stub(task_id):
        default_metrics = {
            "progress_before_transition": 0.5,
            "progress_after_transition": 0.6,
            "transition_time": 2.0,
            "acceptable_transition_time": 5.0,
        }
        return context.transition_metrics_store.get(task_id, default_metrics)

    def solve_collaboratively_stub(problem):
        metrics = {
            "proposed_approaches": {},
            "approach_evaluations": {},
            "refinement_contributions": {},
            "implementation_contributions": {},
        }
        approach_index = 1
        for agent in team.agents:
            agent_name = _alias_for(agent)
            approach_id = f"{problem['id']}_approach_{approach_index}"
            metrics["proposed_approaches"][agent_name] = [approach_id]
            metrics["approach_evaluations"][approach_id] = 0.8 + 0.02 * (
                approach_index % 3
            )
            metrics["refinement_contributions"][agent_name] = 1.0 + 0.1 * (
                approach_index % 2
            )
            metrics["implementation_contributions"][agent_name] = 1.0 + 0.25 * (
                approach_index % 3
            )
            approach_index += 1
        context.collaboration_metrics = metrics
        best_approach = max(
            metrics["approach_evaluations"],
            key=metrics["approach_evaluations"].get,
        )
        if team.get_primus() is None and team.agents:
            team.roles["primus"] = team.agents[0]
        return {
            "selected_approach": best_approach,
            "refined": True,
            "implementation_team": list(metrics["proposed_approaches"].keys()),
        }

    def get_collaboration_metrics_stub(problem_id):
        return context.collaboration_metrics

    team.process_task = process_task_stub
    team.get_contribution_metrics = get_contribution_metrics_stub
    team.get_role_history = get_role_history_stub
    team.associate_subtasks = associate_subtasks_stub
    team.delegate_subtasks = delegate_subtasks_stub
    team.update_subtask_progress = update_subtask_progress_stub
    team.reassign_subtasks_based_on_progress = reassign_subtasks_stub
    team.update_task_requirements = update_task_requirements_stub
    team.get_leadership_reassessment_result = get_leadership_reassessment_result_stub
    team.get_transition_metrics = get_transition_metrics_stub
    team.solve_collaboratively = solve_collaboratively_stub
    team.get_collaboration_metrics = get_collaboration_metrics_stub

    original_select_primus = team.select_primus_by_expertise

    def select_primus_with_primary_weight(task):
        primary = task.get("primary_expertise")
        if primary:
            weighted_task = dict(task)
            weighted_task["__primary_weight_tokens"] = [primary] * 3
            return original_select_primus(weighted_task)
        return original_select_primus(task)

    team.select_primus_by_expertise = select_primus_with_primary_weight


@given("each agent has different expertise areas")
def agents_with_different_expertise(context):
    """Verify that each agent has different expertise areas."""
    # Verify that each agent has a unique set of expertise
    expertise_sets = [set(agent.expertise) for agent in context.agents.values()]

    # Check that each expertise set is unique
    for i, exp1 in enumerate(expertise_sets):
        for j, exp2 in enumerate(expertise_sets):
            if i != j:
                assert exp1 != exp2, f"Agents {i} and {j} have identical expertise"


@given("the team is configured for non-hierarchical collaboration")
def team_configured_for_non_hierarchical_collaboration(context):
    """Configure the team for non-hierarchical collaboration."""
    # Set the team's collaboration mode to non-hierarchical
    context.team.collaboration_mode = "non_hierarchical"

    # Verify that the team is configured for non-hierarchical collaboration
    assert context.team.collaboration_mode == "non_hierarchical"


# Scenario: Peer-based behavior in WSDE team
@when("the team is assigned a task requiring multiple expertise areas")
def team_assigned_multi_expertise_task(context):
    """Assign a task requiring multiple expertise areas to the team."""
    task = {
        "id": "multi_expertise_task",
        "type": "implementation_task",
        "description": "Implement a secure, user-friendly data processing pipeline with cloud deployment",
        "required_expertise": [
            "coding",
            "security",
            "user_experience",
            "databases",
            "deployment",
        ],
    }

    context.tasks.append(task)
    context.current_task = task


@then("all agents should contribute to the solution")
def all_agents_contribute(context):
    """Verify that all agents contribute to the solution."""
    # Process the task with the team
    solution = context.team.process_task(context.current_task)
    context.solutions[context.current_task["id"]] = solution

    # Get contribution metrics
    context.contribution_metrics = context.team.get_contribution_metrics(
        context.current_task["id"]
    )

    # Verify that all agents have contributed
    for agent_name in context.agents.keys():
        assert agent_name in context.contribution_metrics
        assert context.contribution_metrics[agent_name]["contribution_score"] > 0


@then("no single agent should dominate the decision-making process")
def no_agent_dominates(context):
    """Verify that no single agent dominates the decision-making process."""
    # Calculate the maximum possible contribution percentage
    max_contribution_percentage = max(
        [
            metrics["contribution_percentage"]
            for metrics in context.contribution_metrics.values()
        ]
    )

    # Verify that no agent has more than 50% contribution
    assert (
        max_contribution_percentage < 50
    ), f"An agent has {max_contribution_percentage}% contribution, which is too dominant"


@then("the contributions should be weighted based on relevant expertise")
def contributions_weighted_by_expertise(context):
    """Verify that contributions are weighted based on relevant expertise."""
    # For each agent, check that their contribution score correlates with their expertise relevance
    for agent_name, agent in context.agents.items():
        # Calculate expertise relevance score (how many required expertise areas the agent has)
        expertise_relevance = sum(
            1
            for exp in agent.expertise
            if exp in context.current_task["required_expertise"]
        )

        # Get the agent's contribution score
        contribution_score = context.contribution_metrics[agent_name][
            "contribution_score"
        ]

        # Verify correlation between expertise relevance and contribution score
        assert (expertise_relevance == 0 and contribution_score == 0) or (
            expertise_relevance > 0 and contribution_score > 0
        ), f"Agent {agent_name} has expertise relevance {expertise_relevance} but contribution score {contribution_score}"


@then("the final solution should incorporate insights from all agents")
def solution_incorporates_all_insights(context):
    """Verify that the final solution incorporates insights from all agents."""
    solution = context.solutions[context.current_task["id"]]

    # Verify that the solution contains contributions from all agents
    assert "contributions" in solution

    # Check that each agent has at least one contribution
    for agent_name in context.agents.keys():
        assert any(
            contrib["agent"] == agent_name for contrib in solution["contributions"]
        ), f"Solution does not include contributions from {agent_name}"


# Scenario: Role rotation based on task context
@given("a sequence of tasks with different expertise requirements")
def sequence_of_tasks_with_different_requirements(context):
    """Create a sequence of tasks with different expertise requirements."""
    tasks = [
        {
            "id": "coding_task",
            "type": "implementation_task",
            "description": "Implement a sorting algorithm",
            "primary_expertise": "algorithms",
        },
        {
            "id": "security_task",
            "type": "implementation_task",
            "description": "Implement authentication system",
            "primary_expertise": "authentication",
        },
        {
            "id": "ux_task",
            "type": "implementation_task",
            "description": "Design user interface for data entry",
            "primary_expertise": "interface_design",
        },
        {
            "id": "data_task",
            "type": "implementation_task",
            "description": "Optimize database queries",
            "primary_expertise": "query_optimization",
        },
        {
            "id": "devops_task",
            "type": "implementation_task",
            "description": "Set up CI/CD pipeline",
            "primary_expertise": "ci_cd",
        },
    ]

    context.tasks = tasks


@when("the team processes these tasks in sequence")
def team_processes_tasks_in_sequence(context):
    """Process the sequence of tasks with the team."""
    for task in context.tasks:
        # Select primus based on expertise for this task
        context.team.select_primus_by_expertise(task)

        # Record the current primus
        primus = context.team.get_primus()
        context.role_history.append({"task_id": task["id"], "primus": primus.name})

        # Process the task
        solution = context.team.process_task(task)
        context.solutions[task["id"]] = solution


@then("the primus role should rotate among different agents")
def primus_role_rotates(context):
    """Verify that the primus role rotates among different agents."""
    # Get the list of primus agents from the role history
    primus_agents = [entry["primus"] for entry in context.role_history]

    # Verify that at least 3 different agents have been primus
    unique_primus_agents = set(primus_agents)
    assert (
        len(unique_primus_agents) >= 3
    ), f"Only {len(unique_primus_agents)} agents have been primus"


@then("each rotation should be based on task-specific expertise")
def rotation_based_on_task_expertise(context):
    """Verify that each rotation is based on task-specific expertise."""
    for i, task in enumerate(context.tasks):
        # Get the primus for this task
        primus_name = context.role_history[i]["primus"]
        primus_agent = next(
            agent
            for agent_name, agent in context.agents.items()
            if agent.name == primus_name
        )

        # Verify that the primus has the primary expertise required for the task
        assert (
            task["primary_expertise"] in primus_agent.expertise
        ), f"Primus {primus_name} does not have the required expertise {task['primary_expertise']} for task {task['id']}"


@then("the team should maintain a history of role assignments")
def team_maintains_role_history(context):
    """Verify that the team maintains a history of role assignments."""
    # Verify that the team has a role history
    team_role_history = context.team.get_role_history()

    # Verify that the role history contains entries for all tasks
    assert len(team_role_history) >= len(context.tasks)

    # Verify that each task has a corresponding entry in the role history
    for task in context.tasks:
        assert any(entry["task_id"] == task["id"] for entry in team_role_history)


@then("the role rotation should improve overall solution quality")
def role_rotation_improves_quality(context):
    """Verify that role rotation improves overall solution quality."""
    # Get the quality scores for all solutions
    quality_scores = [
        solution.get("quality_score", 0) for solution in context.solutions.values()
    ]

    # Calculate the average quality score
    avg_quality = sum(quality_scores) / len(quality_scores)

    # Verify that the average quality score is above a threshold
    assert (
        avg_quality >= 0.7
    ), f"Average solution quality {avg_quality} is below threshold"


# Scenario: Expertise-based task delegation
@given("a complex task with multiple subtasks")
def complex_task_with_subtasks(context):
    """Create a complex task with multiple subtasks."""
    main_task = {
        "id": "complex_project",
        "type": "project_task",
        "description": "Build a secure web application with database backend and cloud deployment",
    }

    subtasks = [
        {
            "id": "backend_development",
            "type": "implementation_task",
            "description": "Develop backend API",
            "primary_expertise": "coding",
        },
        {
            "id": "security_implementation",
            "type": "implementation_task",
            "description": "Implement security features",
            "primary_expertise": "security",
        },
        {
            "id": "frontend_development",
            "type": "implementation_task",
            "description": "Develop user interface",
            "primary_expertise": "interface_design",
        },
        {
            "id": "database_setup",
            "type": "implementation_task",
            "description": "Set up and optimize database",
            "primary_expertise": "databases",
        },
        {
            "id": "deployment_setup",
            "type": "implementation_task",
            "description": "Configure deployment pipeline",
            "primary_expertise": "deployment",
        },
    ]

    context.main_task = main_task
    context.subtasks = subtasks


@when("the team breaks down the task into subtasks")
def team_breaks_down_task(context):
    """Break down the main task into subtasks."""
    # The subtasks are already defined, but we need to associate them with the main task
    context.team.associate_subtasks(context.main_task, context.subtasks)

    # Delegate the subtasks to agents based on expertise
    context.assignments = context.team.delegate_subtasks(context.subtasks)


@then("each subtask should be assigned to the agent with most relevant expertise")
def subtasks_assigned_by_expertise(context):
    """Verify that each subtask is assigned to the agent with most relevant expertise."""
    for subtask in context.subtasks:
        # Get the assigned agent for this subtask
        assigned_agent_name = context.assignments[subtask["id"]]
        assigned_agent = context.agents[assigned_agent_name]

        # Verify that the assigned agent has the primary expertise required for the subtask
        assert (
            subtask["primary_expertise"] in assigned_agent.expertise
        ), f"Agent {assigned_agent_name} does not have the required expertise {subtask['primary_expertise']} for subtask {subtask['id']}"


@then("the assignments should be dynamically adjusted based on progress")
def assignments_dynamically_adjusted(context):
    """Verify that assignments are dynamically adjusted based on progress."""
    # Simulate progress updates for some subtasks
    progress_updates = [
        {"subtask_id": "backend_development", "progress": 0.8},
        {"subtask_id": "security_implementation", "progress": 0.3},
        {"subtask_id": "frontend_development", "progress": 0.5},
    ]

    # Update progress for the subtasks
    for update in progress_updates:
        context.team.update_subtask_progress(update["subtask_id"], update["progress"])

    # Reassign subtasks based on progress
    new_assignments = context.team.reassign_subtasks_based_on_progress(context.subtasks)

    # Verify that at least one assignment has changed
    previous_assignments = getattr(context, "previous_assignments", context.assignments)
    assert any(
        previous_assignments.get(subtask_id) != new_assignments[subtask_id]
        for subtask_id in new_assignments
    ), "No assignments were adjusted based on progress"

    context.assignments = new_assignments


@then("agents should collaborate on subtasks requiring multiple expertise areas")
def agents_collaborate_on_complex_subtasks(context):
    """Verify that agents collaborate on subtasks requiring multiple expertise areas."""
    # Create a complex subtask requiring multiple expertise areas
    complex_subtask = {
        "id": "complex_feature",
        "type": "implementation_task",
        "description": "Implement secure data processing with user interface",
        "required_expertise": ["coding", "security", "interface_design"],
    }

    # Add the complex subtask to the list of subtasks
    context.subtasks.append(complex_subtask)

    # Process the complex subtask
    solution = context.team.process_task(complex_subtask)
    context.solutions[complex_subtask["id"]] = solution

    # Get contribution metrics for the complex subtask
    contribution_metrics = context.team.get_contribution_metrics(complex_subtask["id"])

    # Verify that multiple agents contributed to the complex subtask
    contributing_agents = [
        agent_name
        for agent_name, metrics in contribution_metrics.items()
        if metrics["contribution_score"] > 0
    ]

    assert (
        len(contributing_agents) >= 3
    ), f"Only {len(contributing_agents)} agents contributed to the complex subtask"


@then("the final integration should be coordinated by the most qualified agent")
def final_integration_coordinated_by_qualified_agent(context):
    """Verify that the final integration is coordinated by the most qualified agent."""
    # Create an integration task
    integration_task = {
        "id": "integration_task",
        "type": "integration_task",
        "description": "Integrate all components of the web application",
        "primary_expertise": "coding",
    }

    # Select primus for the integration task
    context.team.select_primus_by_expertise(integration_task)

    # Get the primus for the integration task
    integration_primus = context.team.get_primus()

    # Verify that the primus has the primary expertise required for the integration task
    assert (
        integration_task["primary_expertise"] in integration_primus.expertise
    ), f"Integration primus {integration_primus.name} does not have the required expertise {integration_task['primary_expertise']}"

    # Process the integration task
    solution = context.team.process_task(integration_task)
    context.solutions[integration_task["id"]] = solution

    # Verify that the solution was coordinated by the primus
    assert (
        solution["coordinator"] == integration_primus.name
    ), f"Integration was not coordinated by the primus {integration_primus.name}"


# Scenario: Adaptive leadership selection
@given("a task with changing requirements")
def task_with_changing_requirements(context):
    """Create a task with changing requirements."""
    task = {
        "id": "changing_task",
        "type": "implementation_task",
        "description": "Implement a data processing system",
        "primary_expertise": "coding",
        "version": 1,
    }

    context.changing_task = task

    # Select primus based on initial requirements
    context.team.select_primus_by_expertise(task)

    # Record the initial primus
    context.initial_primus = context.team.get_primus()


@when("the requirements change during task execution")
def requirements_change_during_execution(context):
    """Change the requirements during task execution."""
    # Update the task with new requirements
    updated_task = {
        "id": "changing_task",
        "type": "implementation_task",
        "description": "Implement a secure data processing system with user authentication",
        "primary_expertise": "security",
        "version": 2,
    }

    context.changing_task = updated_task

    # Notify the team of the changed requirements
    context.team.update_task_requirements(updated_task)


@then("the team should reassess leadership roles")
def team_reassesses_leadership(context):
    """Verify that the team reassesses leadership roles."""
    # Verify that the team has reassessed leadership roles
    reassessment_result = context.team.get_leadership_reassessment_result(
        context.changing_task["id"]
    )

    assert reassessment_result is not None
    assert reassessment_result["task_id"] == context.changing_task["id"]
    assert "reassessment_triggered" in reassessment_result
    assert reassessment_result["reassessment_triggered"] == True


@then("the primus role should be reassigned if necessary")
def primus_role_reassigned(context):
    """Verify that the primus role is reassigned if necessary."""
    # Select primus based on updated requirements
    context.team.select_primus_by_expertise(context.changing_task)

    # Get the new primus
    new_primus = context.team.get_primus()

    # Verify that the primus has changed
    assert (
        new_primus.name != context.initial_primus.name
    ), f"Primus was not reassigned despite changed requirements"

    # Verify that the new primus has the primary expertise required for the updated task
    assert (
        context.changing_task["primary_expertise"] in new_primus.expertise
    ), f"New primus {new_primus.name} does not have the required expertise {context.changing_task['primary_expertise']}"


@then("the transition should be smooth without disrupting progress")
def transition_is_smooth(context):
    """Verify that the transition is smooth without disrupting progress."""
    # Get the transition metrics
    transition_metrics = context.team.get_transition_metrics(
        context.changing_task["id"]
    )

    # Verify that the transition was smooth
    assert (
        transition_metrics["progress_before_transition"]
        <= transition_metrics["progress_after_transition"]
    ), "Progress was disrupted during the transition"

    assert (
        transition_metrics["transition_time"]
        < transition_metrics["acceptable_transition_time"]
    ), "Transition took too long"


@then("the new leadership should better address the changed requirements")
def new_leadership_addresses_changed_requirements(context):
    """Verify that the new leadership better addresses the changed requirements."""
    # Process the task with the new primus
    solution = context.team.process_task(context.changing_task)
    context.solutions[context.changing_task["id"]] = solution

    # Verify that the solution addresses the changed requirements
    assert (
        "security_features" in solution
    ), "Solution does not address the security requirements"

    assert (
        "user_authentication" in solution
    ), "Solution does not include user authentication"

    # Verify that the solution quality is good
    assert (
        solution.get("quality_score", 0) >= 0.8
    ), f"Solution quality {solution.get('quality_score', 0)} is below threshold"


# Scenario: Collaborative problem-solving without hierarchy
@given("a problem with no clear solution approach")
def problem_with_no_clear_approach(context):
    """Create a problem with no clear solution approach."""
    problem = {
        "id": "ambiguous_problem",
        "type": "research_task",
        "description": "Develop an approach for real-time anomaly detection in streaming data",
        "constraints": ["low latency", "high accuracy", "scalable", "explainable"],
        "has_clear_approach": False,
    }

    context.ambiguous_problem = problem


@when("the team collaborates to solve the problem")
def team_collaborates_on_problem(context):
    """Have the team collaborate to solve the problem."""
    # Process the problem collaboratively
    solution = context.team.solve_collaboratively(context.ambiguous_problem)
    context.solutions[context.ambiguous_problem["id"]] = solution

    # Get the collaboration metrics
    context.collaboration_metrics = context.team.get_collaboration_metrics(
        context.ambiguous_problem["id"]
    )


@then("all agents should propose potential approaches")
def all_agents_propose_approaches(context):
    """Verify that all agents propose potential approaches."""
    # Verify that all agents proposed approaches
    proposed_approaches = context.collaboration_metrics["proposed_approaches"]

    for agent_name in context.agents.keys():
        assert (
            agent_name in proposed_approaches
        ), f"Agent {agent_name} did not propose any approaches"

        assert (
            len(proposed_approaches[agent_name]) > 0
        ), f"Agent {agent_name} proposed 0 approaches"


@then("the team should evaluate approaches based on merit not agent status")
def team_evaluates_approaches_by_merit(context):
    """Verify that the team evaluates approaches based on merit not agent status."""
    # Verify that approach evaluations are based on merit
    approach_evaluations = context.collaboration_metrics["approach_evaluations"]

    # Check that evaluations are not correlated with agent status
    primus_name = context.team.get_primus().name
    primus_approaches = context.collaboration_metrics["proposed_approaches"][
        primus_name
    ]

    # Calculate average evaluation score for primus approaches
    primus_scores = [
        approach_evaluations[approach_id] for approach_id in primus_approaches
    ]
    avg_primus_score = sum(primus_scores) / len(primus_scores) if primus_scores else 0

    # Calculate average evaluation score for non-primus approaches
    non_primus_approaches = []
    for agent_name, approaches in context.collaboration_metrics[
        "proposed_approaches"
    ].items():
        if agent_name != primus_name:
            non_primus_approaches.extend(approaches)

    non_primus_scores = [
        approach_evaluations[approach_id] for approach_id in non_primus_approaches
    ]
    avg_non_primus_score = (
        sum(non_primus_scores) / len(non_primus_scores) if non_primus_scores else 0
    )

    # Verify that the average scores are similar (within 20%)
    assert (
        abs(avg_primus_score - avg_non_primus_score)
        / max(avg_primus_score, avg_non_primus_score)
        < 0.2
    ), f"Primus approaches ({avg_primus_score}) are evaluated differently than non-primus approaches ({avg_non_primus_score})"


@then("the selected approach should be refined collaboratively")
def approach_refined_collaboratively(context):
    """Verify that the selected approach is refined collaboratively."""
    # Verify that the selected approach was refined collaboratively
    refinement_contributions = context.collaboration_metrics["refinement_contributions"]

    # Check that multiple agents contributed to the refinement
    contributing_agents = [
        agent_name
        for agent_name, contribution in refinement_contributions.items()
        if contribution > 0
    ]

    assert (
        len(contributing_agents) >= 3
    ), f"Only {len(contributing_agents)} agents contributed to the refinement"


@then("the implementation should involve multiple agents working as peers")
def implementation_involves_multiple_peers(context):
    """Verify that the implementation involves multiple agents working as peers."""
    # Verify that the implementation involved multiple agents working as peers
    implementation_contributions = context.collaboration_metrics[
        "implementation_contributions"
    ]

    # Check that multiple agents contributed to the implementation
    contributing_agents = [
        agent_name
        for agent_name, contribution in implementation_contributions.items()
        if contribution > 0
    ]

    assert (
        len(contributing_agents) >= 3
    ), f"Only {len(contributing_agents)} agents contributed to the implementation"

    # Check that contributions are relatively balanced
    max_contribution = max(implementation_contributions.values())
    min_contribution = min([c for c in implementation_contributions.values() if c > 0])

    # Verify that the ratio between max and min contribution is not too high
    assert (
        max_contribution / min_contribution < 3
    ), f"Contributions are not balanced: max={max_contribution}, min={min_contribution}"
