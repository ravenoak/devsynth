"""
Agent Memory Integration module.

This module provides integration between agents and the memory system,
allowing agents to store and retrieve information from memory.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class AgentMemoryIntegration:
    """
    Integration between agents and the memory system.

    This class provides methods for agents to store and retrieve information
    from the memory system, including solutions, dialectical reasoning, and context.
    """

    def __init__(self, memory_adapter: MemorySystemAdapter, wsde_team: WSDETeam):
        """
        Initialize the agent memory integration.

        Args:
            memory_adapter: The memory system adapter to use
            wsde_team: The WSDE team to integrate with
        """
        self.memory_adapter = memory_adapter
        self.wsde_team = wsde_team
        self.memory_store = memory_adapter.get_memory_store()
        self.context_manager = memory_adapter.get_context_manager()
        self.vector_store = memory_adapter.get_vector_store() if memory_adapter.has_vector_store() else None

        logger.info("Agent memory integration initialized")

    def store_agent_solution(self, agent_id: str, task: Dict[str, Any], solution: Dict[str, Any]) -> str:
        """
        Store an agent solution in memory.

        Args:
            agent_id: The ID of the agent that produced the solution
            task: The task that the solution addresses
            solution: The solution produced by the agent

        Returns:
            The ID of the stored memory item
        """
        # Create a memory item for the solution
        solution_item = MemoryItem(
            id=str(uuid.uuid4()),
            content=json.dumps(solution),
            memory_type=MemoryType.SOLUTION,
            metadata={
                "agent_id": agent_id,
                "task_id": task["id"],
                "solution_id": solution["id"],
                "timestamp": datetime.now().isoformat()
            }
        )

        # Store the solution in memory
        item_id = self.memory_store.store(solution_item)

        logger.info(f"Stored agent solution in memory with ID {item_id}")
        return item_id

    def retrieve_agent_solutions(self, task_id: str) -> List[MemoryItem]:
        """
        Retrieve agent solutions for a specific task from memory.

        Args:
            task_id: The ID of the task to retrieve solutions for

        Returns:
            A list of memory items containing solutions for the task
        """
        # Get all solutions
        all_items = []
        for item in self.memory_store.items.values() if hasattr(self.memory_store, 'items') else []:
            if item.memory_type == MemoryType.SOLUTION and item.metadata.get("task_id") == task_id:
                all_items.append(item)

        # If the direct access approach didn't work, try using search
        if not all_items and hasattr(self.memory_store, 'search'):
            # First try with the memory type as enum
            solutions = self.memory_store.search({
                "memory_type": MemoryType.SOLUTION
            })

            # Filter by task_id in Python
            all_items = [item for item in solutions if item.metadata.get("task_id") == task_id]

            # If that didn't work, try with memory type as string
            if not all_items:
                solutions = self.memory_store.search({
                    "memory_type": MemoryType.SOLUTION.value
                })
                all_items = [item for item in solutions if item.metadata.get("task_id") == task_id]

        logger.info(f"Retrieved {len(all_items)} agent solutions for task {task_id}")
        return all_items

    def store_dialectical_reasoning(self, task_id: str, thesis: Dict[str, Any], 
                                   antithesis: Dict[str, Any], synthesis: Dict[str, Any]) -> str:
        """
        Store dialectical reasoning in memory.

        Args:
            task_id: The ID of the task that the reasoning addresses
            thesis: The thesis in the dialectical reasoning
            antithesis: The antithesis in the dialectical reasoning
            synthesis: The synthesis in the dialectical reasoning

        Returns:
            The ID of the stored memory item
        """
        # Create a memory item for the dialectical reasoning
        reasoning_content = {
            "thesis": thesis,
            "antithesis": antithesis,
            "synthesis": synthesis
        }

        reasoning_item = MemoryItem(
            id=str(uuid.uuid4()),
            content=json.dumps(reasoning_content),
            memory_type=MemoryType.DIALECTICAL_REASONING,
            metadata={
                "task_id": task_id,
                "thesis_id": thesis["id"],
                "antithesis_id": antithesis["id"],
                "synthesis_id": synthesis["id"],
                "timestamp": datetime.now().isoformat()
            }
        )

        # Store the dialectical reasoning in memory
        item_id = self.memory_store.store(reasoning_item)

        logger.info(f"Stored dialectical reasoning in memory with ID {item_id}")
        return item_id

    def retrieve_dialectical_reasoning(self, task_id: str) -> Optional[MemoryItem]:
        """
        Retrieve dialectical reasoning for a specific task from memory.

        Args:
            task_id: The ID of the task to retrieve reasoning for

        Returns:
            A memory item containing dialectical reasoning for the task, or None if not found
        """
        # Search for dialectical reasoning with the given task ID
        reasoning_items = self.memory_store.search({
            "memory_type": MemoryType.DIALECTICAL_REASONING,
            "metadata.task_id": task_id
        })

        if reasoning_items:
            logger.info(f"Retrieved dialectical reasoning for task {task_id}")
            return reasoning_items[0]
        else:
            logger.info(f"No dialectical reasoning found for task {task_id}")
            return None

    def store_agent_context(self, agent_id: str, context_data: Dict[str, Any]) -> None:
        """
        Store agent context in memory.

        Args:
            agent_id: The ID of the agent
            context_data: The context data to store
        """
        # Add the context to the context manager
        self.context_manager.add_to_context(f"agent:{agent_id}", context_data)

        logger.info(f"Stored context for agent {agent_id}")

    def retrieve_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """
        Retrieve agent context from memory.

        Args:
            agent_id: The ID of the agent

        Returns:
            The context data for the agent
        """
        # Get the context from the context manager
        context_data = self.context_manager.get_from_context(f"agent:{agent_id}")

        logger.info(f"Retrieved context for agent {agent_id}")
        return context_data

    def search_similar_solutions(self, query: str, top_k: int = 5) -> List[Any]:
        """
        Search for solutions similar to the query using vector similarity.

        Args:
            query: The query to search for
            top_k: The number of results to return

        Returns:
            A list of similar solutions
        """
        if not self.vector_store:
            logger.warning("Vector store not available for similarity search")
            return []

        # Use the vector store to search for similar solutions
        similar_vectors = self.vector_store.similarity_search(query, top_k=top_k)

        logger.info(f"Found {len(similar_vectors)} similar solutions for query")
        return similar_vectors
