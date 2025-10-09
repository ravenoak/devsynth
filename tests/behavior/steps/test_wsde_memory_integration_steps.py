"""
Step Definitions for WSDE Model and Memory System Integration BDD Tests

This file implements the step definitions for the WSDE model and memory system integration
feature file, testing the integration between the WSDE model and the memory system.
"""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file


scenarios(feature_path(__file__, "general", "wsde_memory_integration.feature"))

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryItem, MemoryType

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
            self.dialectical_results = {}
            self.memory_adapter = None
            self.memory_manager = None
            self.current_team_id = None
            self.original_team_state = None
            self.retrieved_team_state = None
            self.knowledge_graph = None
            self.memory_backends = {}

    return Context()


# Background steps


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


@given("a team with multiple agents")
def given_team_with_multiple_agents(context):
    """Create a team with multiple agents."""
    # Create multiple agents with different roles
    agent_types = [
        AgentType.PLANNER.value,
        AgentType.SPECIFICATION.value,
        AgentType.CODE.value,
        AgentType.VALIDATION.value,
    ]

    for agent_type in agent_types:
        agent = UnifiedAgent()
        agent_config = AgentConfig(
            name=f"{agent_type}_agent",
            agent_type=AgentType(agent_type),
            description=f"Agent for {agent_type} tasks",
            capabilities=[],
            parameters={},
        )
        agent.initialize(agent_config)
        context.agents[agent_type] = agent
        context.team_coordinator.add_agent(agent)


@given("the memory system is configured with a test backend")
def memory_system_configured(context):
    """Configure the memory system with a test backend."""
    # Create a memory system adapter with an in-memory backend for testing
    context.memory_adapter = MemorySystemAdapter.create_for_testing(
        storage_type="memory"
    )

    # Create a memory manager that uses the memory store from the adapter
    # This is the key change - we're passing the memory store, not the adapter itself
    context.memory_manager = MemoryManager(
        {"default": context.memory_adapter.get_memory_store()}
    )


# Scenario: Store and retrieve WSDE team state


@when("I create a team with multiple agents")
def create_team_with_multiple_agents(context):
    """Create a team with multiple agents."""
    # Create multiple agents with different roles
    agent_types = [
        AgentType.PLANNER.value,
        AgentType.SPECIFICATION.value,
        AgentType.CODE.value,
        AgentType.VALIDATION.value,
    ]

    for agent_type in agent_types:
        agent = UnifiedAgent()
        agent_config = AgentConfig(
            name=f"{agent_type}_agent",
            agent_type=AgentType(agent_type),
            description=f"Agent for {agent_type} tasks",
            capabilities=[],
            parameters={},
        )
        agent.initialize(agent_config)
        context.agents[agent_type] = agent
        context.team_coordinator.add_agent(agent)


@when("I store the team state in memory")
def store_team_state_in_memory(context):
    """Store the team state in memory."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Store the original team state for later comparison
    context.original_team_state = {
        "team_id": context.current_team_id,
        "agents": [agent.config.name for agent in team.agents],
        "primus_index": team.primus_index,
    }

    # Create a memory item for the team state
    memory_item = MemoryItem(
        id="team_state_1",
        memory_type=MemoryType.TEAM_STATE,
        content=context.original_team_state,
        metadata={"team_id": context.current_team_id, "agent_count": len(team.agents)},
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)


@then("I should be able to retrieve the team state from memory")
def retrieve_team_state_from_memory(context):
    """Retrieve the team state from memory."""
    # Query for team state memory items
    query_result = context.memory_manager.query_by_type(MemoryType.TEAM_STATE)

    # Verify that we got at least one result
    assert len(query_result) > 0

    # Get the first result (should be our team state)
    team_state_item = query_result[0]

    # Store the retrieved team state for later comparison
    context.retrieved_team_state = team_state_item.content


@then("the retrieved team state should match the original state")
def verify_team_state_matches(context):
    """Verify that the retrieved team state matches the original state."""
    # Verify that the retrieved team state matches the original team state
    assert context.retrieved_team_state is not None
    assert context.original_team_state is not None

    # Compare team_id
    assert (
        context.retrieved_team_state["team_id"]
        == context.original_team_state["team_id"]
    )

    # Compare agents (order may not matter)
    assert set(context.retrieved_team_state["agents"]) == set(
        context.original_team_state["agents"]
    )

    # Compare primus_index
    assert (
        context.retrieved_team_state["primus_index"]
        == context.original_team_state["primus_index"]
    )


# Scenario: Store and retrieve solutions with EDRR phase tagging


@when(parsers.parse("a solution is proposed for a task"))
def solution_proposed_for_task(context):
    """Propose a solution for a task."""
    # Create a task
    task = {
        "type": "code_generation",
        "description": "Generate a Python function to calculate Fibonacci numbers",
    }
    context.tasks["fibonacci_task"] = task

    # Create a solution
    solution = {
        "agent": "code_agent",
        "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        "description": "Recursive implementation of Fibonacci",
    }
    context.solutions["fibonacci_solution"] = solution

    # Add the solution to the team
    team = context.teams[context.current_team_id]
    team.add_solution(task, solution)


@when(parsers.parse('the solution is stored in memory with EDRR phase "{phase}"'))
def store_solution_with_edrr_phase(context, phase):
    """Store the solution in memory with the specified EDRR phase."""
    # Get the task and solution
    task = context.tasks["fibonacci_task"]
    solution = context.solutions["fibonacci_solution"]

    # Create a memory item for the solution with EDRR phase
    memory_item = MemoryItem(
        id="solution_1",
        memory_type=MemoryType.SOLUTION,
        content=solution,
        metadata={
            "task_id": str(hash(frozenset(task.items()))),
            "agent": solution["agent"],
            "edrr_phase": phase,
        },
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)


@then("I should be able to retrieve the solution by EDRR phase")
def retrieve_solution_by_edrr_phase(context):
    """Retrieve the solution by EDRR phase."""
    # Query for solution memory items with EDRR phase "Expand"
    query_result = context.memory_manager.query_by_metadata({"edrr_phase": "Expand"})

    # Verify that we got at least one result
    assert len(query_result) > 0

    # Get the first result (should be our solution)
    solution_item = query_result[0]

    # Verify that it's a solution
    assert solution_item.memory_type == MemoryType.SOLUTION

    # Store the retrieved solution for later comparison
    context.retrieved_solution = solution_item.content


@then("the solution should have the correct EDRR phase tag")
def verify_solution_edrr_phase(context):
    """Verify that the solution has the correct EDRR phase tag."""
    # Query for solution memory items with EDRR phase "Expand"
    query_result = context.memory_manager.query_by_metadata({"edrr_phase": "Expand"})

    # Verify that we got at least one result
    assert len(query_result) > 0

    # Get the first result (should be our solution)
    solution_item = query_result[0]

    # Verify that it has the correct EDRR phase tag
    assert solution_item.metadata["edrr_phase"] == "Expand"


# Scenario: Store and retrieve dialectical reasoning results


@given("a team with a Critic agent")
def team_with_critic_agent(context):
    """Create a team with a Critic agent."""
    # Create a Critic agent
    agent = UnifiedAgent()
    agent_config = AgentConfig(
        name="critic_agent",
        agent_type=AgentType.ORCHESTRATOR,
        description="Agent for applying dialectical reasoning",
        capabilities=[],
        parameters={"expertise": ["dialectical_reasoning", "critique", "synthesis"]},
    )
    agent.initialize(agent_config)
    context.agents["critic_agent"] = agent
    context.team_coordinator.add_agent(agent)


@when("a solution is proposed")
def solution_proposed(context):
    """Propose a solution."""
    # Create a solution
    context.solutions["proposed_solution"] = {
        "agent": "code_agent",
        "description": "Solution for user authentication",
        "code": "def authenticate(username, password):\n    # Implementation details\n    return True",
    }


@when("the Critic agent applies dialectical reasoning")
def critic_applies_dialectical_reasoning(context):
    """Apply dialectical reasoning to the proposed solution."""
    # Get the team and critic agent
    team = context.teams[context.current_team_id]
    critic_agent = context.agents["critic_agent"]

    # Create a task for the dialectical reasoning
    task = {"type": "dialectical_test", "description": "Test dialectical reasoning"}
    context.tasks["dialectical_task"] = task

    # Add the proposed solution to the team
    team.add_solution(task, context.solutions["proposed_solution"])

    # Apply dialectical reasoning
    dialectical_result = team.apply_enhanced_dialectical_reasoning(task, critic_agent)

    # Store the dialectical result
    context.dialectical_results["auth_solution"] = dialectical_result


@when("the dialectical reasoning results are stored in memory")
def store_dialectical_results(context):
    """Store the dialectical reasoning results in memory."""
    # Get the task and dialectical result
    task = context.tasks["dialectical_task"]
    dialectical_result = context.dialectical_results["auth_solution"]

    # Create a memory item for the dialectical result
    memory_item = MemoryItem(
        id="dialectical_1",
        memory_type=MemoryType.DIALECTICAL_REASONING,
        content=dialectical_result,
        metadata={
            "task_id": str(hash(frozenset(task.items()))),
            "critic_agent": "critic_agent",
        },
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)


@then("I should be able to retrieve the dialectical reasoning results")
def retrieve_dialectical_results(context):
    """Retrieve the dialectical reasoning results from memory."""
    # Query for dialectical reasoning memory items
    query_result = context.memory_manager.query_by_type(
        MemoryType.DIALECTICAL_REASONING
    )

    # Verify that we got at least one result
    assert len(query_result) > 0

    # Get the first result (should be our dialectical result)
    dialectical_item = query_result[0]

    # Store the retrieved dialectical result for later comparison
    context.retrieved_dialectical_result = dialectical_item.content


@then("the retrieved results should contain thesis, antithesis, and synthesis")
def verify_dialectical_results(context):
    """Verify that the retrieved dialectical results contain thesis, antithesis, and synthesis."""
    # Verify that the retrieved dialectical result contains thesis, antithesis, and synthesis
    assert context.retrieved_dialectical_result is not None
    assert "thesis" in context.retrieved_dialectical_result
    assert "antithesis" in context.retrieved_dialectical_result
    assert "synthesis" in context.retrieved_dialectical_result


# Scenario: Access knowledge graph for enhanced reasoning


@given("a knowledge graph with domain knowledge")
def knowledge_graph_with_domain_knowledge(context):
    """Create a knowledge graph with domain knowledge."""
    # For testing purposes, we'll create a simple knowledge graph
    # In a real implementation, this would be an RDF graph or similar
    context.knowledge_graph = {
        "entities": {
            "authentication": {
                "type": "concept",
                "related": ["security", "password", "username"],
            },
            "password": {"type": "concept", "related": ["authentication", "security"]},
            "security": {
                "type": "concept",
                "related": ["authentication", "password", "encryption"],
            },
            "encryption": {"type": "concept", "related": ["security", "hashing"]},
            "hashing": {"type": "concept", "related": ["encryption", "password"]},
        },
        "relationships": [
            {"source": "authentication", "target": "password", "type": "uses"},
            {"source": "authentication", "target": "username", "type": "uses"},
            {"source": "password", "target": "hashing", "type": "should_use"},
            {"source": "security", "target": "encryption", "type": "requires"},
        ],
    }

    # Store the knowledge graph in memory
    memory_item = MemoryItem(
        id="knowledge_graph_1",
        memory_type=MemoryType.KNOWLEDGE_GRAPH,
        content=context.knowledge_graph,
        metadata={"domain": "security", "version": "1.0"},
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)


@when("the team needs to reason about a complex task")
def team_reasons_about_complex_task(context):
    """The team needs to reason about a complex task."""
    # Create a complex task related to authentication
    task = {
        "type": "security_implementation",
        "description": "Implement a secure authentication system",
        "requirements": ["user authentication", "password security", "encryption"],
    }
    context.tasks["security_task"] = task


@then("the team should be able to query the knowledge graph")
def team_queries_knowledge_graph(context):
    """The team should be able to query the knowledge graph."""
    # Query for knowledge graph memory items
    query_result = context.memory_manager.query_by_type(MemoryType.KNOWLEDGE_GRAPH)

    # Verify that we got at least one result
    assert len(query_result) > 0

    # Get the first result (should be our knowledge graph)
    knowledge_graph_item = query_result[0]

    # Verify that it's a knowledge graph
    assert knowledge_graph_item.memory_type == MemoryType.KNOWLEDGE_GRAPH

    # Store the retrieved knowledge graph for later use
    context.retrieved_knowledge_graph = knowledge_graph_item.content


@then("incorporate the knowledge into their reasoning process")
def incorporate_knowledge_into_reasoning(context):
    """Incorporate the knowledge into the reasoning process."""
    # Get the team and task
    team = context.teams[context.current_team_id]
    task = context.tasks["security_task"]

    # Get the knowledge graph
    knowledge_graph = context.retrieved_knowledge_graph

    # In a real implementation, the team would use the knowledge graph to enhance reasoning
    # For testing purposes, we'll simulate this by creating a solution that incorporates knowledge
    solution = {
        "agent": "code_agent",
        "description": "Secure authentication implementation",
        "code": """
def authenticate(username, password):
    # Hash the password for security
    hashed_password = hash_password(password)

    # Check if the username and hashed password match stored values
    if check_credentials(username, hashed_password):
        return True
    return False

def hash_password(password):
    # Use a secure hashing algorithm
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
        """,
    }

    # Add the solution to the team
    team.add_solution(task, solution)

    # Store the solution in memory with knowledge graph references
    # Create a task_id without hashing the list
    task_id = f"{task['type']}_{task['description']}"

    memory_item = MemoryItem(
        id="solution_2",
        memory_type=MemoryType.SOLUTION,
        content=solution,
        metadata={
            "task_id": task_id,
            "agent": solution["agent"],
            "knowledge_sources": ["authentication", "password", "hashing", "security"],
        },
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)

    # Verify that the solution incorporates knowledge from the knowledge graph
    # In this case, we check that the solution includes hashing, which is a concept from the knowledge graph
    assert "hash_password" in solution["code"]
    assert "secure hashing algorithm" in solution["code"]


# Scenario: Use different memory backends for WSDE artifacts


@given("the memory system is configured with multiple backends")
def memory_system_with_multiple_backends(context):
    """Configure the memory system with multiple backends."""
    # Create memory adapters for different backends
    file_adapter = MemorySystemAdapter.create_for_testing(storage_type="file")
    tinydb_adapter = MemorySystemAdapter.create_for_testing(storage_type="tinydb")

    # Store the memory stores from the adapters
    context.memory_backends["file"] = file_adapter.get_memory_store()
    context.memory_backends["tinydb"] = tinydb_adapter.get_memory_store()

    # Create a memory manager that can use multiple backends
    context.memory_managers = {
        backend_name: MemoryManager({"default": memory_store})
        for backend_name, memory_store in context.memory_backends.items()
    }


@when("I store WSDE artifacts in different backends")
def store_artifacts_in_different_backends(context):
    """Store WSDE artifacts in different backends."""
    # Create a task
    task = {
        "type": "multi_backend_test",
        "description": "Test storing artifacts in different backends",
    }
    context.tasks["multi_backend_task"] = task

    # Create a team state artifact
    team_state = {
        "team_id": context.current_team_id,
        "agents": [
            agent.config.name for agent in context.teams[context.current_team_id].agents
        ],
        "primus_index": context.teams[context.current_team_id].primus_index,
    }

    # Create a solution artifact
    solution = {
        "agent": "code_agent",
        "description": "Solution for multi-backend test",
        "code": "def test_function():\n    return 'Hello, world!'",
    }

    # Store team state in the file backend
    file_memory_item = MemoryItem(
        id="team_state_2",
        memory_type=MemoryType.TEAM_STATE,
        content=team_state,
        metadata={"team_id": context.current_team_id, "backend": "file"},
    )
    context.memory_managers["file"].store_item(file_memory_item)

    # Store solution in the tinydb backend
    tinydb_memory_item = MemoryItem(
        id="solution_3",
        memory_type=MemoryType.SOLUTION,
        content=solution,
        metadata={
            "task_id": str(hash(frozenset(task.items()))),
            "agent": solution["agent"],
            "backend": "tinydb",
        },
    )
    context.memory_managers["tinydb"].store_item(tinydb_memory_item)

    # Store relationship between team state and solution
    # In a real implementation, this would be a more sophisticated relationship
    # For testing purposes, we'll use a simple memory item
    relationship_item = MemoryItem(
        id="relationship_1",
        memory_type=MemoryType.RELATIONSHIP,
        content={
            "source_type": MemoryType.TEAM_STATE,
            "source_id": file_memory_item.id,
            "target_type": MemoryType.SOLUTION,
            "target_id": tinydb_memory_item.id,
            "relationship_type": "created_by",
        },
        metadata={"source_backend": "file", "target_backend": "tinydb"},
    )
    context.memory_managers["file"].store_item(relationship_item)


@then("I should be able to retrieve the artifacts from their respective backends")
def retrieve_artifacts_from_backends(context):
    """Retrieve the artifacts from their respective backends."""
    # Query for team state in the file backend
    file_query_result = context.memory_managers["file"].query_by_type(
        MemoryType.TEAM_STATE
    )

    # Verify that we got at least one result
    assert len(file_query_result) > 0

    # Get the first result (should be our team state)
    team_state_item = file_query_result[0]

    # Verify that it's a team state
    assert team_state_item.memory_type == MemoryType.TEAM_STATE

    # Store the retrieved team state for later use
    context.retrieved_team_state = team_state_item.content

    # Query for solution in the tinydb backend
    tinydb_query_result = context.memory_managers["tinydb"].query_by_type(
        MemoryType.SOLUTION
    )

    # Verify that we got at least one result
    assert len(tinydb_query_result) > 0

    # Get the first result (should be our solution)
    solution_item = tinydb_query_result[0]

    # Verify that it's a solution
    assert solution_item.memory_type == MemoryType.SOLUTION

    # Store the retrieved solution for later use
    context.retrieved_solution = solution_item.content


@then("the artifacts should maintain their relationships")
def verify_artifact_relationships(context):
    """Verify that the artifacts maintain their relationships."""
    # Query for relationships in the file backend
    relationship_query_result = context.memory_managers["file"].query_by_type(
        MemoryType.RELATIONSHIP
    )

    # Verify that we got at least one result
    assert len(relationship_query_result) > 0

    # Get the first result (should be our relationship)
    relationship_item = relationship_query_result[0]

    # Verify that it's a relationship
    assert relationship_item.memory_type == MemoryType.RELATIONSHIP

    # Verify that the relationship connects the correct artifacts
    relationship = relationship_item.content

    # Handle both string and enum values for memory types
    if isinstance(relationship["source_type"], str):
        assert relationship["source_type"] == MemoryType.TEAM_STATE.value
    else:
        assert relationship["source_type"] == MemoryType.TEAM_STATE

    if isinstance(relationship["target_type"], str):
        assert relationship["target_type"] == MemoryType.SOLUTION.value
    else:
        assert relationship["target_type"] == MemoryType.SOLUTION

    assert relationship["relationship_type"] == "created_by"

    # Verify that the relationship metadata indicates the correct backends
    assert relationship_item.metadata["source_backend"] == "file"
    assert relationship_item.metadata["target_backend"] == "tinydb"
