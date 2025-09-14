"""
Enhanced Graph Memory Adapter for EDRR framework.

This module provides an enhanced version of the GraphMemoryAdapter that supports:
1. Context-aware memory retrieval
2. Memory persistence across cycles
3. Enhanced knowledge graph integration with transitive inference
4. Multi-modal memory with heterogeneous data types
5. Memory with temporal awareness and versioning
"""

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING

try:  # pragma: no cover - optional dependency
    import rdflib
    from rdflib import OWL, RDF, Graph, Literal, Namespace, URIRef
    from rdflib.namespace import DC, FOAF
except Exception:  # pragma: no cover - fallback when rdflib is missing
    rdflib = None

    class URIRef(str):  # noqa: F811
        """Fallback URI reference when ``rdflib`` is unavailable."""

    class Graph:  # noqa: F811
        """Simplified graph stub used when ``rdflib`` is not installed."""

        def parse(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError("rdflib is required for graph operations")

        def serialize(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError("rdflib is required for graph operations")

        def add(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError("rdflib is required for graph operations")

        def bind(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError("rdflib is required for graph operations")

        def objects(self, *args, **kwargs):  # pragma: no cover
            return iter(())

        def triples(self, *args, **kwargs):  # pragma: no cover
            return iter(())

        def value(self, *args, **kwargs):  # pragma: no cover
            return None

    class Literal(str):  # noqa: F811
        """Fallback literal when ``rdflib`` is unavailable."""

    class _RDFType:
        """Placeholder for RDF namespace attributes."""

    OWL = RDF = FOAF = DC = _RDFType()

    def Namespace(uri: str) -> str:  # noqa: F811
        """Return ``rdflib.term.URIRef`` when available, else a plain string."""
        return uri


if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from rdflib import OWL, RDF, Graph, Literal, Namespace, URIRef  # noqa: F401,F811
    from rdflib.namespace import DC, FOAF  # noqa: F401,F811

from devsynth.exceptions import MemoryItemNotFoundError, MemoryStoreError

from ....domain.models.memory import MemoryItem, MemoryType
from ....logging_setup import DevSynthLogger
from .graph_memory_adapter import GraphMemoryAdapter

# Setup logger
logger = DevSynthLogger(__name__)

# Define additional namespaces for enhanced graph capabilities
DEVSYNTH = Namespace("http://devsynth.ai/ontology#")
EDRR = Namespace("http://devsynth.ai/ontology/edrr#")
CYCLE = Namespace("http://devsynth.ai/ontology/cycle#")
RELATION = Namespace("http://devsynth.ai/ontology/relation#")
TEMPORAL = Namespace("http://devsynth.ai/ontology/temporal#")
CONTEXT = Namespace("http://devsynth.ai/ontology/context#")


class EnhancedGraphMemoryAdapter(GraphMemoryAdapter):
    """
    Enhanced Graph Memory Adapter that extends the base GraphMemoryAdapter with
    advanced features for EDRR framework integration.
    """

    def __init__(self, base_path: str | None = None, use_rdflib_store: bool = False):
        """
        Initialize the EnhancedGraphMemoryAdapter.

        Args:
            base_path: Optional path to store the graph data
            use_rdflib_store: Whether to use RDFLib's store for persistence
        """
        super().__init__(base_path, use_rdflib_store)

        # Register additional namespaces
        if rdflib is not None:
            self.graph.bind("edrr", EDRR)
            self.graph.bind("cycle", CYCLE)
            self.graph.bind("relation", RELATION)
            self.graph.bind("temporal", TEMPORAL)
            self.graph.bind("context", CONTEXT)

            # Add OWL properties for transitive inference
            self.graph.add((RELATION.relatedTo, RDF.type, OWL.TransitiveProperty))
            self.graph.add((RELATION.partOf, RDF.type, OWL.TransitiveProperty))
            self.graph.add((RELATION.dependsOn, RDF.type, OWL.TransitiveProperty))

            # Save the graph
            self._save_graph()

    def store_with_edrr_phase(
        self,
        content: object,
        memory_type: str | MemoryType,
        edrr_phase: str,
        metadata: Mapping[str, object] | None = None,
    ) -> str:
        """
        Store a memory item with an EDRR phase with enhanced metadata.

        Args:
            content: The content of the memory item
            memory_type: The type of memory (e.g., CODE, REQUIREMENT) as string or MemoryType enum
            edrr_phase: The EDRR phase (EXPAND, DIFFERENTIATE, REFINE, RETROSPECT)
            metadata: Additional metadata for the memory item

        Returns:
            The ID of the stored memory item
        """
        # Create metadata with EDRR phase and enhanced properties
        metadata_dict = dict(metadata) if metadata else {}
        metadata_dict["edrr_phase"] = edrr_phase

        # Add timestamp for temporal awareness
        metadata_dict["timestamp"] = datetime.datetime.now().isoformat()

        # Add version information if updating existing content
        if "previous_version" in metadata_dict:
            metadata_dict["version"] = metadata_dict.get("version", 0) + 1
        else:
            metadata_dict["version"] = 1

        # Store domain information for cross-cycle persistence
        if "domain" in metadata_dict:
            # Ensure we can query by domain later
            metadata_dict["domain_tag"] = f"domain:{metadata_dict['domain']}"

        # Convert memory_type to MemoryType enum if it's a string
        if isinstance(memory_type, str):
            try:
                memory_type_enum = MemoryType(memory_type)
            except ValueError:
                # If the string doesn't match any enum value, use a default
                logger.warning(
                    f"Unknown memory type: {memory_type}, using CODE as default"
                )
                memory_type_enum = MemoryType.CODE
        else:
            memory_type_enum = memory_type

        # Create the memory item
        memory_item = MemoryItem(
            id="", content=content, memory_type=memory_type_enum, metadata=metadata_dict
        )

        # Store the memory item
        item_id = super().store(memory_item)

        # Add enhanced graph relationships if rdflib is available
        if rdflib is not None:
            item_uri = URIRef(f"{DEVSYNTH}item_{item_id}")

            # Add EDRR phase relationship
            phase_uri = URIRef(f"{EDRR}{edrr_phase}")
            self.graph.add((item_uri, EDRR.hasPhase, phase_uri))

            # Add cycle relationship if cycle_id is provided
            if "cycle_id" in metadata_dict:
                cycle_uri = URIRef(f"{CYCLE}{metadata_dict['cycle_id']}")
                self.graph.add((item_uri, CYCLE.belongsToCycle, cycle_uri))

                # Link to previous cycles in the same domain
                if "domain" in metadata_dict and "previous_cycle_id" in metadata_dict:
                    prev_cycle_uri = URIRef(
                        f"{CYCLE}{metadata_dict['previous_cycle_id']}"
                    )
                    self.graph.add((cycle_uri, CYCLE.followsCycle, prev_cycle_uri))
                    self.graph.add((prev_cycle_uri, CYCLE.precededBy, cycle_uri))

            # Add content relationships if specified
            if "related_to" in metadata_dict and isinstance(
                metadata_dict["related_to"], list
            ):
                for related_concept in metadata_dict["related_to"]:
                    concept_uri = URIRef(f"{DEVSYNTH}concept_{related_concept}")
                    self.graph.add((item_uri, RELATION.relatedTo, concept_uri))

            # Save the enhanced graph
            self._save_graph()

        return item_id

    def retrieve_with_edrr_phase(
        self,
        item_type: str,
        edrr_phase: str,
        metadata: Mapping[str, object] | None = None,
        context_aware: bool = True,
        semantic_similarity: bool = True,
        include_previous_cycles: bool = True,
    ) -> list[dict[str, object]]:
        """
        Retrieve items stored with a specific EDRR phase with enhanced context awareness.

        Args:
            item_type: Identifier of the stored item type.
            edrr_phase: The phase tag used during storage.
            metadata: Optional additional metadata for adapter queries.
            context_aware: Whether to use context-aware retrieval.
            semantic_similarity: Whether to consider semantic similarity.
            include_previous_cycles: Whether to include items from previous cycles.

        Returns:
            A list of retrieved items with relevance scores.
        """
        try:
            # Get all items from the graph
            all_items = []
            for s, p, o in self.graph.triples((None, RDF.type, DEVSYNTH.MemoryItem)):
                item = self._triples_to_memory_item(s)
                if item:
                    all_items.append(item)

            logger.debug(f"Found {len(all_items)} total memory items")

            # Filter items by memory type, EDRR phase, and additional metadata
            matching_items = []
            for item in all_items:
                # Convert memory_type to string for comparison
                item_memory_type = (
                    item.memory_type.value
                    if hasattr(item.memory_type, "value")
                    else str(item.memory_type)
                )

                # Check if the item has the correct memory type
                if item_memory_type != item_type and str(item.memory_type) != item_type:
                    continue

                # Check if the item has the specified EDRR phase
                if item.metadata.get("edrr_phase") != edrr_phase:
                    continue

                # Check if the item matches additional metadata
                match = True
                if metadata:
                    for key, value in metadata.items():
                        if key == "domain" and "domain_tag" in item.metadata:
                            # Special handling for domain queries
                            if item.metadata.get("domain_tag") != f"domain:{value}":
                                match = False
                                break
                        elif item.metadata.get(key) != value:
                            match = False
                            break

                if match:
                    matching_items.append(item)
                    logger.debug(
                        f"Found matching item: {item.id}, Type: {item.memory_type}, Metadata: {item.metadata}"
                    )

            # If no exact matches and semantic similarity is enabled, try semantic matching
            if not matching_items and semantic_similarity and rdflib is not None:
                logger.debug("No exact matches found, trying semantic similarity")
                semantic_items = self._retrieve_with_semantic_similarity(
                    item_type, edrr_phase, metadata
                )
                matching_items.extend(semantic_items)

            # If context-aware retrieval is enabled, include context-relevant items
            if (
                context_aware
                and metadata
                and "task_id" in metadata
                and rdflib is not None
            ):
                logger.debug("Adding context-relevant items")
                context_items = self._retrieve_context_relevant_items(
                    metadata.get("task_id"), edrr_phase
                )
                # Add only items that aren't already in matching_items
                existing_ids = {item.id for item in matching_items}
                for item in context_items:
                    if item.id not in existing_ids:
                        matching_items.append(item)
                        existing_ids.add(item.id)

            # If include_previous_cycles is enabled, include items from previous cycles
            if (
                include_previous_cycles
                and metadata
                and "cycle_id" in metadata
                and rdflib is not None
            ):
                logger.debug("Adding items from previous cycles")
                cycle_items = self._retrieve_previous_cycle_items(
                    metadata.get("cycle_id"), edrr_phase
                )
                # Add only items that aren't already in matching_items
                existing_ids = {item.id for item in matching_items}
                for item in cycle_items:
                    if item.id not in existing_ids:
                        matching_items.append(item)
                        existing_ids.add(item.id)

            # Rank items by relevance if context-aware retrieval is enabled
            if context_aware and matching_items:
                ranked_items = self._rank_items_by_relevance(matching_items, metadata)
            else:
                # Just add a default relevance score
                ranked_items = [
                    {"item": item, "relevance": 1.0} for item in matching_items
                ]

            if ranked_items:
                # Return the content of all matching items with relevance scores
                logger.info(
                    f"Retrieved {len(ranked_items)} items with type {item_type}, EDRR phase {edrr_phase}"
                )
                return [
                    {
                        "content": item["item"].content,
                        "relevance": item["relevance"],
                        "id": item["item"].id,
                        "metadata": item["item"].metadata,
                    }
                    for item in ranked_items
                ]

            logger.debug(
                f"No items found with type {item_type} and EDRR phase {edrr_phase}"
            )
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve item with EDRR phase: {e}")
            return []

    def _retrieve_with_semantic_similarity(
        self, item_type: str, edrr_phase: str, metadata: Mapping[str, object] | None
    ) -> list[MemoryItem]:
        """
        Retrieve items using semantic similarity rather than exact matches.

        Args:
            item_type: The type of memory item to retrieve.
            edrr_phase: The EDRR phase to filter by.
            metadata: Additional metadata for filtering.

        Returns:
            A list of memory items that are semantically similar to the query.
        """
        semantic_items = []

        # If we have rdflib, we can use the graph to find semantically similar items
        if rdflib is not None:
            # Get all items of the specified type
            type_items = []
            for s, p, o in self.graph.triples((None, RDF.type, DEVSYNTH.MemoryItem)):
                item = self._triples_to_memory_item(s)
                if item:
                    item_memory_type = (
                        item.memory_type.value
                        if hasattr(item.memory_type, "value")
                        else str(item.memory_type)
                    )
                    if (
                        item_memory_type == item_type
                        or str(item.memory_type) == item_type
                    ):
                        type_items.append(item)

            # Find items that are related to the same concepts
            if (
                metadata
                and "related_to" in metadata
                and isinstance(metadata["related_to"], list)
            ):
                for item in type_items:
                    if "related_to" in item.metadata and isinstance(
                        item.metadata["related_to"], list
                    ):
                        # Check for overlap in related concepts
                        query_concepts = set(metadata["related_to"])
                        item_concepts = set(item.metadata["related_to"])
                        overlap = query_concepts.intersection(item_concepts)
                        if overlap:
                            semantic_items.append(item)

            # Find items with similar metadata keys
            if metadata:
                for item in type_items:
                    # Check for overlap in metadata keys (excluding special keys)
                    query_keys = set(metadata.keys()) - {
                        "cycle_id",
                        "task_id",
                        "related_to",
                    }
                    item_keys = set(item.metadata.keys()) - {
                        "cycle_id",
                        "task_id",
                        "related_to",
                    }
                    overlap = query_keys.intersection(item_keys)
                    if overlap:
                        semantic_items.append(item)

        return semantic_items

    def _retrieve_context_relevant_items(
        self, task_id: str, edrr_phase: str
    ) -> list[MemoryItem]:
        """
        Retrieve items that are relevant to the current context (task).

        Args:
            task_id: The ID of the current task.
            edrr_phase: The current EDRR phase.

        Returns:
            A list of memory items relevant to the current context.
        """
        context_items = []

        # If we have rdflib, we can use the graph to find context-relevant items
        if rdflib is not None:
            # Find items related to the current task
            task_uri = URIRef(f"{DEVSYNTH}task_{task_id}")
            for s, p, o in self.graph.triples((None, CONTEXT.relatedToTask, task_uri)):
                item = self._triples_to_memory_item(s)
                if item:
                    context_items.append(item)

            # Find items from the same domain as the current task
            for s, p, o in self.graph.triples((task_uri, CONTEXT.hasDomain, None)):
                domain_uri = o
                for s2, p2, o2 in self.graph.triples(
                    (None, CONTEXT.hasDomain, domain_uri)
                ):
                    if s2 != task_uri:  # Don't include the task itself
                        item = self._triples_to_memory_item(s2)
                        if item:
                            context_items.append(item)

        return context_items

    def _retrieve_previous_cycle_items(
        self, cycle_id: str, edrr_phase: str
    ) -> list[MemoryItem]:
        """
        Retrieve items from previous cycles that are related to the current cycle.

        Args:
            cycle_id: The ID of the current cycle.
            edrr_phase: The current EDRR phase.

        Returns:
            A list of memory items from previous related cycles.
        """
        cycle_items = []

        # If we have rdflib, we can use the graph to find items from previous cycles
        if rdflib is not None:
            # Find previous cycles
            cycle_uri = URIRef(f"{CYCLE}{cycle_id}")
            previous_cycles = set()

            # Direct predecessors
            for s, p, o in self.graph.triples((cycle_uri, CYCLE.followsCycle, None)):
                previous_cycles.add(o)

            # Transitive predecessors (predecessors of predecessors)
            for cycle in list(
                previous_cycles
            ):  # Make a copy to avoid modifying during iteration
                for s, p, o in self.graph.triples((cycle, CYCLE.followsCycle, None)):
                    previous_cycles.add(o)

            # Find items from previous cycles
            for cycle in previous_cycles:
                for s, p, o in self.graph.triples((None, CYCLE.belongsToCycle, cycle)):
                    item = self._triples_to_memory_item(s)
                    if item:
                        # Only include items from the same EDRR phase
                        if item.metadata.get("edrr_phase") == edrr_phase:
                            cycle_items.append(item)

        return cycle_items

    def _rank_items_by_relevance(
        self, items: list[MemoryItem], metadata: Mapping[str, object] | None
    ) -> list[dict[str, object]]:
        """
        Rank items by relevance to the current context.

        Args:
            items: The items to rank.
            metadata: The metadata representing the current context.

        Returns:
            A list of items with relevance scores.
        """
        ranked_items = []

        for item in items:
            relevance = 1.0  # Default relevance

            # Adjust relevance based on various factors
            if metadata:
                # Items from the current cycle are more relevant
                if (
                    "cycle_id" in metadata
                    and item.metadata.get("cycle_id") == metadata["cycle_id"]
                ):
                    relevance += 0.5

                # Items with more matching metadata are more relevant
                matching_keys = 0
                for key, value in metadata.items():
                    if key in item.metadata and item.metadata[key] == value:
                        matching_keys += 1
                relevance += 0.1 * matching_keys

                # More recent items are more relevant
                if "timestamp" in item.metadata:
                    try:
                        item_time = datetime.datetime.fromisoformat(
                            item.metadata["timestamp"]
                        )
                        now = datetime.datetime.now()
                        age_days = (now - item_time).days
                        # Decrease relevance for older items (max penalty of 0.5 for items older than 30 days)
                        relevance -= min(0.5, age_days / 60)
                    except (ValueError, TypeError):
                        pass

                # Higher version items are more relevant
                if "version" in item.metadata:
                    try:
                        version = int(item.metadata["version"])
                        # Add a small boost for each version (max boost of 0.3)
                        relevance += min(0.3, version * 0.1)
                    except (ValueError, TypeError):
                        pass

            # Ensure relevance is between 0 and 2
            relevance = max(0.0, min(2.0, relevance))

            ranked_items.append({"item": item, "relevance": relevance})

        # Sort by relevance (descending)
        ranked_items.sort(key=lambda x: x["relevance"], reverse=True)

        return ranked_items

    def query_by_edrr_phase(self, edrr_phase: str) -> list[MemoryItem]:
        """
        Query memory items by EDRR phase.

        Args:
            edrr_phase: The EDRR phase to query for.

        Returns:
            A list of memory items with the specified EDRR phase.
        """
        try:
            # Get all items from the graph
            all_items = []
            for s, p, o in self.graph.triples((None, RDF.type, DEVSYNTH.MemoryItem)):
                item = self._triples_to_memory_item(s)
                if item and item.metadata.get("edrr_phase") == edrr_phase:
                    all_items.append(item)

            return all_items
        except Exception as e:
            logger.error(f"Failed to query by EDRR phase: {e}")
            return []

    def query_evolution_across_edrr_phases(self, item_id: str) -> list[MemoryItem]:
        """
        Query the evolution of an item across different EDRR phases.

        Args:
            item_id: The ID of the item to track.

        Returns:
            A list of memory items representing the evolution of the item.
        """
        try:
            # Get the item
            item = self.retrieve(item_id)
            if not item:
                return []

            # Get all items with the same domain and task
            domain = item.metadata.get("domain")
            task_id = item.metadata.get("task_id")

            if not domain or not task_id:
                return [item]

            # Query items with the same domain and task
            all_items = []
            for s, p, o in self.graph.triples((None, RDF.type, DEVSYNTH.MemoryItem)):
                candidate = self._triples_to_memory_item(s)
                if (
                    candidate
                    and candidate.metadata.get("domain") == domain
                    and candidate.metadata.get("task_id") == task_id
                ):
                    all_items.append(candidate)

            # Sort by EDRR phase order
            phase_order = {
                "EXPAND": 1,
                "DIFFERENTIATE": 2,
                "REFINE": 3,
                "RETROSPECT": 4,
            }
            all_items.sort(
                key=lambda x: phase_order.get(x.metadata.get("edrr_phase", ""), 0)
            )

            return all_items
        except Exception as e:
            logger.error(f"Failed to query evolution across EDRR phases: {e}")
            return []

    def find_related_concepts(self, concept: str, max_depth: int = 2) -> list[str]:
        """
        Find concepts related to the given concept using transitive inference.

        Args:
            concept: The concept to find related concepts for.
            max_depth: The maximum depth of transitive relationships to explore.

        Returns:
            A list of related concepts.
        """
        if rdflib is None:
            return []

        try:
            concept_uri = URIRef(f"{DEVSYNTH}concept_{concept}")
            related_concepts = set()

            # Find directly related concepts
            for s, p, o in self.graph.triples((concept_uri, RELATION.relatedTo, None)):
                if s != concept_uri:  # Don't include the concept itself
                    concept_str = str(s).replace(f"{DEVSYNTH}concept_", "")
                    related_concepts.add(concept_str)

            # Find transitively related concepts up to max_depth
            current_depth = 1
            current_concepts = {concept_uri}

            while current_depth < max_depth:
                next_concepts = set()
                for c in current_concepts:
                    for s, p, o in self.graph.triples((c, RELATION.relatedTo, None)):
                        if o not in current_concepts:  # Avoid cycles
                            next_concepts.add(o)
                            concept_str = str(o).replace(f"{DEVSYNTH}concept_", "")
                            related_concepts.add(concept_str)

                if not next_concepts:
                    break

                current_concepts = next_concepts
                current_depth += 1

            return list(related_concepts)
        except Exception as e:
            logger.error(f"Failed to find related concepts: {e}")
            return []

    def store_version_history(
        self,
        item_id: str,
        new_content: object,
        metadata: Mapping[str, object] | None = None,
    ) -> str:
        """
        Store a new version of an existing item with version history.

        Args:
            item_id: The ID of the item to update.
            new_content: The new content for the item.
            metadata: Additional metadata for the new version.

        Returns:
            The ID of the new version.
        """
        try:
            # Get the existing item
            existing_item = self.retrieve(item_id)
            if not existing_item:
                raise MemoryItemNotFoundError(f"Item with ID {item_id} not found")

            # Create metadata for the new version
            if metadata is None:
                metadata = {}

            # Copy metadata from the existing item
            new_metadata = existing_item.metadata.copy()

            # Update with new metadata
            new_metadata.update(metadata)

            # Set version information
            new_metadata["previous_version"] = item_id
            new_metadata["version"] = new_metadata.get("version", 0) + 1
            new_metadata["timestamp"] = datetime.datetime.now().isoformat()

            # Create the new version
            memory_item = MemoryItem(
                id="",
                content=new_content,
                memory_type=existing_item.memory_type,
                metadata=new_metadata,
            )

            # Store the new version
            new_id = self.store(memory_item)

            # Add version relationship in the graph
            if rdflib is not None:
                item_uri = URIRef(f"{DEVSYNTH}item_{new_id}")
                prev_uri = URIRef(f"{DEVSYNTH}item_{item_id}")
                self.graph.add((item_uri, TEMPORAL.versionOf, prev_uri))
                self.graph.add((prev_uri, TEMPORAL.hasVersion, item_uri))
                self._save_graph()

            return new_id
        except Exception as e:
            logger.error(f"Failed to store version history: {e}")
            raise MemoryStoreError(f"Failed to store version history: {e}")

    def get_version_history(self, item_id: str) -> list[MemoryItem]:
        """
        Get the version history of an item.

        Args:
            item_id: The ID of the item to get the version history for.

        Returns:
            A list of memory items representing the version history.
        """
        try:
            # Get the item
            item = self.retrieve(item_id)
            if not item:
                return []

            # Start with the current item
            history = [item]

            # Traverse the version history backwards
            while "previous_version" in history[-1].metadata:
                prev_id = history[-1].metadata["previous_version"]
                prev_item = self.retrieve(prev_id)
                if prev_item:
                    history.append(prev_item)
                else:
                    break

                # Avoid infinite loops
                if len(history) > 100:
                    break

            # Reverse to get chronological order
            history.reverse()

            return history
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return []
