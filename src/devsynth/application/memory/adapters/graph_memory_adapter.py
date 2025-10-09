"""
Graph Memory Adapter Module

This module provides a memory adapter that handles relationships between memory items
using a graph-based approach with RDFLib. It integrates with RDFLibStore for enhanced
functionality and improved integration between different memory stores.
"""

from __future__ import annotations

import importlib
import json
import os
import uuid
from collections import deque
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from types import ModuleType
from typing import TYPE_CHECKING, Any, TypedDict, cast

from devsynth.exceptions import MemoryStoreError

from ....domain.interfaces.memory import MemoryStore, VectorStore
from ....domain.models.memory import MemoryItem, MemoryType, MemoryVector
from ....exceptions import MemoryTransactionError
from ....logging_setup import DevSynthLogger
from ..dto import MemoryRecord, build_memory_record
from ..rdflib_store import RDFLibStore

if TYPE_CHECKING:  # pragma: no cover - imported for static analysis only
    import rdflib as rdflib_module
    from rdflib import Graph as GraphType
    from rdflib import Literal as LiteralType
    from rdflib import Namespace as NamespaceType
    from rdflib import URIRef as URIRefType
    from rdflib.namespace import DC as DCType
    from rdflib.namespace import FOAF as FOAFType
else:  # pragma: no cover - runtime fallbacks when rdflib is absent
    GraphType = LiteralType = NamespaceType = URIRefType = object  # type: ignore[assignment]
    DCType = FOAFType = object  # type: ignore[assignment]

rdflib: ModuleType | None
RDF: Any
Graph: type[GraphType] | None
Literal: type[LiteralType] | None
Namespace: type[NamespaceType] | None
URIRef: type[URIRefType] | None
DC: DCType | None
FOAF: FOAFType | None

try:  # pragma: no cover - optional dependency
    rdflib = importlib.import_module("rdflib")
    namespace_module = importlib.import_module("rdflib.namespace")
    RDF = getattr(rdflib, "RDF")
    Graph = cast("type[GraphType]", getattr(rdflib, "Graph"))
    Literal = cast("type[LiteralType]", getattr(rdflib, "Literal"))
    Namespace = cast("type[NamespaceType]", getattr(rdflib, "Namespace"))
    URIRef = cast("type[URIRefType]", getattr(rdflib, "URIRef"))
    DC = cast("DCType", getattr(namespace_module, "DC"))
    FOAF = cast("FOAFType", getattr(namespace_module, "FOAF"))
except Exception:  # pragma: no cover - fallback when rdflib is missing
    rdflib = None
    RDF = None
    Graph = Literal = Namespace = URIRef = None
    DC = FOAF = None

logger = DevSynthLogger(__name__)

# Define custom namespaces
if Namespace is not None:
    _devsynth_namespace = Namespace("http://devsynth.ai/ontology/")
    _memory_namespace = Namespace("http://devsynth.ai/memory/")
else:  # pragma: no cover - Namespace unavailable without rdflib
    _devsynth_namespace = None
    _memory_namespace = None

DEVSYNTH = cast("NamespaceType", _devsynth_namespace)
MEMORY = cast("NamespaceType", _memory_namespace)


class _GraphTransactionState(TypedDict):
    snapshot: str
    prepared: bool


class GraphMemoryAdapter(MemoryStore):
    """
    Graph Memory Adapter handles relationships between memory items using a graph-based approach.

    It implements the MemoryStore interface and provides additional methods for querying
    relationships between items. This implementation uses RDFLib to store and retrieve
    memory items and their relationships as RDF triples.

    This adapter can optionally integrate with RDFLibStore for enhanced functionality
    such as vector storage and retrieval, SPARQL queries, and improved memory volatility controls.
    """

    backend_type = "graph"

    @staticmethod
    def _ensure_core_dependencies() -> None:
        if Graph is None or URIRef is None or Literal is None or RDF is None:
            raise MemoryStoreError(
                "GraphMemoryAdapter requires the 'rdflib' package. "
                "Install it to enable graph memory support."
            )
        if _devsynth_namespace is None or _memory_namespace is None:
            raise MemoryStoreError(
                "Required RDF namespaces are unavailable. Ensure rdflib is installed."
            )

    @staticmethod
    def _require_graph_class() -> type[GraphType]:
        GraphMemoryAdapter._ensure_core_dependencies()
        return cast("type[GraphType]", Graph)

    @staticmethod
    def _require_uri_ref_class() -> type[URIRefType]:
        GraphMemoryAdapter._ensure_core_dependencies()
        return cast("type[URIRefType]", URIRef)

    def _create_graph_instance(self) -> GraphType:
        graph_cls = self._require_graph_class()
        return graph_cls()

    def _bind_default_namespaces(self) -> None:
        self.graph.bind("devsynth", DEVSYNTH)
        self.graph.bind("memory", MEMORY)
        if FOAF is not None:
            self.graph.bind("foaf", FOAF)
        if DC is not None:
            self.graph.bind("dc", DC)

    def _memory_uri(self, identifier: str | uuid.UUID) -> URIRefType:
        uri_cls = self._require_uri_ref_class()
        return uri_cls(f"{MEMORY}{str(identifier)}")

    def __init__(self, base_path: str | None = None, use_rdflib_store: bool = False):
        """
        Initialize the Graph Memory Adapter.

        Args:
            base_path: Optional path to store the RDF graph. If not provided,
                      an in-memory graph will be used.
            use_rdflib_store: Whether to use RDFLibStore for enhanced functionality.
                             If True, a RDFLibStore instance will be created and used
                             for advanced operations.
        """
        self._ensure_core_dependencies()

        self.base_path = base_path
        self.use_rdflib_store = use_rdflib_store
        self._active_transactions: dict[str, _GraphTransactionState] = {}
        self._transaction_stack: list[str] = []

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
            self.graph = self._create_graph_instance()
            self._bind_default_namespaces()

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
            # Ensure the RDFLibStore uses the same graph file
            self.rdflib_store.graph_file = getattr(
                self,
                "graph_file",
                os.path.join(self.base_path or "", "graph_memory.ttl"),
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
    def transaction(self) -> Iterator[None]:
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

        # Create a snapshot of the current state
        snapshot = cast(str, self.graph.serialize(format="turtle"))

        # Store the snapshot with the transaction ID
        self._active_transactions[transaction_id] = {
            "snapshot": snapshot,
            "prepared": False,
        }

        # Also maintain compatibility with the existing transaction stack
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
        logger.debug(
            f"Preparing to commit transaction {transaction_id} in GraphMemoryAdapter"
        )

        # Check if this is an active transaction
        if transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="GraphMemoryAdapter",
                operation="prepare_commit",
            )

        # Mark the transaction as prepared
        self._active_transactions[transaction_id]["prepared"] = True

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
        if transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="GraphMemoryAdapter",
                operation="commit_transaction",
            )

        # Remove the transaction from the active transactions
        del self._active_transactions[transaction_id]

        # Also maintain compatibility with the existing transaction stack
        if self._transaction_stack:
            self._transaction_stack.pop()

        # Save the current state to ensure durability
        self._save_graph()

        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Check if a transaction is currently active.

        Args:
            transaction_id: The ID of the transaction to check.

        Returns:
            ``True`` if the transaction is active, ``False`` otherwise.
        """

        return transaction_id in self._active_transactions

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
        if transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="GraphMemoryAdapter",
                operation="rollback_transaction",
            )

        # Get the snapshot
        snapshot = self._active_transactions[transaction_id]["snapshot"]

        # Restore the graph from the snapshot
        self.graph = self._create_graph_instance()
        self.graph.parse(data=snapshot, format="turtle")

        # Save the restored graph
        self._save_graph()

        # Remove the transaction from the active transactions
        del self._active_transactions[transaction_id]

        # Also maintain compatibility with the existing transaction stack
        if self._transaction_stack:
            self._transaction_stack.pop()

        return True

    def snapshot(self) -> str:
        """
        Create a snapshot of the current state.

        Returns:
            A serialized representation of the graph
        """
        return cast(str, self.graph.serialize(format="turtle"))

    def restore(self, snapshot: str | None) -> bool:
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
            self.graph = self._create_graph_instance()
            self.graph.parse(data=snapshot, format="turtle")
            self._save_graph()
            return True
        except Exception as e:
            logger.error(f"Failed to restore graph from snapshot: {e}")
            return False

    def get_all_vectors(self) -> list[MemoryVector]:
        """Return all vectors from the underlying RDFLibStore if available."""
        if (
            self.use_rdflib_store
            and self.rdflib_store
            and hasattr(self.rdflib_store, "get_all_vectors")
        ):
            return cast(list[MemoryVector], self.rdflib_store.get_all_vectors())
        return []

    def _memory_item_to_triples(self, item: MemoryItem) -> URIRefType:
        """
        Convert a memory item to RDF triples and add them to the graph.

        Args:
            item: The memory item to convert

        Returns:
            The URI reference for the item
        """
        # Create a URI for the item
        item_uri = self._memory_uri(str(item.id))

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

    def _triples_to_memory_item(self, item_uri: URIRef) -> MemoryItem | None:
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

            existing_uri = self._memory_uri(str(item.id))
            if (existing_uri, RDF.type, DEVSYNTH.MemoryItem) in self.graph:
                self.graph.remove((existing_uri, None, None))

            # Convert the item to triples and add to the graph
            item_uri = self._memory_item_to_triples(item)

            # Process relationships
            related_to = item.metadata.get("related_to")
            if related_to:
                related_uri = self._memory_uri(str(related_to))

                # Add the relationship
                self.graph.add((item_uri, DEVSYNTH.relatedTo, related_uri))

                # Add the reverse relationship
                self.graph.add((related_uri, DEVSYNTH.relatedTo, item_uri))

            # Save the graph
            self._save_graph()

            logger.info(f"Stored memory item with ID {item.id} in Graph Memory Adapter")
            return str(item.id)
        except Exception as e:
            logger.error(f"Failed to store memory item: {e}")
            raise MemoryStoreError(f"Failed to store memory item: {e}")

    def retrieve(self, item_id: str) -> MemoryItem | None:
        """
        Retrieve a memory item by ID.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        try:
            # Create a URI for the item
            item_uri = self._memory_uri(item_id)

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

    def search(self, query: Mapping[str, object]) -> list[MemoryRecord]:
        """
        Search for memory items matching the query.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        try:
            results: list[MemoryRecord] = []
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
                    results.append(build_memory_record(item, source=self.backend_type))

            logger.info(
                f"Found {len(results)} matching memory records in Graph Memory Adapter"
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
            item_uri = self._memory_uri(item_id)

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

    def query_related_items(self, item_id: str) -> list[MemoryItem]:
        """
        Query for items related to a given item ID.

        Args:
            item_id: The ID of the item to find related items for

        Returns:
            A list of related memory items
        """
        try:
            # Create a URI for the item
            item_uri = self._memory_uri(item_id)

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

    def get_all_relationships(self) -> dict[str, set[str]]:
        """
        Get all relationships in the graph.

        Returns:
            A dictionary of relationships by item ID
        """
        try:
            relationships: dict[str, set[str]] = {}

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

            logger.info("Retrieved all relationships from Graph Memory Adapter")
            return relationships
        except Exception as e:
            logger.error(f"Failed to get all relationships: {e}")
            raise MemoryStoreError(f"Failed to get all relationships: {e}")

    def traverse_graph(
        self,
        start_id: str,
        max_depth: int = 1,
        *,
        include_research: bool = False,
    ) -> set[str]:
        """
        Traverse related nodes starting from the given item ID.

        Args:
            start_id: The ID of the starting node.
            max_depth: Maximum depth to traverse.

        Returns:
            A set of item IDs reachable within the given depth, excluding the
            starting node.
        """
        if rdflib is None or max_depth <= 0:
            return set()

        try:
            start_uri = self._resolve_traversal_uri(start_id)
            if start_uri is None:
                return set()

            visited: set[URIRef] = {start_uri}
            queue: deque[tuple[URIRef, int]] = deque([(start_uri, 0)])
            discovered: set[str] = set()

            predicates = tuple(self._traversal_predicates())

            while queue:
                current, depth = queue.popleft()
                if depth >= max_depth:
                    continue

                for predicate in predicates:
                    for _, _, neighbor in self.graph.triples(
                        (current, predicate, None)
                    ):
                        if neighbor in visited:
                            continue

                        if self._should_skip_traversal_target(
                            neighbor, include_research=include_research
                        ):
                            visited.add(neighbor)
                            continue

                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))

                        identifier = self._uri_to_identifier(neighbor)
                        if identifier and neighbor != start_uri:
                            discovered.add(identifier)

            logger.info(
                "Traversed graph from %s to depth %s and found %s nodes",
                start_id,
                max_depth,
                len(discovered),
            )
            return discovered
        except Exception as e:
            logger.error(f"Failed to traverse graph: {e}")
            raise MemoryStoreError(f"Failed to traverse graph: {e}")

    # ------------------------------------------------------------------
    # Traversal helpers
    # ------------------------------------------------------------------

    def _resolve_traversal_uri(self, node_id: str) -> URIRef | None:
        """Resolve ``node_id`` into a URI present in the graph."""

        candidate = self._memory_uri(node_id)
        if list(self.graph.triples((candidate, None, None))):
            return candidate
        return None

    def _traversal_predicates(self) -> tuple[URIRef, ...]:
        """Return the predicates followed during traversal."""

        return (DEVSYNTH.relatedTo,)

    def _should_skip_traversal_target(
        self, uri: URIRef, *, include_research: bool
    ) -> bool:
        """Return True when ``uri`` should be excluded from traversal results."""

        return False

    def _uri_to_identifier(self, uri: URIRef) -> str | None:
        """Convert a node URI into its stored identifier."""

        value = str(uri)
        if value.startswith(str(MEMORY)):
            return value[len(str(MEMORY)) :]
        identifier_literal = self.graph.value(uri, DEVSYNTH.id)
        if identifier_literal is not None:
            return str(identifier_literal)
        return value

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

                    INSERT {{
                        ?item devsynth:confidence "1.0"^^<http://www.w3.org/2001/XMLSchema#float> .
                        ?item devsynth:decayRate "{:f}"^^<http://www.w3.org/2001/XMLSchema#float> .
                        ?item devsynth:confidenceThreshold "{:f}"^^<http://www.w3.org/2001/XMLSchema#float> .
                        ?item devsynth:lastAccessTime ?now .
                        ?item devsynth:accessCount "0"^^<http://www.w3.org/2001/XMLSchema#integer> .
                        ?item devsynth:volatilityEnabled "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .
                    }}
                    WHERE {{
                        ?item rdf:type devsynth:MemoryItem .
                        FILTER NOT EXISTS {{ ?item devsynth:confidence ?conf }}
                        BIND(NOW() as ?now)
                    }}
                """.format(
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

    def apply_memory_decay(self, advanced_decay: bool = False) -> list[str]:
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
        content: object,
        memory_type: MemoryType,
        edrr_phase: str,
        metadata: Mapping[str, object] | None = None,
    ) -> str:
        """
        Store a memory item with an EDRR phase.

        Args:
            content: The content of the memory item
            memory_type: The type of memory (e.g., CODE, REQUIREMENT)
            edrr_phase: The EDRR phase (EXPAND, DIFFERENTIATE, REFINE, RETROSPECT)
            metadata: Additional metadata for the memory item

        Returns:
            The ID of the stored memory item
        """
        # Create metadata with EDRR phase
        metadata_dict = dict(metadata) if metadata else {}
        metadata_dict["edrr_phase"] = edrr_phase

        # Create the memory item
        memory_item = MemoryItem(
            id="", content=content, memory_type=memory_type, metadata=metadata_dict
        )

        # Store the memory item
        return self.store(memory_item)

    def retrieve_with_edrr_phase(
        self,
        item_type: str,
        edrr_phase: str,
        metadata: Mapping[str, object] | None = None,
    ) -> object:
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
        other_store: MemoryStore | VectorStore[MemoryVector],
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
                    vectors: list[MemoryVector] = []
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
