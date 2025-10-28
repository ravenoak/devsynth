"""
WSDE Memory Integration module.

This module provides integration between the WSDE model and the memory system,
allowing WSDE teams to store and retrieve information from memory.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class WSDEMemoryIntegration:
    """Integration between WSDE teams and the memory system."""

    def __init__(
        self,
        memory_adapter: MemorySystemAdapter,
        wsde_team: WSDETeam,
        agent_memory: AgentMemoryIntegration | None = None,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        """Initialize the WSDE memory integration."""
        self.memory_adapter = memory_adapter
        self.wsde_team = wsde_team
        self.agent_memory = agent_memory or AgentMemoryIntegration(
            memory_adapter, wsde_team
        )
        self.context_manager = memory_adapter.get_context_manager()
        self.memory_manager = memory_manager

        logger.info("WSDE memory integration initialized")

    def store_dialectical_process(
        self,
        task: dict[str, Any],
        thesis: dict[str, Any],
        antithesis: dict[str, Any],
        synthesis: dict[str, Any],
    ) -> str:
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

    def retrieve_dialectical_process(self, task_id: str) -> dict[str, Any]:
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

    def store_agent_solution(
        self,
        agent_id: str,
        task: dict[str, Any],
        solution: dict[str, Any],
        edrr_phase: str | None = None,
    ) -> str:
        """Store an agent solution in memory."""

        if self.memory_manager is not None:
            # Build a memory item for the solution and sync across stores
            item = MemoryItem(
                id=str(uuid.uuid4()),
                content=solution,
                memory_type=MemoryType.SOLUTION,
                metadata={
                    "agent_id": agent_id,
                    "task_id": task["id"],
                    "solution_id": solution["id"],
                    "timestamp": datetime.now().isoformat(),
                },
            )
            if edrr_phase:
                item.metadata["edrr_phase"] = edrr_phase

            try:
                from devsynth.application.collaboration.collaboration_memory_utils import (
                    store_collaboration_entity,
                )

                store_collaboration_entity(
                    self.memory_manager,
                    solution,
                    primary_store="tinydb",
                    memory_item=item,
                )
                if hasattr(self.memory_manager, "flush_updates"):
                    self.memory_manager.flush_updates()
            except Exception as e:
                logger.error(f"Failed to store solution with cross-store sync: {e}")
            return item.id

        # Fallback to simple storage if no memory manager
        item_id = self.agent_memory.store_agent_solution(agent_id, task, solution)

        if edrr_phase:
            logger.info(f"Including EDRR phase '{edrr_phase}' in solution metadata")
            memory_store = self.memory_adapter.get_memory_store()
            stored_item = memory_store.get_item(item_id)
            if stored_item:
                stored_item.metadata["edrr_phase"] = edrr_phase
                memory_store.update_item(stored_item)
                if hasattr(memory_store, "flush"):
                    try:
                        memory_store.flush()
                    except Exception:
                        logger.debug("Memory store flush failed", exc_info=True)

        logger.info(f"Stored agent solution in memory with ID {item_id}")
        return item_id

    def retrieve_agent_solutions(self, task_id: str) -> list[MemoryItem]:
        """
        Retrieve agent solutions for a specific task from memory.

        Args:
            task_id: The ID of the task to retrieve solutions for

        Returns:
            A list of memory items containing solutions for the task
        """
        # If a memory manager is available, query all registered stores
        if self.memory_manager is not None:
            results: list[MemoryItem] = []
            for adapter in self.memory_manager.adapters.values():
                store = adapter
                if hasattr(adapter, "get_memory_store"):
                    store = adapter.get_memory_store()  # type: ignore[assignment]

                items: list[MemoryItem] = []
                if hasattr(store, "items"):
                    items = list(store.items.values())  # type: ignore[assignment]
                elif hasattr(store, "search"):
                    items = []
                    query_variants = [
                        {"type": MemoryType.SOLUTION},
                        {"type": MemoryType.SOLUTION.value},
                        {"memory_type": MemoryType.SOLUTION},
                        {"memory_type": MemoryType.SOLUTION.value},
                    ]
                    for query in query_variants:
                        try:
                            items = store.search(query)
                            if items:
                                break
                        except Exception:
                            continue
                for item in items:
                    if (
                        item.memory_type == MemoryType.SOLUTION
                        and item.metadata.get("task_id") == task_id
                    ):
                        results.append(item)
            logger.info(
                f"Retrieved {len(results)} agent solutions for task {task_id} across stores"
            )
            return results

        # Fallback to agent-level retrieval
        solutions = self.agent_memory.retrieve_agent_solutions(task_id)
        logger.info(f"Retrieved {len(solutions)} agent solutions for task {task_id}")
        return solutions

    def store_team_context(self, context_data: dict[str, Any]) -> None:
        """
        Store team context in memory.

        Args:
            context_data: The context data to store
        """
        # Add the context to the context manager
        self.context_manager.add_to_context("wsde_team", context_data)

        logger.info("Stored team context in memory")

    def retrieve_team_context(self) -> dict[str, Any]:
        """
        Retrieve team context from memory.

        Returns:
            The team context data
        """
        # Get the context from the context manager
        context_data = self.context_manager.get_from_context("wsde_team")

        logger.info("Retrieved team context from memory")
        return context_data

    def search_similar_solutions(self, query: str, top_k: int = 5) -> list[Any]:
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

    def retrieve_solutions_by_edrr_phase(
        self, task_id: str, edrr_phase: str
    ) -> list[MemoryItem]:
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
        filtered_solutions = [
            sol for sol in all_solutions if sol.metadata.get("edrr_phase") == edrr_phase
        ]

        logger.info(
            f"Retrieved {len(filtered_solutions)} solutions with EDRR phase '{edrr_phase}' for task {task_id}"
        )
        return filtered_solutions

    def query_knowledge_graph(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
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
            logger.info(
                f"Queried knowledge graph with '{query}', found {len(results)} results"
            )
            return results
        else:
            error_msg = (
                "Knowledge graph querying is not supported by the current memory store"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

    def query_related_concepts(
        self, concept: str, limit: int = 10
    ) -> list[dict[str, Any]]:
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
        logger.info(
            f"Queried for concepts related to '{concept}', found {len(results)} results"
        )
        return results

    def query_concept_relationships(
        self, concept1: str, concept2: str
    ) -> list[dict[str, Any]]:
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
        logger.info(
            f"Queried for relationships between '{concept1}' and '{concept2}', found {len(results)} results"
        )
        return results

    def query_by_concept_type(
        self, concept_type: str, limit: int = 10
    ) -> list[dict[str, Any]]:
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
        logger.info(
            f"Queried for concepts of type '{concept_type}', found {len(results)} results"
        )
        return results

    def query_knowledge_for_task(
        self, task: dict[str, Any], limit: int = 10
    ) -> list[dict[str, Any]]:
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
        common_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "for",
            "in",
            "on",
            "at",
            "to",
            "with",
        }
        keywords = [kw for kw in keywords if kw not in common_words]
        keywords = list(set(keywords))

        # Create a query to find relevant concepts
        keyword_filters = " || ".join(
            [f'CONTAINS(LCASE(STR(?concept)), "{kw}")' for kw in keywords]
        )
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
        logger.info(
            f"Queried for knowledge relevant to task, found {len(results)} results"
        )
        return results

    def integrate_knowledge_from_dialectical_process(
        self, task_id: str, dialectical_process: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract key insights from a dialectical process and integrate them into the team's memory system.

        This method implements the knowledge integration requirements from the dialectical process:
        1. Extract key insights from the dialectical process
        2. Store the knowledge in the team's memory system
        3. Categorize the knowledge by domain and relevance
        4. Make the integrated knowledge available for future tasks

        Args:
            task_id: The ID of the task associated with the dialectical process
            dialectical_process: The dialectical process containing thesis, antithesis, and synthesis

        Returns:
            A dictionary containing the integrated knowledge with categorization and metadata
        """
        logger.info(
            f"Integrating knowledge from dialectical process for task {task_id}"
        )

        # Extract components from the dialectical process
        thesis = dialectical_process.get("thesis", {})
        antithesis = dialectical_process.get("antithesis", {})
        synthesis = dialectical_process.get("synthesis", {})
        evaluation = dialectical_process.get("evaluation", {})

        # Initialize the integrated knowledge structure
        integrated_knowledge = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "key_insights": [],
            "domain_categories": {},
            "relevance_scores": {},
            "knowledge_graph_entries": [],
        }

        # Extract key insights from the synthesis
        if "improvements" in synthesis:
            integrated_knowledge["key_insights"].extend(synthesis["improvements"])

        if "addressed_critiques" in synthesis:
            for category, critiques in synthesis["addressed_critiques"].items():
                if category not in integrated_knowledge["domain_categories"]:
                    integrated_knowledge["domain_categories"][category] = []
                integrated_knowledge["domain_categories"][category].extend(critiques)

        # Extract insights from the evaluation
        if "strengths" in evaluation:
            integrated_knowledge["key_insights"].extend(
                [f"Strength: {strength}" for strength in evaluation["strengths"]]
            )

        if "weaknesses" in evaluation:
            integrated_knowledge["key_insights"].extend(
                [
                    f"Area for improvement: {weakness}"
                    for weakness in evaluation["weaknesses"]
                ]
            )

        # Extract insights from the antithesis
        if "critique" in antithesis and isinstance(antithesis["critique"], list):
            for critique in antithesis["critique"]:
                # Categorize the critique by domain
                domain = self._categorize_insight_by_domain(critique)
                if domain not in integrated_knowledge["domain_categories"]:
                    integrated_knowledge["domain_categories"][domain] = []
                integrated_knowledge["domain_categories"][domain].append(critique)

                # Assign relevance score based on whether it was addressed in the synthesis
                relevance = self._calculate_insight_relevance(critique, synthesis)
                integrated_knowledge["relevance_scores"][critique] = relevance

        # Prepare knowledge graph entries
        for insight in integrated_knowledge["key_insights"]:
            # Create a knowledge graph entry for each key insight
            entry = {
                "concept": f"insight:{task_id}:{uuid.uuid4()}",
                "properties": {
                    "text": insight,
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                    "source": "dialectical_process",
                },
                "relationships": [],
            }

            # Add domain categorization as a relationship
            domain = self._categorize_insight_by_domain(insight)
            entry["relationships"].append(
                {"type": "categorized_as", "target": f"domain:{domain}"}
            )

            # Add relevance as a property
            relevance = integrated_knowledge["relevance_scores"].get(insight, 0.5)
            entry["properties"]["relevance"] = relevance

            integrated_knowledge["knowledge_graph_entries"].append(entry)

        # Store the integrated knowledge in the memory system
        self._store_integrated_knowledge(integrated_knowledge)

        logger.info(
            f"Successfully integrated {len(integrated_knowledge['key_insights'])} insights from dialectical process"
        )
        return integrated_knowledge

    def _categorize_insight_by_domain(self, insight: str) -> str:
        """
        Categorize an insight by domain based on its content.

        Args:
            insight: The insight text to categorize

        Returns:
            The domain category for the insight
        """
        # Convert insight to lowercase for case-insensitive matching
        insight_lower = insight.lower() if isinstance(insight, str) else ""

        # Define domain keywords for categorization
        domain_keywords = {
            "security": [
                "security",
                "authentication",
                "authorization",
                "vulnerability",
                "exploit",
                "password",
                "encryption",
                "csrf",
                "xss",
            ],
            "performance": [
                "performance",
                "speed",
                "latency",
                "throughput",
                "optimization",
                "efficient",
                "slow",
                "fast",
                "bottleneck",
            ],
            "maintainability": [
                "maintainability",
                "readability",
                "documentation",
                "comment",
                "structure",
                "organization",
                "clean",
                "technical debt",
            ],
            "reliability": [
                "reliability",
                "error handling",
                "exception",
                "fault tolerance",
                "recovery",
                "robustness",
                "stability",
            ],
            "usability": [
                "usability",
                "user experience",
                "ux",
                "interface",
                "accessibility",
                "intuitive",
                "user-friendly",
            ],
            "scalability": [
                "scalability",
                "scale",
                "load",
                "concurrent",
                "distributed",
                "horizontal",
                "vertical",
            ],
            "testability": [
                "testability",
                "test",
                "mock",
                "stub",
                "assertion",
                "coverage",
                "unit test",
                "integration test",
            ],
        }

        # Check each domain for keyword matches
        for domain, keywords in domain_keywords.items():
            if any(keyword in insight_lower for keyword in keywords):
                return domain

        # Default domain if no matches found
        return "general"

    def _calculate_insight_relevance(
        self, insight: str, synthesis: dict[str, Any]
    ) -> float:
        """
        Calculate the relevance score of an insight based on whether it was addressed in the synthesis.

        Args:
            insight: The insight text to evaluate
            synthesis: The synthesis from the dialectical process

        Returns:
            A relevance score between 0.0 and 1.0
        """
        # Default medium relevance
        relevance = 0.5

        # Check if the insight was explicitly addressed in the synthesis
        if "addressed_critiques" in synthesis:
            for category, critiques in synthesis["addressed_critiques"].items():
                if any(insight in critique for critique in critiques):
                    relevance = 0.9
                    break

        # Check if the insight is mentioned in the improvements
        if "improvements" in synthesis:
            if any(insight in improvement for improvement in synthesis["improvements"]):
                relevance = 0.8

        # Check if the insight is mentioned in the synthesis content
        if "content" in synthesis:
            insight_words = set(insight.lower().split())
            content_words = set(synthesis["content"].lower().split())
            word_overlap = (
                len(insight_words.intersection(content_words)) / len(insight_words)
                if insight_words
                else 0
            )
            if word_overlap > 0.5:
                relevance = max(relevance, 0.7)

        return relevance

    def _store_integrated_knowledge(self, integrated_knowledge: dict[str, Any]) -> None:
        """
        Store the integrated knowledge in the memory system.

        Args:
            integrated_knowledge: The integrated knowledge to store
        """
        # Create a memory item for the integrated knowledge
        knowledge_item = MemoryItem(
            id=str(uuid.uuid4()),
            content=json.dumps(integrated_knowledge),
            memory_type=MemoryType.KNOWLEDGE,
            metadata={
                "task_id": integrated_knowledge["task_id"],
                "timestamp": integrated_knowledge["timestamp"],
                "source": "dialectical_process",
                "num_insights": len(integrated_knowledge["key_insights"]),
                "domains": list(integrated_knowledge["domain_categories"].keys()),
            },
        )

        # Store the knowledge in memory
        memory_store = self.memory_adapter.get_memory_store()
        item_id = memory_store.store(knowledge_item)

        logger.info(f"Stored integrated knowledge in memory with ID {item_id}")

        # If the memory store supports knowledge graph operations, add the entries
        if hasattr(memory_store, "add_to_graph"):
            for entry in integrated_knowledge["knowledge_graph_entries"]:
                try:
                    memory_store.add_to_graph(
                        entry["concept"], entry["properties"], entry["relationships"]
                    )
                    logger.info(
                        f"Added knowledge graph entry for concept {entry['concept']}"
                    )
                except Exception as e:
                    logger.error(f"Failed to add knowledge graph entry: {str(e)}")

    def retrieve_integrated_knowledge(self, task_id: str) -> list[dict[str, Any]]:
        """
        Retrieve integrated knowledge for a specific task from memory.

        Args:
            task_id: The ID of the task to retrieve integrated knowledge for

        Returns:
            A list of integrated knowledge items for the task
        """
        # Query the memory store for integrated knowledge
        memory_store = self.memory_adapter.get_memory_store()

        # Create a query to find integrated knowledge for the task
        query = {
            "memory_type": MemoryType.KNOWLEDGE,
            "metadata.task_id": task_id,
            "metadata.source": "dialectical_process",
        }

        # Execute the query
        results = memory_store.search(query)

        # Parse the content of each result
        knowledge_items = []
        for result in results:
            try:
                content = json.loads(result.content)
                knowledge_items.append(content)
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse integrated knowledge content for item {result.id}"
                )

        logger.info(
            f"Retrieved {len(knowledge_items)} integrated knowledge items for task {task_id}"
        )
        return knowledge_items
