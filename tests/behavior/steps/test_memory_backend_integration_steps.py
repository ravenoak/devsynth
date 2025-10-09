"""
Step Definitions for Memory Backend Integration BDD Tests

This file implements the step definitions for the memory backend integration
feature file, testing all available memory backends with the WSDE model.
"""

import logging
import os
import time

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from tests.behavior.feature_paths import feature_path

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("chromadb"),
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("faiss"),
]

chromadb_enabled = os.environ.get("ENABLE_CHROMADB", "false").lower() not in {
    "0",
    "false",
    "no",
}
if not chromadb_enabled:
    pytest.skip("ChromaDB feature not enabled", allow_module_level=True)


logger = logging.getLogger(__name__)

scenarios(feature_path(__file__, "general", "memory_backend_integration.feature"))


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
            self.memory_managers = {}
            self.current_team_id = None
            self.original_team_state = None
            self.original_solution = None
            self.original_dialectical_result = None
            self.retrieved_team_state = None
            self.retrieved_solution = None
            self.retrieved_dialectical_result = None
            self.memory_backends = {}
            self.performance_metrics = {}
            self.all_backends = [
                "memory",
                "file",
                "tinydb",
                "chromadb",
                "duckdb",
                "faiss",
                "json",
                "lmdb",
                "rdflib",
            ]

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


# Scenario Outline: Store and retrieve WSDE artifacts in different memory backends


@given(parsers.parse('the memory system is configured with a "{backend_type}" backend'))
def memory_system_configured_with_backend(context, backend_type):
    """Configure the memory system with the specified backend type."""
    # Create a memory system adapter with the specified backend
    try:
        context.memory_adapter = MemorySystemAdapter.create_for_testing(
            storage_type=backend_type
        )

        # Create a memory manager that uses the memory store from the adapter
        context.memory_manager = MemoryManager(
            {"default": context.memory_adapter.get_memory_store()}
        )

        # Store the backend type for later reference
        context.current_backend_type = backend_type
    except Exception as e:
        pytest.skip(f"Backend {backend_type} not available: {str(e)}")


@when("I store a WSDE team state in the memory backend")
def store_team_state_in_backend(context):
    """Store a WSDE team state in the memory backend."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Create a team state
    context.original_team_state = {
        "team_id": context.current_team_id,
        "agents": [agent.config.name for agent in team.agents],
        "primus_index": team.primus_index,
    }

    # Create a memory item for the team state
    memory_item = MemoryItem(
        id=f"team_state_{context.current_backend_type}",
        memory_type=MemoryType.TEAM_STATE,
        content=context.original_team_state,
        metadata={
            "team_id": context.current_team_id,
            "backend": context.current_backend_type,
        },
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)


@when("I store a solution in the memory backend")
def store_solution_in_backend(context):
    """Store a solution in the memory backend."""
    # Create a task
    task = {
        "type": "backend_test",
        "description": f"Test {context.current_backend_type} backend",
    }
    context.tasks[f"{context.current_backend_type}_task"] = task

    # Create a solution
    context.original_solution = {
        "agent": "code_agent",
        "content": f"def test_{context.current_backend_type}():\n    return '{context.current_backend_type} works!'",
        "description": f"Test solution for {context.current_backend_type} backend",
    }

    # Create a memory item for the solution
    memory_item = MemoryItem(
        id=f"solution_{context.current_backend_type}",
        memory_type=MemoryType.SOLUTION,
        content=context.original_solution,
        metadata={
            "task_id": str(hash(frozenset(task.items()))),
            "agent": context.original_solution["agent"],
            "backend": context.current_backend_type,
        },
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)


@when("I store a dialectical reasoning result in the memory backend")
def store_dialectical_result_in_backend(context):
    """Store a dialectical reasoning result in the memory backend."""
    # Create a dialectical reasoning result
    context.original_dialectical_result = {
        "thesis": {
            "content": f"Initial solution for {context.current_backend_type} backend",
            "agent": "code_agent",
        },
        "antithesis": {
            "content": f"Critique of solution for {context.current_backend_type} backend",
            "agent": "critic_agent",
        },
        "synthesis": {
            "content": f"Improved solution for {context.current_backend_type} backend",
            "agent": "orchestrator_agent",
        },
    }

    # Create a memory item for the dialectical result
    memory_item = MemoryItem(
        id=f"dialectical_{context.current_backend_type}",
        memory_type=MemoryType.DIALECTICAL_REASONING,
        content=context.original_dialectical_result,
        metadata={
            "task_id": str(
                hash(
                    frozenset(
                        context.tasks[f"{context.current_backend_type}_task"].items()
                    )
                )
            ),
            "backend": context.current_backend_type,
        },
    )

    # Store the memory item
    context.memory_manager.store_item(memory_item)


@then("I should be able to retrieve the team state from the memory backend")
def retrieve_team_state_from_backend(context):
    """Retrieve the team state from the memory backend."""
    # Query for team state memory items
    query_result = context.memory_manager.query_by_type(MemoryType.TEAM_STATE)

    # Verify that we got at least one result
    assert len(query_result) > 0

    # Get the first result (should be our team state)
    team_state_item = query_result[0]

    # Store the retrieved team state for later comparison
    context.retrieved_team_state = team_state_item.content


@then("I should be able to retrieve the solution from the memory backend")
def retrieve_solution_from_backend(context):
    """Retrieve the solution from the memory backend."""
    # Query for solution memory items
    query_result = context.memory_manager.query_by_type(MemoryType.SOLUTION)

    # Verify that we got at least one result
    assert len(query_result) > 0

    # Get the first result (should be our solution)
    solution_item = query_result[0]

    # Store the retrieved solution for later comparison
    context.retrieved_solution = solution_item.content


@then(
    "I should be able to retrieve the dialectical reasoning result from the memory backend"
)
def retrieve_dialectical_result_from_backend(context):
    """Retrieve the dialectical reasoning result from the memory backend."""
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


@then("all retrieved artifacts should match their original versions")
def verify_artifacts_match_originals(context):
    """Verify that all retrieved artifacts match their original versions."""
    # Verify team state
    assert context.retrieved_team_state is not None
    assert context.original_team_state is not None
    assert (
        context.retrieved_team_state["team_id"]
        == context.original_team_state["team_id"]
    )
    assert set(context.retrieved_team_state["agents"]) == set(
        context.original_team_state["agents"]
    )
    assert (
        context.retrieved_team_state["primus_index"]
        == context.original_team_state["primus_index"]
    )

    # Verify solution
    assert context.retrieved_solution is not None
    assert context.original_solution is not None
    assert context.retrieved_solution["agent"] == context.original_solution["agent"]
    assert context.retrieved_solution["content"] == context.original_solution["content"]
    assert (
        context.retrieved_solution["description"]
        == context.original_solution["description"]
    )

    # Verify dialectical result
    assert context.retrieved_dialectical_result is not None
    assert context.original_dialectical_result is not None
    assert (
        context.retrieved_dialectical_result["thesis"]["content"]
        == context.original_dialectical_result["thesis"]["content"]
    )
    assert (
        context.retrieved_dialectical_result["antithesis"]["content"]
        == context.original_dialectical_result["antithesis"]["content"]
    )
    assert (
        context.retrieved_dialectical_result["synthesis"]["content"]
        == context.original_dialectical_result["synthesis"]["content"]
    )


# Scenario: Cross-backend relationships between WSDE artifacts


@given("the memory system is configured with multiple backends")
def memory_system_with_multiple_backends(context):
    """Configure the memory system with multiple backends."""
    # Create memory adapters for different backends
    try:
        # Try to create adapters for file, tinydb, and chromadb
        file_adapter = MemorySystemAdapter.create_for_testing(storage_type="file")
        tinydb_adapter = MemorySystemAdapter.create_for_testing(storage_type="tinydb")
        chromadb_adapter = MemorySystemAdapter.create_for_testing(
            storage_type="chromadb"
        )

        # Store the memory stores from the adapters
        context.memory_backends["file"] = file_adapter.get_memory_store()
        context.memory_backends["tinydb"] = tinydb_adapter.get_memory_store()
        context.memory_backends["chromadb"] = chromadb_adapter.get_memory_store()

        # Create memory managers for each backend
        context.memory_managers = {
            backend_name: MemoryManager({"default": memory_store})
            for backend_name, memory_store in context.memory_backends.items()
        }
    except Exception as e:
        pytest.skip(f"One or more required backends not available: {str(e)}")


@when(parsers.parse('I store team state in the "{backend_name}" backend'))
def store_team_state_in_named_backend(context, backend_name):
    """Store team state in the specified backend."""
    # Get the team
    team = context.teams[context.current_team_id]

    # Create a team state
    team_state = {
        "team_id": context.current_team_id,
        "agents": [agent.config.name for agent in team.agents],
        "primus_index": team.primus_index,
    }

    # Store the original team state for later comparison
    context.original_team_state = team_state

    # Create a memory item for the team state
    memory_item = MemoryItem(
        id=f"team_state_{backend_name}",
        memory_type=MemoryType.TEAM_STATE,
        content=team_state,
        metadata={"team_id": context.current_team_id, "backend": backend_name},
    )

    # Store the memory item in the specified backend
    context.memory_managers[backend_name].store_item(memory_item)


@when(parsers.parse('I store a solution in the "{backend_name}" backend'))
def store_solution_in_named_backend(context, backend_name):
    """Store a solution in the specified backend."""
    # Create a task
    task = {
        "type": "cross_backend_test",
        "description": "Test cross-backend relationships",
    }
    context.tasks["cross_backend_task"] = task

    # Create a solution
    solution = {
        "agent": "code_agent",
        "content": f"def test_cross_backend():\n    return '{backend_name} works!'",
        "description": f"Test solution for cross-backend test in {backend_name}",
    }

    # Store the original solution for later comparison
    context.original_solution = solution

    # Create a memory item for the solution
    memory_item = MemoryItem(
        id=f"solution_{backend_name}",
        memory_type=MemoryType.SOLUTION,
        content=solution,
        metadata={
            "task_id": str(hash(frozenset(task.items()))),
            "agent": solution["agent"],
            "backend": backend_name,
        },
    )

    # Store the memory item in the specified backend
    context.memory_managers[backend_name].store_item(memory_item)


@when(
    parsers.parse(
        'I store a dialectical reasoning result in the "{backend_name}" backend'
    )
)
def store_dialectical_result_in_named_backend(context, backend_name):
    """Store a dialectical reasoning result in the specified backend."""
    # Create a dialectical reasoning result
    dialectical_result = {
        "thesis": {
            "content": f"Initial solution for cross-backend test in {backend_name}",
            "agent": "code_agent",
        },
        "antithesis": {
            "content": f"Critique of solution for cross-backend test in {backend_name}",
            "agent": "critic_agent",
        },
        "synthesis": {
            "content": f"Improved solution for cross-backend test in {backend_name}",
            "agent": "orchestrator_agent",
        },
    }

    # Store the original dialectical result for later comparison
    context.original_dialectical_result = dialectical_result

    # Create a memory item for the dialectical result
    memory_item = MemoryItem(
        id=f"dialectical_{backend_name}",
        memory_type=MemoryType.DIALECTICAL_REASONING,
        content=dialectical_result,
        metadata={
            "task_id": str(
                hash(frozenset(context.tasks["cross_backend_task"].items()))
            ),
            "backend": backend_name,
        },
    )

    # Store the memory item in the specified backend
    context.memory_managers[backend_name].store_item(memory_item)


@when("I create relationships between these artifacts")
def create_relationships_between_artifacts(context):
    """Create relationships between artifacts in different backends."""
    # Create relationships between team state, solution, and dialectical result
    # Team state (file) -> Solution (tinydb)
    team_to_solution_relationship = MemoryItem(
        id="relationship_team_to_solution",
        memory_type=MemoryType.RELATIONSHIP,
        content={
            "source_type": MemoryType.TEAM_STATE,
            "source_id": "team_state_file",
            "target_type": MemoryType.SOLUTION,
            "target_id": "solution_tinydb",
            "relationship_type": "created_by",
        },
        metadata={"source_backend": "file", "target_backend": "tinydb"},
    )

    # Solution (tinydb) -> Dialectical result (chromadb)
    solution_to_dialectical_relationship = MemoryItem(
        id="relationship_solution_to_dialectical",
        memory_type=MemoryType.RELATIONSHIP,
        content={
            "source_type": MemoryType.SOLUTION,
            "source_id": "solution_tinydb",
            "target_type": MemoryType.DIALECTICAL_REASONING,
            "target_id": "dialectical_chromadb",
            "relationship_type": "evaluated_by",
        },
        metadata={"source_backend": "tinydb", "target_backend": "chromadb"},
    )

    # Store the relationships in a common backend (file)
    context.memory_managers["file"].store_item(team_to_solution_relationship)
    context.memory_managers["file"].store_item(solution_to_dialectical_relationship)


@then("I should be able to retrieve all artifacts from their respective backends")
def retrieve_all_artifacts_from_backends(context):
    """Retrieve all artifacts from their respective backends."""
    # Retrieve team state from file backend
    file_query_result = context.memory_managers["file"].query_by_type(
        MemoryType.TEAM_STATE
    )
    assert len(file_query_result) > 0
    context.retrieved_team_state = file_query_result[0].content

    # Retrieve solution from tinydb backend
    tinydb_query_result = context.memory_managers["tinydb"].query_by_type(
        MemoryType.SOLUTION
    )
    assert len(tinydb_query_result) > 0
    context.retrieved_solution = tinydb_query_result[0].content

    # Retrieve dialectical result from chromadb backend
    chromadb_query_result = context.memory_managers["chromadb"].query_by_type(
        MemoryType.DIALECTICAL_REASONING
    )
    assert len(chromadb_query_result) > 0
    context.retrieved_dialectical_result = chromadb_query_result[0].content


@then(
    "I should be able to traverse relationships between artifacts in different backends"
)
def traverse_relationships_between_artifacts(context):
    """Traverse relationships between artifacts in different backends."""
    # Query for relationships in the file backend
    relationship_query_result = context.memory_managers["file"].query_by_type(
        MemoryType.RELATIONSHIP
    )

    # Verify that we got at least two results (our two relationships)
    assert len(relationship_query_result) >= 2

    # Find the team_to_solution relationship
    team_to_solution = None
    for item in relationship_query_result:
        if item.id == "relationship_team_to_solution":
            team_to_solution = item.content
            break

    assert team_to_solution is not None
    assert team_to_solution["source_type"] == MemoryType.TEAM_STATE
    assert team_to_solution["source_id"] == "team_state_file"
    assert team_to_solution["target_type"] == MemoryType.SOLUTION
    assert team_to_solution["target_id"] == "solution_tinydb"

    # Find the solution_to_dialectical relationship
    solution_to_dialectical = None
    for item in relationship_query_result:
        if item.id == "relationship_solution_to_dialectical":
            solution_to_dialectical = item.content
            break

    assert solution_to_dialectical is not None
    assert solution_to_dialectical["source_type"] == MemoryType.SOLUTION
    assert solution_to_dialectical["source_id"] == "solution_tinydb"
    assert solution_to_dialectical["target_type"] == MemoryType.DIALECTICAL_REASONING
    assert solution_to_dialectical["target_id"] == "dialectical_chromadb"


@then(
    "the relationship metadata should correctly identify the source and target backends"
)
def verify_relationship_metadata(context):
    """Verify that relationship metadata correctly identifies source and target backends."""
    # Query for relationships in the file backend
    relationship_query_result = context.memory_managers["file"].query_by_type(
        MemoryType.RELATIONSHIP
    )

    # Find the team_to_solution relationship
    team_to_solution = None
    for item in relationship_query_result:
        if item.id == "relationship_team_to_solution":
            team_to_solution = item
            break

    assert team_to_solution is not None
    assert team_to_solution.metadata["source_backend"] == "file"
    assert team_to_solution.metadata["target_backend"] == "tinydb"

    # Find the solution_to_dialectical relationship
    solution_to_dialectical = None
    for item in relationship_query_result:
        if item.id == "relationship_solution_to_dialectical":
            solution_to_dialectical = item
            break

    assert solution_to_dialectical is not None
    assert solution_to_dialectical.metadata["source_backend"] == "tinydb"
    assert solution_to_dialectical.metadata["target_backend"] == "chromadb"


# Scenario: Memory backend performance comparison


@given("the memory system is configured with all available backends")
def memory_system_with_all_backends(context):
    """Configure the memory system with all available backends."""
    # Try to create adapters for all backends
    for backend_type in context.all_backends:
        try:
            adapter = MemorySystemAdapter.create_for_testing(storage_type=backend_type)
            context.memory_backends[backend_type] = adapter.get_memory_store()
            context.memory_managers[backend_type] = MemoryManager(
                {"default": adapter.get_memory_store()}
            )
        except Exception as e:
            logger.warning("Backend %s not available: %s", backend_type, str(e))

    # Skip the test if we couldn't create at least 3 backends
    if len(context.memory_backends) < 3:
        pytest.skip("Not enough backends available for performance comparison")


@when("I perform a benchmark storing 100 memory items in each backend")
def benchmark_storing_items(context):
    """Perform a benchmark storing 100 memory items in each backend."""
    for backend_name, memory_manager in context.memory_managers.items():
        # Skip if the backend is not available
        if not memory_manager:
            continue

        # Create 100 memory items
        items = []
        for i in range(100):
            item = MemoryItem(
                id=f"benchmark_store_{backend_name}_{i}",
                memory_type=MemoryType.WORKING,
                content={"index": i, "value": f"Test value {i} for {backend_name}"},
                metadata={"backend": backend_name, "test_type": "store_benchmark"},
            )
            items.append(item)

        # Measure the time to store all items
        start_time = time.time()
        for item in items:
            memory_manager.store_item(item)
        end_time = time.time()

        # Store the performance metric
        if "store" not in context.performance_metrics:
            context.performance_metrics["store"] = {}
        context.performance_metrics["store"][backend_name] = end_time - start_time


@when("I perform a benchmark retrieving items by type from each backend")
def benchmark_retrieving_by_type(context):
    """Perform a benchmark retrieving items by type from each backend."""
    for backend_name, memory_manager in context.memory_managers.items():
        # Skip if the backend is not available
        if not memory_manager:
            continue

        # Measure the time to retrieve all items by type
        start_time = time.time()
        items = memory_manager.query_by_type(MemoryType.WORKING)
        end_time = time.time()

        # Store the performance metric
        if "retrieve_by_type" not in context.performance_metrics:
            context.performance_metrics["retrieve_by_type"] = {}
        context.performance_metrics["retrieve_by_type"][backend_name] = (
            end_time - start_time
        )


@when("I perform a benchmark retrieving items by metadata from each backend")
def benchmark_retrieving_by_metadata(context):
    """Perform a benchmark retrieving items by metadata from each backend."""
    for backend_name, memory_manager in context.memory_managers.items():
        # Skip if the backend is not available
        if not memory_manager:
            continue

        # Measure the time to retrieve all items by metadata
        start_time = time.time()
        items = memory_manager.query_by_metadata({"test_type": "store_benchmark"})
        end_time = time.time()

        # Store the performance metric
        if "retrieve_by_metadata" not in context.performance_metrics:
            context.performance_metrics["retrieve_by_metadata"] = {}
        context.performance_metrics["retrieve_by_metadata"][backend_name] = (
            end_time - start_time
        )


@then("I should get performance metrics for each backend")
def verify_performance_metrics(context):
    """Verify that we have performance metrics for each backend."""
    # Check that we have metrics for each operation
    assert "store" in context.performance_metrics
    assert "retrieve_by_type" in context.performance_metrics
    assert "retrieve_by_metadata" in context.performance_metrics

    # Check that we have metrics for each available backend
    for backend_name in context.memory_managers.keys():
        if backend_name in context.memory_backends:
            assert backend_name in context.performance_metrics["store"]
            assert backend_name in context.performance_metrics["retrieve_by_type"]
            assert backend_name in context.performance_metrics["retrieve_by_metadata"]


@then("I should be able to compare the performance of different backends")
def compare_backend_performance(context):
    """Compare the performance of different backends."""
    # For each operation, find the fastest and slowest backends
    for operation in ["store", "retrieve_by_type", "retrieve_by_metadata"]:
        metrics = context.performance_metrics[operation]
        if not metrics:
            continue

        fastest_backend = min(metrics.items(), key=lambda x: x[1])
        slowest_backend = max(metrics.items(), key=lambda x: x[1])

        logger.info("%s PERFORMANCE:", operation.upper())
        logger.info(
            "Fastest: %s (%.6f seconds)",
            fastest_backend[0],
            fastest_backend[1],
        )
        logger.info(
            "Slowest: %s (%.6f seconds)",
            slowest_backend[0],
            slowest_backend[1],
        )
        logger.info(
            "Difference: %.2fx slower",
            slowest_backend[1] / fastest_backend[1],
        )

        # Log all metrics
        logger.info("All metrics:")
        for backend, time_taken in sorted(metrics.items(), key=lambda x: x[1]):
            logger.info("%s: %.6f seconds", backend, time_taken)

    # The test passes as long as we can compare the metrics
    assert True
