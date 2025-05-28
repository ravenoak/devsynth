"""
Graph Memory Adapter Module

This module provides a memory adapter that handles relationships between memory items
using a graph-based approach with RDFLib. It integrates with RDFLibStore for enhanced
functionality and improved integration between different memory stores.
"""
import os
import uuid
from typing import Dict, List, Any, Optional, Set, Union
import rdflib
from rdflib import Graph, Literal, URIRef, Namespace, RDF, RDFS, XSD
from rdflib.namespace import FOAF, DC

from ....domain.models.memory import MemoryItem, MemoryType, MemoryVector
from ....domain.interfaces.memory import MemoryStore, VectorStore
from ....logging_setup import DevSynthLogger
from devsynth.exceptions import MemoryError, MemoryStoreError, MemoryItemNotFoundError
from ..rdflib_store import RDFLibStore

logger = DevSynthLogger(__name__)

# Define custom namespaces
DEVSYNTH = Namespace("http://devsynth.ai/ontology/")
MEMORY = Namespace("http://devsynth.ai/memory/")

class GraphMemoryAdapter(MemoryStore):
    """
    Graph Memory Adapter handles relationships between memory items using a graph-based approach.

    It implements the MemoryStore interface and provides additional methods for querying
    relationships between items. This implementation uses RDFLib to store and retrieve
    memory items and their relationships as RDF triples.

    This adapter can optionally integrate with RDFLibStore for enhanced functionality
    such as vector storage and retrieval, SPARQL queries, and improved memory volatility controls.
    """

    def __init__(self, base_path: str = None, use_rdflib_store: bool = False):
        """
        Initialize the Graph Memory Adapter.

        Args:
            base_path: Optional path to store the RDF graph. If not provided,
                      an in-memory graph will be used.
            use_rdflib_store: Whether to use RDFLibStore for enhanced functionality.
                             If True, a RDFLibStore instance will be created and used
                             for advanced operations.
        """
        self.base_path = base_path
        self.use_rdflib_store = use_rdflib_store

        if use_rdflib_store and base_path:
            # Use RDFLibStore for enhanced functionality
            self.rdflib_store = RDFLibStore(base_path)
            self.graph = self.rdflib_store.graph
            logger.info("Graph Memory Adapter initialized with RDFLibStore integration")
        else:
            # Use basic RDFLib functionality
            self.rdflib_store = None
            self.graph = Graph()

            # Register namespaces
            self.graph.bind("devsynth", DEVSYNTH)
            self.graph.bind("memory", MEMORY)
            self.graph.bind("foaf", FOAF)
            self.graph.bind("dc", DC)

            # Load existing graph if base_path is provided
            if base_path:
                os.makedirs(base_path, exist_ok=True)
                self.graph_file = os.path.join(base_path, "graph_memory.ttl")
                if os.path.exists(self.graph_file):
                    try:
                        self.graph.parse(self.graph_file, format="turtle")
                        logger.info(f"Loaded RDF graph from {self.graph_file}")
                    except Exception as e:
                        logger.error(f"Failed to load RDF graph: {e}")

            logger.info("Graph Memory Adapter initialized with basic RDFLib")

    def _save_graph(self) -> None:
        """Save the RDF graph to disk if a base path is provided."""
        if self.use_rdflib_store and self.rdflib_store:
            # RDFLibStore handles saving the graph
            logger.debug("Using RDFLibStore to save the graph")
            # No need to explicitly save as RDFLibStore methods handle this
            return
        elif self.base_path:
            try:
                self.graph.serialize(destination=self.graph_file, format="turtle")
                logger.info(f"Saved RDF graph to {self.graph_file}")
            except Exception as e:
                logger.error(f"Failed to save RDF graph: {e}")
                raise MemoryStoreError(f"Failed to save RDF graph: {e}")

    def _memory_item_to_triples(self, item: MemoryItem) -> URIRef:
        """
        Convert a memory item to RDF triples and add them to the graph.

        Args:
            item: The memory item to convert

        Returns:
            The URI reference for the item
        """
        # Create a URI for the item
        item_uri = URIRef(f"{MEMORY}{item.id}")

        # Add basic triples
        self.graph.add((item_uri, RDF.type, DEVSYNTH.MemoryItem))
        self.graph.add((item_uri, DEVSYNTH.id, Literal(item.id)))
        self.graph.add((item_uri, DEVSYNTH.content, Literal(item.content)))
        self.graph.add((item_uri, DEVSYNTH.memory_type, Literal(item.memory_type.value)))

        # Add metadata
        for key, value in item.metadata.items():
            # Skip complex objects in metadata
            if isinstance(value, (str, int, float, bool)):
                self.graph.add((item_uri, DEVSYNTH[key], Literal(value)))

        return item_uri

    def _triples_to_memory_item(self, item_uri: URIRef) -> Optional[MemoryItem]:
        """
        Convert RDF triples to a memory item.

        Args:
            item_uri: The URI reference for the item

        Returns:
            The memory item, or None if not found
        """
        # Check if the item exists
        if (item_uri, RDF.type, DEVSYNTH.MemoryItem) not in self.graph:
            return None

        # Get basic properties
        item_id = str(self.graph.value(item_uri, DEVSYNTH.id))
        content = str(self.graph.value(item_uri, DEVSYNTH.content))
        memory_type_value = str(self.graph.value(item_uri, DEVSYNTH.memory_type))
        memory_type = MemoryType(memory_type_value)

        # Get metadata
        metadata = {}
        for s, p, o in self.graph.triples((item_uri, None, None)):
            # Skip non-metadata properties
            if p in [RDF.type, DEVSYNTH.id, DEVSYNTH.content, DEVSYNTH.memory_type]:
                continue

            # Extract the property name from the URI
            prop_name = p.split('/')[-1]
            metadata[prop_name] = o.toPython()

        # Create and return the memory item
        return MemoryItem(
            id=item_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata
        )

    def store(self, item: MemoryItem) -> str:
        """
        Store a memory item and process its relationships.

        Args:
            item: The memory item to store

        Returns:
            The ID of the stored memory item
        """
        try:
            # Generate an ID if not provided
            if not item.id:
                item.id = f"graph_{uuid.uuid4()}"

            # Convert the item to triples and add to the graph
            item_uri = self._memory_item_to_triples(item)

            # Process relationships
            related_to = item.metadata.get("related_to")
            if related_to:
                related_uri = URIRef(f"{MEMORY}{related_to}")

                # Add the relationship
                self.graph.add((item_uri, DEVSYNTH.relatedTo, related_uri))

                # Add the reverse relationship
                self.graph.add((related_uri, DEVSYNTH.relatedTo, item_uri))

            # Save the graph
            self._save_graph()

            logger.info(f"Stored memory item with ID {item.id} in Graph Memory Adapter")
            return item.id
        except Exception as e:
            logger.error(f"Failed to store memory item: {e}")
            raise MemoryStoreError(f"Failed to store memory item: {e}")

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        try:
            # Create a URI for the item
            item_uri = URIRef(f"{MEMORY}{item_id}")

            # Convert triples to a memory item
            item = self._triples_to_memory_item(item_uri)

            if item:
                logger.info(f"Retrieved memory item with ID {item_id} from Graph Memory Adapter")
            else:
                logger.warning(f"Memory item with ID {item_id} not found in Graph Memory Adapter")

            return item
        except Exception as e:
            logger.error(f"Failed to retrieve memory item: {e}")
            raise MemoryStoreError(f"Failed to retrieve memory item: {e}")

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Search for memory items matching the query.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        try:
            results = []
            logger.debug(f"Searching with query: {query}")

            # Get all memory items
            all_items = []
            for s, p, o in self.graph.triples((None, RDF.type, DEVSYNTH.MemoryItem)):
                item = self._triples_to_memory_item(s)
                if item:
                    all_items.append(item)

            logger.debug(f"Found {len(all_items)} total memory items")

            # Check each item against the query
            for item in all_items:
                match = True
                memory_type_value = item.memory_type.value if hasattr(item.memory_type, 'value') else str(item.memory_type)
                logger.info(f"Checking item with ID: {item.id}, memory_type: {memory_type_value}, metadata: {item.metadata}")

                for key, value in query.items():
                    if key == "type":
                        # Check if the memory_type matches the value
                        # Convert both memory_type and value to string for comparison
                        value_str = value.value if hasattr(value, 'value') else str(value)
                        if memory_type_value != value_str:
                            # Also check if the type is in metadata
                            if key in item.metadata and item.metadata[key] == value_str:
                                logger.info(f"Item {item.id} matches type in metadata: {item.metadata[key]} == {value_str}")
                            else:
                                logger.info(f"Item {item.id} doesn't match type: {memory_type_value} != {value_str}")
                                match = False
                                break
                    elif key in item.metadata:
                        if item.metadata[key] != value:
                            logger.info(f"Item {item.id} doesn't match metadata {key}: {item.metadata[key]} != {value}")
                            match = False
                            break
                    else:
                        logger.info(f"Item {item.id} doesn't have metadata key: {key}")
                        match = False
                        break

                if match:
                    logger.debug(f"Item {item.id} matches the query")
                    results.append(item)

            logger.info(f"Found {len(results)} matching memory items in Graph Memory Adapter")
            return results
        except Exception as e:
            logger.error(f"Failed to search memory items: {e}")
            raise MemoryStoreError(f"Failed to search memory items: {e}")

    def delete(self, item_id: str) -> bool:
        """
        Delete a memory item.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the item was deleted, False otherwise
        """
        try:
            # Create a URI for the item
            item_uri = URIRef(f"{MEMORY}{item_id}")

            # Check if the item exists
            if (item_uri, RDF.type, DEVSYNTH.MemoryItem) not in self.graph:
                logger.warning(f"Memory item with ID {item_id} not found in Graph Memory Adapter")
                return False

            # Get related items
            related_uris = list(self.graph.objects(item_uri, DEVSYNTH.relatedTo))

            # Remove relationships
            for related_uri in related_uris:
                self.graph.remove((item_uri, DEVSYNTH.relatedTo, related_uri))
                self.graph.remove((related_uri, DEVSYNTH.relatedTo, item_uri))

            # Remove all triples for this item
            self.graph.remove((item_uri, None, None))

            # Save the graph
            self._save_graph()

            logger.info(f"Deleted memory item with ID {item_id} from Graph Memory Adapter")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory item: {e}")
            raise MemoryStoreError(f"Failed to delete memory item: {e}")

    def query_related_items(self, item_id: str) -> List[MemoryItem]:
        """
        Query for items related to a given item ID.

        Args:
            item_id: The ID of the item to find related items for

        Returns:
            A list of related memory items
        """
        try:
            # Create a URI for the item
            item_uri = URIRef(f"{MEMORY}{item_id}")

            # Check if the item exists
            if (item_uri, RDF.type, DEVSYNTH.MemoryItem) not in self.graph:
                logger.warning(f"Memory item with ID {item_id} not found in Graph Memory Adapter")
                return []

            # Get related items
            related_uris = list(self.graph.objects(item_uri, DEVSYNTH.relatedTo))
            related_items = []

            for related_uri in related_uris:
                item = self._triples_to_memory_item(related_uri)
                if item:
                    related_items.append(item)

            logger.info(f"Found {len(related_items)} items related to {item_id} in Graph Memory Adapter")
            return related_items
        except Exception as e:
            logger.error(f"Failed to query related items: {e}")
            raise MemoryStoreError(f"Failed to query related items: {e}")

    def get_all_relationships(self) -> Dict[str, Set[str]]:
        """
        Get all relationships in the graph.

        Returns:
            A dictionary of relationships by item ID
        """
        try:
            relationships = {}

            # Query all relatedTo relationships
            for s, p, o in self.graph.triples((None, DEVSYNTH.relatedTo, None)):
                # Extract item IDs from URIs
                subject_id = str(self.graph.value(s, DEVSYNTH.id))
                object_id = str(self.graph.value(o, DEVSYNTH.id))

                # Initialize set if not exists
                if subject_id not in relationships:
                    relationships[subject_id] = set()

                # Add relationship
                relationships[subject_id].add(object_id)

            logger.info(f"Retrieved all relationships from Graph Memory Adapter")
            return relationships
        except Exception as e:
            logger.error(f"Failed to get all relationships: {e}")
            raise MemoryStoreError(f"Failed to get all relationships: {e}")

    def add_memory_volatility(self, decay_rate: float = 0.1, threshold: float = 0.5, 
                              advanced_controls: bool = False) -> None:
        """
        Add memory volatility controls to the graph.

        This method adds a 'confidence' property to all memory items and
        implements a decay mechanism where confidence decreases over time.

        When using RDFLibStore integration with advanced_controls enabled, 
        this method implements more sophisticated volatility controls including
        time-based decay, access frequency adjustments, and relationship-based
        confidence boosting.

        Args:
            decay_rate: The rate at which confidence decays (0.0 to 1.0)
            threshold: The confidence threshold below which items are considered volatile
            advanced_controls: Whether to use advanced volatility controls (requires RDFLibStore)
        """
        try:
            if self.use_rdflib_store and self.rdflib_store and advanced_controls:
                # Use SPARQL for more efficient batch updates
                sparql_update = """
                    PREFIX devsynth: <http://devsynth.ai/ontology/>
                    PREFIX memory: <http://devsynth.ai/memory/>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

                    INSERT {
                        ?item devsynth:confidence "1.0"^^<http://www.w3.org/2001/XMLSchema#float> .
                        ?item devsynth:decayRate "%f"^^<http://www.w3.org/2001/XMLSchema#float> .
                        ?item devsynth:confidenceThreshold "%f"^^<http://www.w3.org/2001/XMLSchema#float> .
                        ?item devsynth:lastAccessTime ?now .
                        ?item devsynth:accessCount "0"^^<http://www.w3.org/2001/XMLSchema#integer> .
                        ?item devsynth:volatilityEnabled "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .
                    }
                    WHERE {
                        ?item rdf:type devsynth:MemoryItem .
                        FILTER NOT EXISTS { ?item devsynth:confidence ?conf }
                        BIND(NOW() as ?now)
                    }
                """ % (decay_rate, threshold)

                self.graph.update(sparql_update)
                logger.info(f"Added advanced memory volatility controls with decay rate {decay_rate} and threshold {threshold}")
            else:
                # Use basic RDFLib approach
                for s, p, o in self.graph.triples((None, RDF.type, DEVSYNTH.MemoryItem)):
                    # Check if confidence already exists
                    if (s, DEVSYNTH.confidence, None) not in self.graph:
                        # Add initial confidence of 1.0
                        self.graph.add((s, DEVSYNTH.confidence, Literal(1.0)))

                        # Add decay rate and threshold
                        self.graph.add((s, DEVSYNTH.decayRate, Literal(decay_rate)))
                        self.graph.add((s, DEVSYNTH.confidenceThreshold, Literal(threshold)))

            # Save the graph
            self._save_graph()

            logger.info(f"Added memory volatility controls with decay rate {decay_rate} and threshold {threshold}")
        except Exception as e:
            logger.error(f"Failed to add memory volatility controls: {e}")
            raise MemoryStoreError(f"Failed to add memory volatility controls: {e}")

    def apply_memory_decay(self, advanced_decay: bool = False) -> List[str]:
        """
        Apply memory decay to all items in the graph.

        This method decreases the confidence of all memory items according to their
        decay rate and returns the IDs of items that have fallen below the confidence threshold.

        When using RDFLibStore integration with advanced_decay enabled, this method implements
        more sophisticated decay mechanisms including:
        - Time-based decay (items decay faster the longer they haven't been accessed)
        - Access frequency adjustments (frequently accessed items decay slower)
        - Relationship-based confidence boosting (items with many relationships decay slower)

        Args:
            advanced_decay: Whether to use advanced decay mechanisms (requires RDFLibStore)

        Returns:
            A list of IDs of memory items that have fallen below the confidence threshold
        """
        try:
            volatile_items = []

            if self.use_rdflib_store and self.rdflib_store and advanced_decay:
                # Use SPARQL for more efficient batch processing

                # 1. First, get all items with volatility enabled
                sparql_query = """
                    PREFIX devsynth: <http://devsynth.ai/ontology/>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

                    SELECT ?item ?id ?confidence ?decayRate ?threshold ?lastAccess ?accessCount
                    WHERE {
                        ?item rdf:type devsynth:MemoryItem .
                        ?item devsynth:id ?id .
                        ?item devsynth:confidence ?confidence .
                        ?item devsynth:decayRate ?decayRate .
                        ?item devsynth:confidenceThreshold ?threshold .
                        OPTIONAL { ?item devsynth:lastAccessTime ?lastAccess }
                        OPTIONAL { ?item devsynth:accessCount ?accessCount }
                        OPTIONAL { 
                            ?item devsynth:volatilityEnabled ?enabled .
                            FILTER(?enabled = "true"^^<http://www.w3.org/2001/XMLSchema#boolean>)
                        }
                    }
                """

                results = self.graph.query(sparql_query)

                # Process each item with advanced decay logic
                for row in results:
                    item_uri = row[0]
                    item_id = str(row[1])
                    confidence = float(row[2])
                    decay_rate = float(row[3])
                    threshold = float(row[4])

                    # Get optional values with defaults
                    last_access = row[5] if row[5] else None
                    access_count = int(row[6]) if row[6] else 0

                    # Calculate time-based decay factor
                    time_factor = 1.0
                    if last_access:
                        # Calculate days since last access
                        from datetime import datetime
                        now = datetime.now()
                        # Convert last_access to a naive datetime by removing timezone info
                        last_access_str = str(last_access).replace('Z', '')
                        if '+' in last_access_str:
                            last_access_str = last_access_str.split('+')[0]
                        last_access_date = datetime.fromisoformat(last_access_str)
                        days_since_access = (now - last_access_date).days
                        # Increase decay for items not accessed recently
                        time_factor = min(2.0, 1.0 + (days_since_access / 30.0))

                    # Calculate access frequency factor
                    access_factor = max(0.5, 1.0 - (access_count / 100.0))

                    # Calculate relationship factor
                    relationship_count = len(list(self.graph.triples((item_uri, DEVSYNTH.relatedTo, None))))
                    relationship_factor = max(0.5, 1.0 - (relationship_count / 20.0))

                    # Apply combined decay
                    combined_decay_rate = decay_rate * time_factor * access_factor * relationship_factor
                    new_confidence = max(0.0, confidence - combined_decay_rate)

                    # Update confidence with SPARQL
                    update_query = f"""
                        PREFIX devsynth: <http://devsynth.ai/ontology/>

                        DELETE {{ 
                            <{item_uri}> devsynth:confidence "{confidence}"^^<http://www.w3.org/2001/XMLSchema#float> .
                        }}
                        INSERT {{ 
                            <{item_uri}> devsynth:confidence "{new_confidence}"^^<http://www.w3.org/2001/XMLSchema#float> .
                        }}
                        WHERE {{ }}
                    """
                    self.graph.update(update_query)

                    # Check if below threshold
                    if new_confidence < threshold:
                        volatile_items.append(item_id)

                logger.info(f"Applied advanced memory decay, {len(volatile_items)} items are now volatile")
            else:
                # Use basic RDFLib approach
                for s, p, o in self.graph.triples((None, DEVSYNTH.confidence, None)):
                    # Get current confidence
                    confidence = float(o)

                    # Get decay rate and threshold
                    decay_rate = float(self.graph.value(s, DEVSYNTH.decayRate, default=Literal(0.1)))
                    threshold = float(self.graph.value(s, DEVSYNTH.confidenceThreshold, default=Literal(0.5)))

                    # Apply decay
                    new_confidence = max(0.0, confidence - decay_rate)

                    # Update confidence
                    self.graph.remove((s, DEVSYNTH.confidence, o))
                    self.graph.add((s, DEVSYNTH.confidence, Literal(new_confidence)))

                    # Check if below threshold
                    if new_confidence < threshold:
                        # Get item ID
                        item_id = str(self.graph.value(s, DEVSYNTH.id))
                        volatile_items.append(item_id)

            # Save the graph
            self._save_graph()

            logger.info(f"Applied memory decay, {len(volatile_items)} items are now volatile")
            return volatile_items
        except Exception as e:
            logger.error(f"Failed to apply memory decay: {e}")
            raise MemoryStoreError(f"Failed to apply memory decay: {e}")

    def store_with_edrr_phase(self, content: Any, memory_type: Union[str, MemoryType], edrr_phase: str, 
                             metadata: Dict[str, Any] = None) -> str:
        """
        Store a memory item with an EDRR phase.

        Args:
            content: The content of the memory item
            memory_type: The type of memory (e.g., CODE, REQUIREMENT) as string or MemoryType enum
            edrr_phase: The EDRR phase (EXPAND, DIFFERENTIATE, REFINE, RETROSPECT)
            metadata: Additional metadata for the memory item

        Returns:
            The ID of the stored memory item
        """
        # Create metadata with EDRR phase
        if metadata is None:
            metadata = {}
        metadata["edrr_phase"] = edrr_phase

        # Store the original memory_type as a metadata field for searching
        if isinstance(memory_type, str):
            metadata["type"] = memory_type
        elif hasattr(memory_type, 'value'):
            metadata["type"] = memory_type.value
        else:
            metadata["type"] = str(memory_type)

        # Convert memory_type to MemoryType enum if it's a string
        if isinstance(memory_type, str):
            try:
                memory_type = MemoryType(memory_type)
            except ValueError:
                # If the string doesn't match any enum value, use a default
                logger.warning(f"Unknown memory type: {memory_type}, using CODE as default")
                memory_type = MemoryType.CODE

        # Create the memory item
        memory_item = MemoryItem(
            id="",
            content=content,
            memory_type=memory_type,
            metadata=metadata
        )

        # Store the memory item
        return self.store(memory_item)

    def integrate_with_store(self, other_store: Union[MemoryStore, VectorStore], 
                           sync_mode: str = "bidirectional") -> None:
        """
        Integrate this graph memory adapter with another memory store.

        This method enables data exchange between different memory stores, allowing
        for a more integrated memory architecture. It can synchronize memory items
        between stores and establish relationships between items across stores.

        Args:
            other_store: Another memory store to integrate with
            sync_mode: The synchronization mode, one of:
                       - "bidirectional": Sync data in both directions
                       - "import": Import data from other_store to this store
                       - "export": Export data from this store to other_store

        Raises:
            MemoryStoreError: If integration fails
        """
        try:
            logger.info(f"Integrating with {type(other_store).__name__} in {sync_mode} mode")

            # Use duck typing to check if other_store has MemoryStore-like methods
            has_memory_store_methods = hasattr(other_store, 'store') and hasattr(other_store, 'retrieve') and hasattr(other_store, 'search')

            if has_memory_store_methods:
                # Handle import mode (or bidirectional)
                if sync_mode in ["import", "bidirectional"]:
                    # Get all items from other store
                    # Note: This is a simplified approach that assumes the other store
                    # has a method to get all items. In a real implementation, you might
                    # need to use a different approach depending on the store type.
                    if hasattr(other_store, "get_all_items"):
                        items = other_store.get_all_items()
                    else:
                        # Fallback to searching with empty query if get_all_items is not available
                        items = other_store.search({})

                    # Import items to this store
                    for item in items:
                        # Check if item already exists
                        existing_item = self.retrieve(item.id)
                        if not existing_item:
                            # Store the item
                            self.store(item)
                            logger.debug(f"Imported item {item.id} from {type(other_store).__name__}")

                # Handle export mode (or bidirectional)
                if sync_mode in ["export", "bidirectional"]:
                    # Get all items from this store
                    items = self.search({})

                    # Export items to other store
                    for item in items:
                        # Check if item already exists in other store
                        existing_item = other_store.retrieve(item.id)
                        if not existing_item:
                            # Store the item in other store
                            other_store.store(item)
                            logger.debug(f"Exported item {item.id} to {type(other_store).__name__}")

            # Use duck typing to check if other_store has VectorStore-like methods
            has_vector_store_methods = hasattr(other_store, 'get_collection_stats')

            # Check if this adapter is using RDFLibStore
            if has_vector_store_methods and self.use_rdflib_store and self.rdflib_store:
                # Handle import mode (or bidirectional)
                if sync_mode in ["import", "bidirectional"]:
                    # Get collection stats to determine if vectors exist
                    if hasattr(other_store, "get_collection_stats"):
                        stats = other_store.get_collection_stats()
                        if stats.get("num_vectors", 0) > 0:
                            # This is a simplified approach. In a real implementation,
                            # you would need a way to retrieve all vectors from the other store.
                            logger.info(f"Vector integration with {type(other_store).__name__} would require custom implementation")

                # Handle export mode (or bidirectional)
                if sync_mode in ["export", "bidirectional"] and hasattr(self.rdflib_store, "get_collection_stats"):
                    # Get all vectors from this store
                    stats = self.rdflib_store.get_collection_stats()
                    if stats.get("num_vectors", 0) > 0:
                        # This is a simplified approach. In a real implementation,
                        # you would need a way to retrieve all vectors from this store.
                        logger.info(f"Vector export to {type(other_store).__name__} would require custom implementation")

            logger.info(f"Integration with {type(other_store).__name__} completed")
        except Exception as e:
            logger.error(f"Failed to integrate with {type(other_store).__name__}: {e}")
            raise MemoryStoreError(f"Failed to integrate with {type(other_store).__name__}: {e}")
