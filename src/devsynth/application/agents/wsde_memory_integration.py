"""
WSDE Memory Integration module.

This module provides integration between the WSDE model and the memory system,
allowing WSDE teams to store and retrieve information from memory.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class WSDEMemoryIntegration:
    """
    Integration between WSDE teams and the memory system.

    This class provides methods for WSDE teams to store and retrieve information
    from the memory system, including dialectical processes, agent solutions, and team context.
    """

    def __init__(self, memory_adapter: MemorySystemAdapter, wsde_team: WSDETeam, 
                 agent_memory: Optional[AgentMemoryIntegration] = None):
        """
        Initialize the WSDE memory integration.

        Args:
            memory_adapter: The memory system adapter to use
            wsde_team: The WSDE team to integrate with
            agent_memory: Optional agent memory integration to use (if None, a new one will be created)
        """
        self.memory_adapter = memory_adapter
        self.wsde_team = wsde_team
        self.agent_memory = agent_memory or AgentMemoryIntegration(memory_adapter, wsde_team)
        self.context_manager = memory_adapter.get_context_manager()

        logger.info("WSDE memory integration initialized")

    def store_dialectical_process(self, task: Dict[str, Any], thesis: Dict[str, Any], 
                                 antithesis: Dict[str, Any], synthesis: Dict[str, Any]) -> str:
        """
        Store a dialectical process in memory.

        Args:
            task: The task that the dialectical process addresses
            thesis: The thesis in the dialectical process
            antithesis: The antithesis in the dialectical process
            synthesis: The synthesis in the dialectical process

        Returns:
            The ID of the stored memory item
        """
        # Use the agent memory integration to store the dialectical reasoning
        item_id = self.agent_memory.store_dialectical_reasoning(
            task["id"], thesis, antithesis, synthesis
        )

        logger.info(f"Stored dialectical process in memory with ID {item_id}")
        return item_id

    def retrieve_dialectical_process(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieve a dialectical process for a specific task from memory.

        Args:
            task_id: The ID of the task to retrieve the dialectical process for

        Returns:
            A dictionary containing the dialectical process (thesis, antithesis, synthesis)
        """
        # Use the agent memory integration to retrieve the dialectical reasoning
        reasoning_item = self.agent_memory.retrieve_dialectical_reasoning(task_id)

        if reasoning_item:
            # Parse the content as JSON
            reasoning_content = json.loads(reasoning_item.content)
            logger.info(f"Retrieved dialectical process for task {task_id}")
            return reasoning_content
        else:
            logger.info(f"No dialectical process found for task {task_id}")
            return {}

    def store_agent_solution(self, agent_id: str, task: Dict[str, Any], solution: Dict[str, Any], 
                               edrr_phase: Optional[str] = None) -> str:
        """
        Store an agent solution in memory.

        Args:
            agent_id: The ID of the agent that produced the solution
            task: The task that the solution addresses
            solution: The solution produced by the agent
            edrr_phase: Optional EDRR phase tag (e.g., "Expand", "Differentiate", "Refine", "Retrospect")

        Returns:
            The ID of the stored memory item
        """
        # Use the agent memory integration to store the solution
        item_id = self.agent_memory.store_agent_solution(agent_id, task, solution)

        # If an EDRR phase is provided, tag the memory item with it
        if edrr_phase:
            memory_store = self.memory_adapter.get_memory_store()
            memory_item = memory_store.get_item(item_id)
            if memory_item:
                # Add EDRR phase directly to metadata
                memory_item.metadata["edrr_phase"] = edrr_phase
                memory_store.update_item(memory_item)
                logger.info(f"Tagged solution {item_id} with EDRR phase: {edrr_phase}")

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
        # Use the agent memory integration to retrieve the solutions
        solutions = self.agent_memory.retrieve_agent_solutions(task_id)

        logger.info(f"Retrieved {len(solutions)} agent solutions for task {task_id}")
        return solutions

    def store_team_context(self, context_data: Dict[str, Any]) -> None:
        """
        Store team context in memory.

        Args:
            context_data: The context data to store
        """
        # Add the context to the context manager
        self.context_manager.add_to_context("wsde_team", context_data)

        logger.info("Stored team context in memory")

    def retrieve_team_context(self) -> Dict[str, Any]:
        """
        Retrieve team context from memory.

        Returns:
            The team context data
        """
        # Get the context from the context manager
        context_data = self.context_manager.get_from_context("wsde_team")

        logger.info("Retrieved team context from memory")
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
        # Use the agent memory integration to search for similar solutions
        similar_vectors = self.agent_memory.search_similar_solutions(query, top_k=top_k)

        logger.info(f"Found {len(similar_vectors)} similar solutions for query")
        return similar_vectors

    def retrieve_solutions_by_edrr_phase(self, task_id: str, edrr_phase: str) -> List[MemoryItem]:
        """
        Retrieve agent solutions for a specific task filtered by EDRR phase.

        Args:
            task_id: The ID of the task to retrieve solutions for
            edrr_phase: The EDRR phase to filter by (e.g., "Expand", "Differentiate", "Refine", "Retrospect")

        Returns:
            A list of memory items containing solutions for the task with the specified EDRR phase
        """
        # First retrieve all solutions for the task
        all_solutions = self.retrieve_agent_solutions(task_id)

        # Filter solutions by EDRR phase
        filtered_solutions = []
        for solution in all_solutions:
            # Check if the solution has the specified EDRR phase
            if solution.metadata.get("edrr_phase") == edrr_phase:
                filtered_solutions.append(solution)

        logger.info(f"Retrieved {len(filtered_solutions)} solutions with EDRR phase '{edrr_phase}' for task {task_id}")
        return filtered_solutions

    def query_knowledge_graph(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph for information.

        Args:
            query: The query to execute (can be a SPARQL query or a natural language query)
            limit: Maximum number of results to return

        Returns:
            A list of results from the knowledge graph

        Raises:
            ValueError: If the knowledge graph is not available
        """
        # Check if we have a knowledge graph-capable memory store
        memory_store = self.memory_adapter.get_memory_store()

        # Check if the memory store supports knowledge graph queries
        if hasattr(memory_store, "query_graph"):
            results = memory_store.query_graph(query, limit=limit)
            logger.info(f"Queried knowledge graph with '{query}', found {len(results)} results")
            return results
        else:
            error_msg = "Knowledge graph querying is not supported by the current memory store"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def query_related_concepts(self, concept: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph for concepts related to a given concept.

        Args:
            concept: The concept to find related concepts for
            limit: Maximum number of results to return

        Returns:
            A list of related concepts with their relationships

        Raises:
            ValueError: If the knowledge graph is not available
        """
        # Create a query to find related concepts
        query = f"""
        SELECT ?related_concept ?relationship
        WHERE {{
            ?concept ?relationship ?related_concept .
            FILTER(?concept = "{concept}")
        }}
        LIMIT {limit}
        """

        # Execute the query
        results = self.query_knowledge_graph(query, limit=limit)
        logger.info(f"Queried for concepts related to '{concept}', found {len(results)} results")
        return results

    def query_concept_relationships(self, concept1: str, concept2: str) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph for relationships between two concepts.

        Args:
            concept1: The first concept
            concept2: The second concept

        Returns:
            A list of relationships between the concepts

        Raises:
            ValueError: If the knowledge graph is not available
        """
        # Create a query to find relationships between concepts
        query = f"""
        SELECT ?relationship ?direction
        WHERE {{
            {{
                ?c1 ?relationship ?c2 .
                FILTER(?c1 = "{concept1}" && ?c2 = "{concept2}")
                BIND("outgoing" AS ?direction)
            }} UNION {{
                ?c2 ?relationship ?c1 .
                FILTER(?c1 = "{concept1}" && ?c2 = "{concept2}")
                BIND("incoming" AS ?direction)
            }}
        }}
        """

        # Execute the query
        results = self.query_knowledge_graph(query)
        logger.info(f"Queried for relationships between '{concept1}' and '{concept2}', found {len(results)} results")
        return results

    def query_by_concept_type(self, concept_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph for concepts of a specific type.

        Args:
            concept_type: The type of concepts to find
            limit: Maximum number of results to return

        Returns:
            A list of concepts of the specified type with their properties

        Raises:
            ValueError: If the knowledge graph is not available
        """
        # Create a query to find concepts by type
        query = f"""
        SELECT ?concept ?properties
        WHERE {{
            ?concept a "{concept_type}" .
            OPTIONAL {{ ?concept ?property ?value }}
            BIND(CONCAT(STR(?property), "=", STR(?value)) AS ?prop_value)
            BIND(GROUP_CONCAT(?prop_value; SEPARATOR="|") AS ?properties)
        }}
        GROUP BY ?concept
        LIMIT {limit}
        """

        # Execute the query
        results = self.query_knowledge_graph(query, limit=limit)
        logger.info(f"Queried for concepts of type '{concept_type}', found {len(results)} results")
        return results

    def query_knowledge_for_task(self, task: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph for knowledge relevant to a specific task.

        Args:
            task: The task to find relevant knowledge for
            limit: Maximum number of results to return

        Returns:
            A list of relevant concepts with their relevance scores

        Raises:
            ValueError: If the knowledge graph is not available
        """
        # Extract keywords from the task
        keywords = []
        if "description" in task:
            keywords.extend(task["description"].lower().split())
        if "requirements" in task and isinstance(task["requirements"], list):
            for req in task["requirements"]:
                if isinstance(req, str):
                    keywords.extend(req.lower().split())

        # Remove common words and duplicates
        common_words = {"a", "an", "the", "and", "or", "but", "for", "in", "on", "at", "to", "with"}
        keywords = [kw for kw in keywords if kw not in common_words]
        keywords = list(set(keywords))

        # Create a query to find relevant concepts
        keyword_filters = " || ".join([f'CONTAINS(LCASE(STR(?concept)), "{kw}")' for kw in keywords])
        query = f"""
        SELECT ?concept (COUNT(?match) AS ?relevance)
        WHERE {{
            ?concept ?property ?value .
            FILTER({keyword_filters})
            BIND(1 AS ?match)
        }}
        GROUP BY ?concept
        ORDER BY DESC(?relevance)
        LIMIT {limit}
        """

        # Execute the query
        results = self.query_knowledge_graph(query, limit=limit)
        logger.info(f"Queried for knowledge relevant to task, found {len(results)} results")
        return results
