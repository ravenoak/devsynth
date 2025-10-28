from __future__ import annotations

"""
RDFLib implementation of MemoryStore and VectorStore.

This implementation uses RDFLib to store and retrieve memory items and vectors
as RDF triples in a knowledge graph. It also supports SPARQL queries for
advanced search capabilities.
"""

import json
import os
import uuid
from datetime import datetime
from types import ModuleType
from typing import TYPE_CHECKING, Optional, cast
from collections.abc import Callable, Sequence

import numpy as np
import tiktoken

if TYPE_CHECKING:  # pragma: no cover - imported for static analysis only
    import rdflib as rdflib_module
    from rdflib import RDF as RDFType
    from rdflib import RDFS as RDFSSType
    from rdflib import XSD as XSDType
    from rdflib import Graph as GraphType
    from rdflib import Literal as LiteralType
    from rdflib import Namespace as NamespaceType
    from rdflib import URIRef as URIRefType
    from rdflib.namespace import DC as DCType
    from rdflib.namespace import FOAF as FOAFType
else:  # pragma: no cover - runtime fallbacks when rdflib is absent
    GraphType = LiteralType = NamespaceType = URIRefType = object  # type: ignore[assignment]
    RDFType = RDFSSType = XSDType = object  # type: ignore[assignment]
    DCType = FOAFType = object  # type: ignore[assignment]

rdflib: ModuleType | None = None
Graph: type[GraphType] | None = None
Literal: type[LiteralType] | None = None
Namespace: Callable[[str], NamespaceType] | None = None
URIRef: type[URIRefType] | None = None
RDF: RDFType | None = None
RDFS: RDFSSType | None = None
XSD: XSDType | None = None
DC: DCType | None = None
FOAF: FOAFType | None = None

try:  # pragma: no cover - optional dependency
    import rdflib as _rdflib
    from rdflib import RDF as _RDF
    from rdflib import RDFS as _RDFS
    from rdflib import XSD as _XSD
    from rdflib import Graph as _Graph
    from rdflib import Literal as _Literal
    from rdflib import Namespace as _Namespace
    from rdflib import URIRef as _URIRef
    from rdflib.namespace import DC as _DC
    from rdflib.namespace import FOAF as _FOAF

    _Namespace("test")
except Exception:  # pragma: no cover - graceful fallback for tests
    pass
else:
    rdflib = _rdflib
    Graph = cast("type[GraphType]", _Graph)
    Literal = cast("type[LiteralType]", _Literal)
    Namespace = cast("Callable[[str], NamespaceType]", _Namespace)
    URIRef = cast("type[URIRefType]", _URIRef)
    RDF = cast("RDFType", _RDF)
    RDFS = cast("RDFSSType", _RDFS)
    XSD = cast("XSDType", _XSD)
    DC = cast("DCType", _DC)
    FOAF = cast("FOAFType", _FOAF)


from devsynth.exceptions import (
    DevSynthError,
    MemoryError,
    MemoryItemNotFoundError,
    MemoryStoreError,
)
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.memory import MemoryStore, SupportsTransactions, VectorStore
from ...domain.models.memory import MemoryItem, MemoryType, MemoryVector
from .dto import (
    MemoryMetadata,
    MemoryRecord,
    MemorySearchQuery,
    VectorStoreStats,
    build_memory_record,
)

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Define namespaces for the RDF graph when rdflib is available
DEVSYNTH: NamespaceType | None
MEMORY: NamespaceType | None
if Namespace is not None:
    DEVSYNTH = Namespace("https://github.com/ravenoak/devsynth/ontology#")
    MEMORY = Namespace("https://github.com/ravenoak/devsynth/ontology/memory#")
else:
    DEVSYNTH = None
    MEMORY = None


class RDFLibStore(MemoryStore, SupportsTransactions, VectorStore[MemoryVector]):
    """
    RDFLib implementation of the MemoryStore and VectorStore interfaces.

    This class uses RDFLib to store and retrieve memory items and vectors
    as RDF triples in a knowledge graph. It also supports SPARQL queries for
    advanced search capabilities.
    """

    _literal: type[LiteralType]
    _uri_ref: type[URIRefType]
    _rdf: RDFType
    _xsd: XSDType
    _dc: DCType
    _foaf: FOAFType
    _memory_ns: NamespaceType
    _devsynth_ns: NamespaceType
    graph: GraphType

    def __init__(self, base_path: str):
        """
        Initialize a RDFLibStore.

        Args:
            base_path: Base path for storing the RDF graph file
        """
        self.base_path = base_path
        self.graph_file = os.path.join(self.base_path, "memory.ttl")
        self.token_count = 0

        # Ensure the directory exists
        os.makedirs(self.base_path, exist_ok=True)

        graph_cls = Graph
        literal_cls = Literal
        uri_ref_cls = URIRef
        rdf_ns = RDF
        xsd_ns = XSD
        dc_ns = DC
        foaf_ns = FOAF
        devsynth_ns = DEVSYNTH
        memory_ns = MEMORY

        missing_aliases = [
            name
            for name, value in (
                ("Graph", graph_cls),
                ("Literal", literal_cls),
                ("URIRef", uri_ref_cls),
                ("RDF", rdf_ns),
                ("XSD", xsd_ns),
                ("DC", dc_ns),
                ("FOAF", foaf_ns),
                ("DEVSYNTH", devsynth_ns),
                ("MEMORY", memory_ns),
            )
            if value is None
        ]

        if missing_aliases:
            missing = ", ".join(missing_aliases)
            raise MemoryStoreError(
                "rdflib is required to initialize RDFLibStore",
                store_type="rdflib",
                operation="initialize",
                original_error=ImportError(f"Missing rdflib aliases: {missing}"),
            )

        assert graph_cls is not None
        assert literal_cls is not None
        assert uri_ref_cls is not None
        assert rdf_ns is not None
        assert xsd_ns is not None
        assert dc_ns is not None
        assert foaf_ns is not None
        assert devsynth_ns is not None
        assert memory_ns is not None

        self.graph = graph_cls()
        self._literal = literal_cls
        self._uri_ref = uri_ref_cls
        self._rdf = rdf_ns
        self._xsd = xsd_ns
        self._dc = dc_ns
        self._foaf = foaf_ns
        self._devsynth_ns = devsynth_ns
        self._memory_ns = memory_ns

        # Bind namespaces to the graph for more readable serialization
        self.graph.bind("devsynth", self._devsynth_ns)
        self.graph.bind("memory", self._memory_ns)
        self.graph.bind("foaf", self._foaf)
        self.graph.bind("dc", self._dc)

        # Initialize the tokenizer for token counting
        self.tokenizer: object | None = None
        if tiktoken is not None:
            try:
                self.tokenizer = tiktoken.get_encoding(
                    "cl100k_base"
                )  # OpenAI's encoding
            except Exception as e:
                logger.warning(
                    f"Failed to initialize tokenizer: {e}. Token counting will be approximate."
                )

        # Load the graph from file if it exists
        self._load_graph()

    def _load_graph(self) -> None:
        """Load the RDF graph from file if it exists."""
        try:
            if os.path.exists(self.graph_file):
                self.graph.parse(self.graph_file, format="turtle")
                logger.info(f"Loaded RDF graph from {self.graph_file}")
            else:
                logger.info(f"No existing RDF graph found at {self.graph_file}")
        except Exception as e:
            logger.error(f"Failed to load RDF graph: {e}")
            raise MemoryStoreError(
                "Failed to load RDF graph",
                store_type="rdflib",
                operation="load_graph",
                original_error=e,
            )

    def _save_graph(self) -> None:
        """Save the RDF graph to file."""
        try:
            self.graph.serialize(destination=self.graph_file, format="turtle")
            logger.info(f"Saved RDF graph to {self.graph_file}")
        except Exception as e:
            logger.error(f"Failed to save RDF graph: {e}")
            raise MemoryStoreError(
                "Failed to save RDF graph",
                store_type="rdflib",
                operation="save_graph",
                original_error=e,
            )

    # transactional API ---------------------------------------------------
    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a new transaction.

        RDFLibStore currently treats transactions as no-ops but returns a
        generated identifier for interface compatibility.

        Args:
            transaction_id: Optional transaction identifier.

        Returns:
            The transaction identifier.
        """

        return transaction_id or str(uuid.uuid4())

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a previously started transaction.

        Transactions are treated as no-ops and always succeed.
        """

        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a previously started transaction.

        Transactions are treated as no-ops and always succeed.
        """

        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Check whether a transaction is active.

        Since transactions are no-ops, this always returns ``False``.
        """

        return False

    def _count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text
        """
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        else:
            # Approximate token count (roughly 4 characters per token)
            return len(text) // 4

    def _memory_item_to_triples(self, item: MemoryItem) -> None:
        """
        Convert a MemoryItem to RDF triples and add them to the graph.

        Args:
            item: The MemoryItem to convert
        """
        # Create a URI for the memory item
        item_uri = self._uri_ref(f"{self._memory_ns}item/{item.id}")

        # Add basic triples for the memory item
        self.graph.add((item_uri, self._rdf.type, self._memory_ns.MemoryItem))
        self.graph.add((item_uri, self._memory_ns.id, self._literal(item.id)))
        self.graph.add(
            (item_uri, self._memory_ns.content, self._literal(str(item.content)))
        )
        self.graph.add(
            (
                item_uri,
                self._memory_ns.memoryType,
                self._literal(item.memory_type.value),
            )
        )
        self.graph.add(
            (
                item_uri,
                self._memory_ns.createdAt,
                self._literal(item.created_at.isoformat(), datatype=self._xsd.dateTime),
            )
        )

        # Add metadata as triples
        if item.metadata:
            metadata_uri = self._uri_ref(f"{self._memory_ns}metadata/{item.id}")
            self.graph.add((item_uri, self._memory_ns.hasMetadata, metadata_uri))
            self.graph.add((metadata_uri, self._rdf.type, self._memory_ns.Metadata))

            for key, value in item.metadata.items():
                # Convert the key to a valid predicate name (replace spaces, etc.)
                predicate_name = key.replace(" ", "_").lower()
                predicate = self._memory_ns[predicate_name]

                # Add the metadata triple
                if isinstance(value, (int, float, bool)):
                    self.graph.add((metadata_uri, predicate, self._literal(value)))
                else:
                    self.graph.add((metadata_uri, predicate, self._literal(str(value))))

    def _triples_to_memory_item(self, item_uri: URIRefType) -> MemoryItem | None:
        """
        Convert RDF triples to a MemoryItem.

        Args:
            item_uri: The URI of the memory item

        Returns:
            The converted MemoryItem, or None if not found
        """
        # Check if the item exists
        if (item_uri, self._rdf.type, self._memory_ns.MemoryItem) not in self.graph:
            return None

        # Get the basic properties
        item_id = str(self.graph.value(item_uri, self._memory_ns.id))
        content = str(self.graph.value(item_uri, self._memory_ns.content))
        memory_type_value = str(self.graph.value(item_uri, self._memory_ns.memoryType))
        memory_type = MemoryType(memory_type_value)
        created_at_str = str(self.graph.value(item_uri, self._memory_ns.createdAt))
        created_at = datetime.fromisoformat(created_at_str)

        # Get the metadata
        metadata: dict[str, object] = {}
        metadata_uri = self.graph.value(item_uri, self._memory_ns.hasMetadata)
        if metadata_uri:
            for s, p, o in self.graph.triples((metadata_uri, None, None)):
                if p != self._rdf.type:
                    # Extract the predicate name from the URI
                    predicate_name = p.split("#")[-1]
                    metadata[predicate_name] = o.toPython()

        # Create and return the MemoryItem
        return MemoryItem(
            id=item_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            created_at=created_at,
        )

    def _memory_vector_to_triples(self, vector: MemoryVector) -> None:
        """
        Convert a MemoryVector to RDF triples and add them to the graph.

        Args:
            vector: The MemoryVector to convert
        """
        # Create a URI for the memory vector
        vector_uri = self._uri_ref(f"{self._memory_ns}vector/{vector.id}")

        # Add basic triples for the memory vector
        self.graph.add((vector_uri, self._rdf.type, self._memory_ns.MemoryVector))
        self.graph.add((vector_uri, self._memory_ns.id, self._literal(vector.id)))
        self.graph.add(
            (vector_uri, self._memory_ns.content, self._literal(str(vector.content)))
        )
        self.graph.add(
            (
                vector_uri,
                self._memory_ns.createdAt,
                self._literal(
                    vector.created_at.isoformat(), datatype=self._xsd.dateTime
                ),
            )
        )

        # Add embedding as a JSON string
        embedding_json = json.dumps(vector.embedding)
        self.graph.add(
            (vector_uri, self._memory_ns.embedding, self._literal(embedding_json))
        )

        # Add metadata as triples
        if vector.metadata:
            metadata_uri = self._uri_ref(f"{self._memory_ns}metadata/{vector.id}")
            self.graph.add((vector_uri, self._memory_ns.hasMetadata, metadata_uri))
            self.graph.add((metadata_uri, self._rdf.type, self._memory_ns.Metadata))

            for key, value in vector.metadata.items():
                # Convert the key to a valid predicate name (replace spaces, etc.)
                predicate_name = key.replace(" ", "_").lower()
                predicate = self._memory_ns[predicate_name]

                # Add the metadata triple
                if isinstance(value, (int, float, bool)):
                    self.graph.add((metadata_uri, predicate, self._literal(value)))
                else:
                    self.graph.add((metadata_uri, predicate, self._literal(str(value))))

    def _triples_to_memory_vector(
        self, vector_uri: URIRefType
    ) -> MemoryVector | None:
        """
        Convert RDF triples to a MemoryVector.

        Args:
            vector_uri: The URI of the memory vector

        Returns:
            The converted MemoryVector, or None if not found
        """
        # Check if the vector exists
        if (vector_uri, self._rdf.type, self._memory_ns.MemoryVector) not in self.graph:
            return None

        # Get the basic properties
        vector_id = str(self.graph.value(vector_uri, self._memory_ns.id))
        content = str(self.graph.value(vector_uri, self._memory_ns.content))
        embedding_json = str(self.graph.value(vector_uri, self._memory_ns.embedding))
        embedding = json.loads(embedding_json)
        created_at_str = str(self.graph.value(vector_uri, self._memory_ns.createdAt))
        created_at = datetime.fromisoformat(created_at_str)

        # Get the metadata
        metadata: dict[str, object] = {}
        metadata_uri = self.graph.value(vector_uri, self._memory_ns.hasMetadata)
        if metadata_uri:
            for s, p, o in self.graph.triples((metadata_uri, None, None)):
                if p != self._rdf.type:
                    # Extract the predicate name from the URI
                    predicate_name = p.split("#")[-1]
                    metadata[predicate_name] = o.toPython()

        # Create and return the MemoryVector
        return MemoryVector(
            id=vector_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            created_at=created_at,
        )

    def store(self, item: MemoryItem) -> str:
        """
        Store an item in memory and return its ID.

        Args:
            item: The MemoryItem to store

        Returns:
            The ID of the stored item

        Raises:
            MemoryStoreError: If the item cannot be stored
        """
        try:
            # Generate an ID if not provided
            if not item.id:
                item.id = str(uuid.uuid4())

            # Convert the item to RDF triples and add them to the graph
            self._memory_item_to_triples(item)

            # Save the graph to file
            self._save_graph()

            # Update token count
            token_count = self._count_tokens(str(item))
            self.token_count += token_count

            logger.info(f"Stored item with ID {item.id} in RDFLib graph")
            return item.id

        except Exception as e:
            logger.error(f"Failed to store item in RDFLib graph: {e}")
            raise MemoryStoreError(
                "Failed to store item",
                store_type="rdflib",
                operation="store",
                original_error=e,
            )

    def retrieve(self, item_id: str) -> MemoryItem | None:
        """
        Retrieve an item from memory by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved MemoryItem, or None if not found

        Raises:
            MemoryStoreError: If there is an error retrieving the item
        """
        try:
            # Create a URI for the memory item
            item_uri = self._uri_ref(f"{self._memory_ns}item/{item_id}")

            # Convert the RDF triples to a MemoryItem
            item = self._triples_to_memory_item(item_uri)

            if item:
                # Update token count
                token_count = self._count_tokens(str(item))
                self.token_count += token_count

                logger.info(f"Retrieved item with ID {item_id} from RDFLib graph")
            else:
                logger.warning(f"Item with ID {item_id} not found in RDFLib graph")

            return item

        except Exception as e:
            logger.error(f"Error retrieving item from RDFLib graph: {e}")
            raise MemoryStoreError(
                "Error retrieving item",
                store_type="rdflib",
                operation="retrieve",
                original_error=e,
            )

    def search(self, query: MemorySearchQuery | MemoryMetadata) -> list[MemoryRecord]:
        """
        Search for items in memory matching the query.

        Args:
            query: Dictionary of search criteria

        Returns:
            List of matching memory items

        Raises:
            MemoryStoreError: If the search operation fails
        """
        try:
            logger.info(f"Searching items in RDFLib graph with query: {query}")

            # Build a SPARQL query based on the search criteria
            sparql_query = """
                SELECT ?item
                WHERE {
                    ?item a <https://github.com/ravenoak/devsynth/ontology/memory#MemoryItem> .
            """

            # Add query conditions
            for key, value in query.items():
                if key == "id":
                    sparql_query += f"""
                        ?item <https://github.com/ravenoak/devsynth/ontology/memory#id> "{value}" .
                    """
                elif key == "memory_type" and isinstance(value, MemoryType):
                    sparql_query += f"""
                        ?item <https://github.com/ravenoak/devsynth/ontology/memory#memoryType> "{value.value}" .
                    """
                elif key == "created_before":
                    dt = (
                        value.isoformat() if hasattr(value, "isoformat") else str(value)
                    )
                    sparql_query += f"""
                        ?item <https://github.com/ravenoak/devsynth/ontology/memory#createdAt> ?created .
                        FILTER(?created <= "{dt}"^^xsd:dateTime)
                    """
                elif key == "created_after":
                    dt = (
                        value.isoformat() if hasattr(value, "isoformat") else str(value)
                    )
                    sparql_query += f"""
                        ?item <https://github.com/ravenoak/devsynth/ontology/memory#createdAt> ?created .
                        FILTER(?created >= "{dt}"^^xsd:dateTime)
                    """
                elif key == "content" and isinstance(value, str):
                    sparql_query += f"""
                        ?item <https://github.com/ravenoak/devsynth/ontology/memory#content> ?content .
                        FILTER(CONTAINS(LCASE(?content), LCASE("{value}")))
                    """
                elif key.startswith("metadata."):
                    field = key.split(".", 1)[1]
                    predicate_name = field.replace(" ", "_").lower()
                    sparql_query += f"""
                        ?item <https://github.com/ravenoak/devsynth/ontology/memory#hasMetadata> ?metadata .
                        ?metadata <https://github.com/ravenoak/devsynth/ontology/memory#{predicate_name}> ?value .
                        FILTER(?value = "{value}")
                    """

            sparql_query += "}"

            # Execute the SPARQL query
            results = self.graph.query(sparql_query)

            # Convert the results to MemoryItems
            records: list[MemoryRecord] = []
            for row in results:
                item_uri = row[0]
                item = self._triples_to_memory_item(item_uri)
                if item:
                    records.append(
                        build_memory_record(item, source=self.__class__.__name__)
                    )

            # Update token count
            if records:
                token_count = sum(
                    self._count_tokens(str(record.item)) for record in records
                )
                self.token_count += token_count

            logger.info(f"Found {len(records)} matching items in RDFLib graph")
            return records

        except Exception as e:
            logger.error(f"Error searching items in RDFLib graph: {e}")
            raise MemoryStoreError(
                "Error searching items",
                store_type="rdflib",
                operation="search",
                original_error=e,
            )

    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False if it was not found

        Raises:
            MemoryStoreError: If the delete operation fails
        """
        try:
            # Create a URI for the memory item
            item_uri = self._uri_ref(f"{self._memory_ns}item/{item_id}")

            # Check if the item exists
            if (item_uri, self._rdf.type, self._memory_ns.MemoryItem) not in self.graph:
                logger.warning(f"Item with ID {item_id} not found for deletion")
                return False

            # Get the metadata URI
            metadata_uri = self.graph.value(item_uri, self._memory_ns.hasMetadata)

            # Remove all triples related to the item
            self.graph.remove((item_uri, None, None))

            # Remove all triples related to the metadata
            if metadata_uri:
                self.graph.remove((metadata_uri, None, None))

            # Save the graph to file
            self._save_graph()

            logger.info(f"Deleted item with ID {item_id} from RDFLib graph")
            return True

        except Exception as e:
            logger.error(f"Error deleting item from RDFLib graph: {e}")
            raise MemoryStoreError(
                "Error deleting item",
                store_type="rdflib",
                operation="delete",
                original_error=e,
            )

    def get_token_usage(self) -> int:
        """
        Get the current token usage estimate.

        Returns:
            The estimated token usage
        """
        return self.token_count

    def _build_vector_record(
        self, vector: MemoryVector, *, similarity: float | None = None
    ) -> MemoryRecord:
        """Convert a :class:`MemoryVector` into a normalized memory record."""

        return build_memory_record(
            vector,
            source=self.__class__.__name__,
            similarity=similarity,
            metadata=vector.metadata,
        )

    def store_vector(self, vector: MemoryVector) -> str:
        """
        Store a vector in the vector store and return its ID.

        Args:
            vector: The MemoryVector to store

        Returns:
            The ID of the stored vector

        Raises:
            MemoryStoreError: If the vector cannot be stored
        """
        try:
            # Generate an ID if not provided
            if not vector.id:
                vector.id = str(uuid.uuid4())

            # Convert the vector to RDF triples and add them to the graph
            self._memory_vector_to_triples(vector)

            # Save the graph to file
            self._save_graph()

            logger.info(f"Stored vector with ID {vector.id} in RDFLib graph")
            return vector.id

        except Exception as e:
            logger.error(f"Failed to store vector in RDFLib graph: {e}")
            raise MemoryStoreError(
                "Failed to store vector",
                store_type="rdflib",
                operation="store_vector",
                original_error=e,
            )

    def retrieve_vector(self, vector_id: str) -> MemoryRecord | None:
        """
        Retrieve a vector from the vector store by ID.

        Args:
            vector_id: The ID of the vector to retrieve

        Returns:
            The retrieved :class:`MemoryRecord`, or ``None`` if not found

        Raises:
            MemoryStoreError: If there is an error retrieving the vector
        """
        try:
            # Create a URI for the memory vector
            vector_uri = self._uri_ref(f"{self._memory_ns}vector/{vector_id}")

            # Convert the RDF triples to a MemoryVector
            vector = self._triples_to_memory_vector(vector_uri)

            if vector:
                logger.info(f"Retrieved vector with ID {vector_id} from RDFLib graph")
                return self._build_vector_record(vector)
            else:
                logger.warning(f"Vector with ID {vector_id} not found in RDFLib graph")

            return None

        except Exception as e:
            logger.error(f"Error retrieving vector from RDFLib graph: {e}")
            raise MemoryStoreError(
                "Error retrieving vector",
                store_type="rdflib",
                operation="retrieve_vector",
                original_error=e,
            )

    def similarity_search(
        self, query_embedding: Sequence[float], top_k: int = 5
    ) -> list[MemoryRecord]:
        """
        Search for vectors similar to the query embedding.

        Args:
            query_embedding: The embedding to search for
            top_k: The number of results to return

        Returns:
            A list of :class:`MemoryRecord` entries similar to the query embedding

        Raises:
            MemoryStoreError: If there is an error performing the search
        """
        try:
            # Convert query_embedding to a numpy array
            query_embedding_np = np.array(list(query_embedding), dtype=float)

            # Get all vectors from the graph
            sparql_query = """
                SELECT ?vector
                WHERE {
                    ?vector a <https://github.com/ravenoak/devsynth/ontology/memory#MemoryVector> .
                }
            """
            results = self.graph.query(sparql_query)

            # Convert the results to MemoryVectors and compute distances
            vectors_with_distances: list[tuple[MemoryVector, float]] = []
            for row in results:
                vector_uri = row[0]
                vector = self._triples_to_memory_vector(vector_uri)
                if vector:
                    # Compute cosine similarity
                    vector_embedding_np = np.array(vector.embedding)
                    similarity = np.dot(query_embedding_np, vector_embedding_np) / (
                        np.linalg.norm(query_embedding_np)
                        * np.linalg.norm(vector_embedding_np)
                    )
                    # Convert similarity to distance (1 - similarity)
                    distance = 1 - similarity
                    vectors_with_distances.append((vector, distance))

            # Sort by distance and take top_k
            vectors_with_distances.sort(key=lambda x: x[1])
            records = [
                self._build_vector_record(vector, similarity=1.0 - distance)
                for vector, distance in vectors_with_distances[:top_k]
            ]

            logger.info(f"Found {len(records)} similar vectors in RDFLib graph")
            return records

        except Exception as e:
            logger.error(f"Error performing similarity search in RDFLib graph: {e}")
            raise MemoryStoreError(
                "Error performing similarity search",
                store_type="rdflib",
                operation="similarity_search",
                original_error=e,
            )

    def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector from the vector store.

        Args:
            vector_id: The ID of the vector to delete

        Returns:
            True if the vector was deleted, False if it was not found

        Raises:
            MemoryStoreError: If there is an error deleting the vector
        """
        try:
            # Create a URI for the memory vector
            vector_uri = self._uri_ref(f"{self._memory_ns}vector/{vector_id}")

            # Check if the vector exists
            if (
                vector_uri,
                self._rdf.type,
                self._memory_ns.MemoryVector,
            ) not in self.graph:
                logger.warning(f"Vector with ID {vector_id} not found for deletion")
                return False

            # Get the metadata URI
            metadata_uri = self.graph.value(vector_uri, self._memory_ns.hasMetadata)

            # Remove all triples related to the vector
            self.graph.remove((vector_uri, None, None))

            # Remove all triples related to the metadata
            if metadata_uri:
                self.graph.remove((metadata_uri, None, None))

            # Save the graph to file
            self._save_graph()

            logger.info(f"Deleted vector with ID {vector_id} from RDFLib graph")
            return True

        except Exception as e:
            logger.error(f"Error deleting vector from RDFLib graph: {e}")
            raise MemoryStoreError(
                "Error deleting vector",
                store_type="rdflib",
                operation="delete_vector",
                original_error=e,
            )

    def get_collection_stats(self) -> VectorStoreStats:
        """Return statistics about the vector store collection."""

        try:
            sparql_query = """
                SELECT (COUNT(?vector) as ?count)
                WHERE {
                    ?vector a <https://github.com/ravenoak/devsynth/ontology/memory#MemoryVector> .
                }
            """
            results = self.graph.query(sparql_query)
            num_vectors = int(list(results)[0][0])

            embedding_dimension = 0
            if num_vectors > 0:
                sparql_query = """
                    SELECT ?embedding
                    WHERE {
                        ?vector a <https://github.com/ravenoak/devsynth/ontology/memory#MemoryVector> .
                        ?vector <https://github.com/ravenoak/devsynth/ontology/memory#embedding> ?embedding .
                    }
                    LIMIT 1
                """
                results = self.graph.query(sparql_query)
                embedding_json = str(list(results)[0][0])
                embedding = json.loads(embedding_json)
                embedding_dimension = len(embedding)

            stats: VectorStoreStats = {
                "collection_name": os.path.basename(self.graph_file),
                "vector_count": num_vectors,
                "embedding_dimensions": embedding_dimension,
                "persist_directory": self.base_path,
                "metadata": {
                    "graph_file": self.graph_file,
                    "triple_count": len(self.graph),
                },
            }

            logger.info("Retrieved collection statistics: %s", stats)
            return stats

        except Exception as exc:
            logger.error(
                "Error getting collection statistics from RDFLib graph: %s", exc
            )
            raise MemoryStoreError(
                "Error getting collection statistics",
                store_type="rdflib",
                operation="get_collection_stats",
                original_error=exc,
            )

    def get_all_vectors(self) -> list[MemoryVector]:
        """Return all vectors stored in the graph."""
        vectors: list[MemoryVector] = []
        try:
            sparql_query = """
                SELECT ?vector
                WHERE {
                    ?vector a <https://github.com/ravenoak/devsynth/ontology/memory#MemoryVector> .
                }
            """
            results = self.graph.query(sparql_query)
            for row in results:
                vector_uri = row[0]
                vector = self._triples_to_memory_vector(vector_uri)
                if vector:
                    vectors.append(vector)
        except Exception as e:  # pragma: no cover - safe fallback
            logger.error(f"Failed to retrieve vectors: {e}")
        return vectors

    supports_transactions: bool = True
