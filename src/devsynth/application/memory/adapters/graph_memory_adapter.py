"""
Graph Memory Adapter Module

This module provides a memory adapter that handles relationships between memory items
using a graph-based approach with RDFLib. It integrates with RDFLibStore for enhanced
functionality and improved integration between different memory stores.
"""

import os
import uuid
import json
from typing import Dict, List, Any, Optional, Set, Union
from contextlib import contextmanager
from copy import deepcopy

try:
    import rdflib
    from rdflib import Graph, Literal, URIRef, Namespace, RDF, RDFS, XSD
    from rdflib.namespace import FOAF, DC
    from ....exceptions import MemoryTransactionError

    try:
        Namespace("test")
    except Exception:
        raise ImportError
except Exception:
    rdflib = None
    Graph = Literal = URIRef = object  # type: ignore
    RDF = RDFS = XSD = object  # type: ignore
    FOAF = DC = object  # type: ignore

    def Namespace(uri: str):  # type: ignore
        return uri


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
        self._transaction_stack: List[str] = []

        if use_rdflib_store and base_path:
            # Use RDFLibStore for enhanced functionality
            self.rdflib_store = RDFLibStore(base_path)
            # Align the graph file name with the adapter expectations
            self.graph_file = os.path.join(base_path, "graph_memory.ttl")
            self.rdflib_store.graph_file = self.graph_file
            # Reload the graph if the custom file exists
            if os.path.exists(self.graph_file):
                try:
                    self.rdflib_store.graph.parse(self.graph_file, format="turtle")
                    logger.info(f"Loaded RDF graph from {self.graph_file}")
                except Exception as e:
                    logger.error(f"Failed to load RDF graph: {e}")
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

    # ------------------------------------------------------------------
    def is_transaction_active(self, transaction_id: str) -> bool:  # pragma: no cover - simple interface compliance
        """Return False as GraphMemoryAdapter does not track transactions."""
        return False

    def _save_graph(self) -> None:
        """Save the RDF graph to disk if a base path is provided."""
        if self.use_rdflib_store and self.rdflib_store:
            # Ensure the RDFLibStore uses the same graph file
            self.rdflib_store.graph_file = getattr(
                self, "graph_file", os.path.join(self.base_path, "graph_memory.ttl")
            )
            logger.debug("Using RDFLibStore to save the graph")
            self.rdflib_store._save_graph()
            return
        elif self.base_path:
            try:
                self.graph.serialize(destination=self.graph_file, format="turtle")
                logger.info(f"Saved RDF graph to {self.graph_file}")
            except Exception as e:
                logger.error(f"Failed to save RDF graph: {e}")
                raise MemoryStoreError(f"Failed to save RDF graph: {e}")

    # transactional support -------------------------------------------------
    @contextmanager
    def transaction(self):
        """Provide a rollback context for graph updates."""
        transaction_id = str(uuid.uuid4())
        self.begin_transaction(transaction_id)
        try:
            yield
            self.commit_transaction(transaction_id)
        except Exception:
            self.rollback_transaction(transaction_id)
            raise
            
    def begin_transaction(self, transaction_id: str) -> str:
        """
        Begin a transaction.
        
        Args:
            transaction_id: The ID of the transaction
            
        Returns:
            The transaction ID
            
        Raises:
            MemoryTransactionError: If the transaction cannot be started
        """
        logger.debug(f"Beginning transaction {transaction_id} in GraphMemoryAdapter")
        
        # Store the transaction ID
        if not hasattr(self, '_active_transactions'):
            self._active_transactions = {}
            
        # Create a snapshot of the current state
        snapshot = self.graph.serialize(format="turtle")
        
        # Store the snapshot with the transaction ID
        self._active_transactions[transaction_id] = {
            'snapshot': snapshot,
            'prepared': False
        }
        
        # Also maintain compatibility with the existing transaction stack
        if not hasattr(self, '_transaction_stack'):
            self._transaction_stack = []
        self._transaction_stack.append(snapshot)
        
        return transaction_id
        
    def prepare_commit(self, transaction_id: str) -> bool:
        """
        Prepare to commit a transaction.
        
        This is the first phase of a two-phase commit protocol.
        
        Args:
            transaction_id: The ID of the transaction
            
        Returns:
            True if the transaction is prepared for commit
            
        Raises:
            MemoryTransactionError: If the transaction cannot be prepared
        """
        logger.debug(f"Preparing to commit transaction {transaction_id} in GraphMemoryAdapter")
        
        # Check if this is an active transaction
        if not hasattr(self, '_active_transactions') or transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="GraphMemoryAdapter",
                operation="prepare_commit"
            )
            
        # Mark the transaction as prepared
        self._active_transactions[transaction_id]['prepared'] = True
        
        # Save the current state to ensure durability
        self._save_graph()
        
        return True
        
    def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction.
        
        Args:
            transaction_id: The ID of the transaction
            
        Returns:
            True if the transaction was committed
            
        Raises:
            MemoryTransactionError: If the transaction cannot be committed
        """
        logger.debug(f"Committing transaction {transaction_id} in GraphMemoryAdapter")
        
        # Check if this is an active transaction
        if not hasattr(self, '_active_transactions') or transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="GraphMemoryAdapter",
                operation="commit_transaction"
            )
            
        # Remove the transaction from the active transactions
        del self._active_transactions[transaction_id]
        
        # Also maintain compatibility with the existing transaction stack
        if hasattr(self, '_transaction_stack') and self._transaction_stack:
            self._transaction_stack.pop()
            
        # Save the current state to ensure durability
        self._save_graph()
        
        return True
        
    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction.
        
        Args:
            transaction_id: The ID of the transaction
            
        Returns:
            True if the transaction was rolled back
            
        Raises:
            MemoryTransactionError: If the transaction cannot be rolled back
        """
        logger.debug(f"Rolling back transaction {transaction_id} in GraphMemoryAdapter")
        
        # Check if this is an active transaction
        if not hasattr(self, '_active_transactions') or transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="GraphMemoryAdapter",
                operation="rollback_transaction"
            )
            
        # Get the snapshot
        snapshot = self._active_transactions[transaction_id]['snapshot']
        
        # Restore the graph from the snapshot
        self.graph = Graph()
        self.graph.parse(data=snapshot, format="turtle")
        
        # Save the restored graph
        self._save_graph()
        
        # Remove the transaction from the active transactions
        del self._active_transactions[transaction_id]
        
        # Also maintain compatibility with the existing transaction stack
        if hasattr(self, '_transaction_stack') and self._transaction_stack:
            self._transaction_stack.pop()
            
        return True
        
    def snapshot(self) -> str:
        """
        Create a snapshot of the current state.
        
        Returns:
            A serialized representation of the graph
        """
        return self.graph.serialize(format="turtle")
        
    def restore(self, snapshot: str) -> bool:
        """
        Restore from a snapshot.
        
        Args:
            snapshot: A serialized representation of the graph
            
        Returns:
            True if the restore was successful
        """
        if snapshot is None:
            return False
            
        try:
            self.graph = Graph()
            self.graph.parse(data=snapshot, format="turtle")
            self._save_graph()
            return True
        except Exception as e:
            logger.error(f"Failed to restore graph from snapshot: {e}")
            return False

    def get_all_vectors(self) -> List[MemoryVector]:
        """Return all vectors from the underlying RDFLibStore if available."""
        if (
            self.use_rdflib_store
            and self.rdflib_store
            and hasattr(self.rdflib_store, "get_all_vectors")
        ):
            return self.rdflib_store.get_all_vectors()
        return []

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

        # Handle content based on its type
        if isinstance(item.content, (str, int, float, bool)):
            # Simple types can be stored directly
            self.graph.add((item_uri, DEVSYNTH.content, Literal(item.content)))
            # Add a flag to indicate this is a simple type
            self.graph.add((item_uri, DEVSYNTH.content_type, Literal("simple")))
        else:
            try:
                # Complex objects need to be serialized to JSON
                json_content = json.dumps(item.content)
                self.graph.add((item_uri, DEVSYNTH.content, Literal(json_content)))
                # Add a flag to indicate this is a JSON-serialized object
                self.graph.add((item_uri, DEVSYNTH.content_type, Literal("json")))
                logger.debug(f"Serialized complex content to JSON for item {item.id}")
            except (TypeError, ValueError) as e:
                # If serialization fails, store as string and log a warning
                logger.warning(
                    f"Failed to serialize content to JSON for item {item.id}: {e}"
                )
                self.graph.add((item_uri, DEVSYNTH.content, Literal(str(item.content))))
                self.graph.add((item_uri, DEVSYNTH.content_type, Literal("string")))

        # Handle memory_type which could be an enum or a string
        memory_type_value = (
            item.memory_type.value
            if hasattr(item.memory_type, "value")
            else str(item.memory_type)
        )
        self.graph.add((item_uri, DEVSYNTH.memory_type, Literal(memory_type_value)))

        # Add metadata
        for key, value in item.metadata.items():
            # Handle metadata values based on their type
            if isinstance(value, (str, int, float, bool)):
                # Simple types can be stored directly
                self.graph.add((item_uri, DEVSYNTH[key], Literal(value)))
            else:
                try:
                    # Complex objects need to be serialized to JSON
                    json_value = json.dumps(value)
                    self.graph.add((item_uri, DEVSYNTH[key], Literal(json_value)))
                    # Add a flag to indicate this is a JSON-serialized value
                    self.graph.add((item_uri, DEVSYNTH[f"{key}_type"], Literal("json")))
                    logger.debug(
                        f"Serialized complex metadata value for key {key} to JSON for item {item.id}"
                    )
                except (TypeError, ValueError) as e:
                    # If serialization fails, skip this metadata
                    logger.warning(
                        f"Failed to serialize metadata value for key {key} to JSON for item {item.id}: {e}"
                    )

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
        content_str = str(self.graph.value(item_uri, DEVSYNTH.content))
        memory_type_value = str(self.graph.value(item_uri, DEVSYNTH.memory_type))
        memory_type = MemoryType(memory_type_value)

        # Get content type
        content_type = self.graph.value(item_uri, DEVSYNTH.content_type)
        content_type = (
            str(content_type) if content_type else "simple"
        )  # Default to simple for backward compatibility

        # Process content based on its type
        if content_type == "json":
            try:
                # Deserialize JSON content
                content = json.loads(content_str)
                logger.debug(f"Deserialized JSON content for item {item_id}")
            except json.JSONDecodeError as e:
                # If deserialization fails, use the string content
                logger.warning(
                    f"Failed to deserialize JSON content for item {item_id}: {e}"
                )
                content = content_str
        else:
            # For simple or string types, use the content as is
            content = content_str

        # Get metadata
        metadata = {}
        metadata_types = {}

        # First pass: collect all metadata and their types
        for s, p, o in self.graph.triples((item_uri, None, None)):
            # Skip non-metadata properties
            if p in [
                RDF.type,
                DEVSYNTH.id,
                DEVSYNTH.content,
                DEVSYNTH.memory_type,
                DEVSYNTH.content_type,
            ]:
                continue

            # Extract the property name from the URI
            prop_name = p.split("/")[-1]

            # Check if this is a type indicator
            if prop_name.endswith("_type"):
                base_prop = prop_name[:-5]  # Remove "_type" suffix
                metadata_types[base_prop] = o.toPython()
            else:
                metadata[prop_name] = o.toPython()

        # Second pass: process metadata values based on their types
        for key, value in list(metadata.items()):
            if key in metadata_types and metadata_types[key] == "json":
                try:
                    # Deserialize JSON metadata
                    metadata[key] = json.loads(value)
                    logger.debug(
                        f"Deserialized JSON metadata for key {key} in item {item_id}"
                    )
                except json.JSONDecodeError as e:
                    # If deserialization fails, keep the string value
                    logger.warning(
                        f"Failed to deserialize JSON metadata for key {key} in item {item_id}: {e}"
                    )

        # Remove type indicators from metadata
        for key in list(metadata.keys()):
            if key.endswith("_type"):
                del metadata[key]

        # Create and return the memory item
        return MemoryItem(
            id=item_id, content=content, memory_type=memory_type, metadata=metadata
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

            existing_uri = URIRef(f"{MEMORY}{item.id}")
            if (existing_uri, RDF.type, DEVSYNTH.MemoryItem) in self.graph:
                self.graph.remove((existing_uri, None, None))

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
                logger.info(
                    f"Retrieved memory item with ID {item_id} from Graph Memory Adapter"
                )
            else:
                logger.warning(
                    f"Memory item with ID {item_id} not found in Graph Memory Adapter"
                )

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
                memory_type_value = (
                    item.memory_type.value
                    if hasattr(item.memory_type, "value")
                    else str(item.memory_type)
                )
                logger.debug(
                    f"Checking item with ID: {item.id}, memory_type: {memory_type_value}, metadata: {item.metadata}"
                )

                for key, value in query.items():
                    if key == "type":
                        # Check if the memory_type matches the value
                        # Convert both memory_type and value to string for comparison
                        value_str = (
                            value.value if hasattr(value, "value") else str(value)
                        )
                        if memory_type_value != value_str:
                            # Also check if the type is in metadata
                            if key in item.metadata and item.metadata[key] == value_str:
                                logger.debug(
                                    f"Item {item.id} matches type in metadata: {item.metadata[key]} == {value_str}"
                                )
                            else:
                                logger.debug(
                                    f"Item {item.id} doesn't match type: {memory_type_value} != {value_str}"
                                )
                                match = False
                                break
                    elif key in item.metadata:
                        if item.metadata[key] != value:
                            logger.debug(
                                f"Item {item.id} doesn't match metadata {key}: {item.metadata[key]} != {value}"
                            )
                            match = False
                            break
                    else:
                        logger.debug(f"Item {item.id} doesn't have metadata key: {key}")
                        match = False
                        break

                if match:
                    logger.debug(f"Item {item.id} matches the query")
                    results.append(item)

            logger.info(
                f"Found {len(results)} matching memory items in Graph Memory Adapter"
            )
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
                logger.warning(
                    f"Memory item with ID {item_id} not found in Graph Memory Adapter"
                )
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

            logger.info(
                f"Deleted memory item with ID {item_id} from Graph Memory Adapter"
            )
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
                logger.warning(
                    f"Memory item with ID {item_id} not found in Graph Memory Adapter"
                )
                return []

            # Get related items
            related_uris = list(self.graph.objects(item_uri, DEVSYNTH.relatedTo))
            related_items = []

            for related_uri in related_uris:
                item = self._triples_to_memory_item(related_uri)
                if item:
                    related_items.append(item)

            logger.info(
                f"Found {len(related_items)} items related to {item_id} in Graph Memory Adapter"
            )
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

    def add_memory_volatility(
        self,
        decay_rate: float = 0.1,
        threshold: float = 0.5,
        advanced_controls: bool = False,
    ) -> None:
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
                """ % (
                    decay_rate,
                    threshold,
                )

                self.graph.update(sparql_update)
                logger.info(
                    f"Added advanced memory volatility controls with decay rate {decay_rate} and threshold {threshold}"
                )
            else:
                # Use basic RDFLib approach
                for s, p, o in self.graph.triples(
                    (None, RDF.type, DEVSYNTH.MemoryItem)
                ):
                    # Check if confidence already exists
                    if (s, DEVSYNTH.confidence, None) not in self.graph:
                        # Add initial confidence of 1.0
                        self.graph.add((s, DEVSYNTH.confidence, Literal(1.0)))

                        # Add decay rate and threshold
                        self.graph.add((s, DEVSYNTH.decayRate, Literal(decay_rate)))
                        self.graph.add(
                            (s, DEVSYNTH.confidenceThreshold, Literal(threshold))
                        )

            # Save the graph
            self._save_graph()

            logger.info(
                f"Added memory volatility controls with decay rate {decay_rate} and threshold {threshold}"
            )
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
                        last_access_str = str(last_access).replace("Z", "")
                        if "+" in last_access_str:
                            last_access_str = last_access_str.split("+")[0]
                        last_access_date = datetime.fromisoformat(last_access_str)
                        days_since_access = (now - last_access_date).days
                        # Increase decay for items not accessed recently
                        time_factor = min(2.0, 1.0 + (days_since_access / 30.0))

                    # Calculate access frequency factor
                    access_factor = max(0.5, 1.0 - (access_count / 100.0))

                    # Calculate relationship factor
                    relationship_count = len(
                        list(self.graph.triples((item_uri, DEVSYNTH.relatedTo, None)))
                    )
                    relationship_factor = max(0.5, 1.0 - (relationship_count / 20.0))

                    # Apply combined decay
                    combined_decay_rate = (
                        decay_rate * time_factor * access_factor * relationship_factor
                    )
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

                logger.info(
                    f"Applied advanced memory decay, {len(volatile_items)} items are now volatile"
                )
            else:
                # Use basic RDFLib approach
                for s, p, o in self.graph.triples((None, DEVSYNTH.confidence, None)):
                    # Get current confidence
                    confidence = float(o)

                    # Get decay rate and threshold
                    decay_rate = float(
                        self.graph.value(s, DEVSYNTH.decayRate, default=Literal(0.1))
                    )
                    threshold = float(
                        self.graph.value(
                            s, DEVSYNTH.confidenceThreshold, default=Literal(0.5)
                        )
                    )

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

            logger.info(
                f"Applied memory decay, {len(volatile_items)} items are now volatile"
            )
            return volatile_items
        except Exception as e:
            logger.error(f"Failed to apply memory decay: {e}")
            raise MemoryStoreError(f"Failed to apply memory decay: {e}")

    def store_with_edrr_phase(
        self,
        content: Any,
        memory_type: Union[str, MemoryType],
        edrr_phase: str,
        metadata: Dict[str, Any] = None,
    ) -> str:
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

        # Make a copy of the metadata to avoid modifying the original
        metadata_copy = metadata.copy()
        metadata_copy["edrr_phase"] = edrr_phase

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
            id="", content=content, memory_type=memory_type_enum, metadata=metadata_copy
        )

        # Store the memory item
        return self.store(memory_item)

    def retrieve_with_edrr_phase(
        self,
        item_type: str,
        edrr_phase: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Any:
        """
        Retrieve an item stored with a specific EDRR phase.

        Args:
            item_type: Identifier of the stored item.
            edrr_phase: The phase tag used during storage.
            metadata: Optional additional metadata for adapter queries.

        Returns:
            The retrieved item or an empty dictionary if not found.
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
                        if item.metadata.get(key) != value:
                            match = False
                            break

                if match:
                    matching_items.append(item)
                    logger.debug(
                        f"Found matching item: {item.id}, Type: {item.memory_type}, Metadata: {item.metadata}"
                    )

            if matching_items:
                # Return the content of the first matching item
                logger.info(
                    f"Retrieved item with type {item_type}, EDRR phase {edrr_phase}, and metadata {metadata}"
                )
                return matching_items[0].content

            logger.debug(
                f"No items found with type {item_type} and EDRR phase {edrr_phase}"
            )
            return {}
        except Exception as e:
            logger.error(f"Failed to retrieve item with EDRR phase: {e}")
            return {}

    def integrate_with_store(
        self,
        other_store: Union[MemoryStore, VectorStore],
        sync_mode: str = "bidirectional",
    ) -> None:
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
            logger.info(
                f"Integrating with {type(other_store).__name__} in {sync_mode} mode"
            )

            # Use duck typing to check if other_store has MemoryStore-like methods
            has_memory_store_methods = (
                hasattr(other_store, "store")
                and hasattr(other_store, "retrieve")
                and hasattr(other_store, "search")
            )

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
                            logger.debug(
                                f"Imported item {item.id} from {type(other_store).__name__}"
                            )

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
                            logger.debug(
                                f"Exported item {item.id} to {type(other_store).__name__}"
                            )

            # Use duck typing to check if other_store behaves like a VectorStore
            has_vector_store_methods = hasattr(other_store, "store_vector") and hasattr(
                other_store, "retrieve_vector"
            )

            if has_vector_store_methods and hasattr(
                other_store, "get_collection_stats"
            ):
                try:
                    stats = other_store.get_collection_stats()
                    logger.info(f"Vector store stats before integration: {stats}")
                except Exception as e:  # pragma: no cover - logging
                    logger.warning(f"Failed to retrieve vector store stats: {e}")

            if has_vector_store_methods and self.use_rdflib_store and self.rdflib_store:
                # Import vectors from the other store
                if sync_mode in ["import", "bidirectional"]:
                    vectors: List[MemoryVector] = []
                    if hasattr(other_store, "get_all_vectors"):
                        vectors = other_store.get_all_vectors()
                    elif hasattr(other_store, "vectors"):
                        vectors = list(other_store.vectors.values())

                    for vec in vectors:
                        if not self.rdflib_store.retrieve_vector(vec.id):
                            self.rdflib_store.store_vector(vec)
                            logger.debug(
                                f"Imported vector {vec.id} from {type(other_store).__name__}"
                            )

                # Export vectors to the other store
                if sync_mode in ["export", "bidirectional"]:
                    local_vectors = (
                        self.rdflib_store.get_all_vectors()
                        if hasattr(self.rdflib_store, "get_all_vectors")
                        else []
                    )
                    for vec in local_vectors:
                        existing = other_store.retrieve_vector(vec.id)
                        if not existing:
                            other_store.store_vector(vec)
                            logger.debug(
                                f"Exported vector {vec.id} to {type(other_store).__name__}"
                            )

            logger.info(f"Integration with {type(other_store).__name__} completed")
        except Exception as e:
            logger.error(f"Failed to integrate with {type(other_store).__name__}: {e}")
            raise MemoryStoreError(
                f"Failed to integrate with {type(other_store).__name__}: {e}"
            )
