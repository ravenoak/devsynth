"""
RDFLib implementation of MemoryStore and VectorStore.

This implementation uses RDFLib to store and retrieve memory items and vectors
as RDF triples in a knowledge graph. It also supports SPARQL queries for
advanced search capabilities.
"""

import os
import json
import uuid
import tiktoken
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
try:  # pragma: no cover - optional dependency
    import rdflib
    from rdflib import Graph, Literal, URIRef, Namespace, RDF, RDFS, XSD
    from rdflib.namespace import FOAF, DC
    try:
        Namespace("test")
    except Exception:
        raise ImportError("Invalid rdflib stub")
except Exception:  # pragma: no cover - graceful fallback for tests
    rdflib = None
    Graph = Literal = URIRef = object  # type: ignore
    RDF = RDFS = XSD = object  # type: ignore
    FOAF = DC = object  # type: ignore
    def Namespace(uri: str):  # type: ignore
        return uri

from ...domain.interfaces.memory import MemoryStore, VectorStore
from ...domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import (
    DevSynthError, 
    MemoryError, 
    MemoryStoreError, 
    MemoryItemNotFoundError
)

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Define namespaces for the RDF graph
DEVSYNTH = Namespace("http://devsynth.org/ontology#")
MEMORY = Namespace("http://devsynth.org/ontology/memory#")

class RDFLibStore(MemoryStore, VectorStore):
    """
    RDFLib implementation of the MemoryStore and VectorStore interfaces.

    This class uses RDFLib to store and retrieve memory items and vectors
    as RDF triples in a knowledge graph. It also supports SPARQL queries for
    advanced search capabilities.
    """

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

        # Initialize the RDF graph
        self.graph = Graph()
        
        # Bind namespaces to the graph for more readable serialization
        self.graph.bind("devsynth", DEVSYNTH)
        self.graph.bind("memory", MEMORY)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("dc", DC)

        # Initialize the tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
        except Exception as e:
            logger.warning(f"Failed to initialize tokenizer: {e}. Token counting will be approximate.")
            self.tokenizer = None

        # Load the graph from file if it exists
        self._load_graph()

    def _load_graph(self):
        """Load the RDF graph from file if it exists."""
        try:
            if os.path.exists(self.graph_file):
                self.graph.parse(self.graph_file, format="turtle")
                logger.info(f"Loaded RDF graph from {self.graph_file}")
            else:
                logger.info(f"No existing RDF graph found at {self.graph_file}")
        except Exception as e:
            logger.error(f"Failed to load RDF graph: {e}")
            raise MemoryStoreError("Failed to load RDF graph", 
                                  store_type="rdflib", 
                                  operation="load_graph", 
                                  original_error=e)

    def _save_graph(self):
        """Save the RDF graph to file."""
        try:
            self.graph.serialize(destination=self.graph_file, format="turtle")
            logger.info(f"Saved RDF graph to {self.graph_file}")
        except Exception as e:
            logger.error(f"Failed to save RDF graph: {e}")
            raise MemoryStoreError("Failed to save RDF graph", 
                                  store_type="rdflib", 
                                  operation="save_graph", 
                                  original_error=e)

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

    def _memory_item_to_triples(self, item: MemoryItem):
        """
        Convert a MemoryItem to RDF triples and add them to the graph.

        Args:
            item: The MemoryItem to convert
        """
        # Create a URI for the memory item
        item_uri = URIRef(f"{MEMORY}item/{item.id}")
        
        # Add basic triples for the memory item
        self.graph.add((item_uri, RDF.type, MEMORY.MemoryItem))
        self.graph.add((item_uri, MEMORY.id, Literal(item.id)))
        self.graph.add((item_uri, MEMORY.content, Literal(str(item.content))))
        self.graph.add((item_uri, MEMORY.memoryType, Literal(item.memory_type.value)))
        self.graph.add((item_uri, MEMORY.createdAt, Literal(item.created_at.isoformat(), datatype=XSD.dateTime)))
        
        # Add metadata as triples
        if item.metadata:
            metadata_uri = URIRef(f"{MEMORY}metadata/{item.id}")
            self.graph.add((item_uri, MEMORY.hasMetadata, metadata_uri))
            self.graph.add((metadata_uri, RDF.type, MEMORY.Metadata))
            
            for key, value in item.metadata.items():
                # Convert the key to a valid predicate name (replace spaces, etc.)
                predicate_name = key.replace(" ", "_").lower()
                predicate = MEMORY[predicate_name]
                
                # Add the metadata triple
                if isinstance(value, (int, float, bool)):
                    self.graph.add((metadata_uri, predicate, Literal(value)))
                else:
                    self.graph.add((metadata_uri, predicate, Literal(str(value))))

    def _triples_to_memory_item(self, item_uri: URIRef) -> Optional[MemoryItem]:
        """
        Convert RDF triples to a MemoryItem.

        Args:
            item_uri: The URI of the memory item

        Returns:
            The converted MemoryItem, or None if not found
        """
        # Check if the item exists
        if (item_uri, RDF.type, MEMORY.MemoryItem) not in self.graph:
            return None
        
        # Get the basic properties
        item_id = str(self.graph.value(item_uri, MEMORY.id))
        content = str(self.graph.value(item_uri, MEMORY.content))
        memory_type_value = str(self.graph.value(item_uri, MEMORY.memoryType))
        memory_type = MemoryType(memory_type_value)
        created_at_str = str(self.graph.value(item_uri, MEMORY.createdAt))
        created_at = datetime.fromisoformat(created_at_str)
        
        # Get the metadata
        metadata = {}
        metadata_uri = self.graph.value(item_uri, MEMORY.hasMetadata)
        if metadata_uri:
            for s, p, o in self.graph.triples((metadata_uri, None, None)):
                if p != RDF.type:
                    # Extract the predicate name from the URI
                    predicate_name = p.split("#")[-1]
                    metadata[predicate_name] = o.toPython()
        
        # Create and return the MemoryItem
        return MemoryItem(
            id=item_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            created_at=created_at
        )

    def _memory_vector_to_triples(self, vector: MemoryVector):
        """
        Convert a MemoryVector to RDF triples and add them to the graph.

        Args:
            vector: The MemoryVector to convert
        """
        # Create a URI for the memory vector
        vector_uri = URIRef(f"{MEMORY}vector/{vector.id}")
        
        # Add basic triples for the memory vector
        self.graph.add((vector_uri, RDF.type, MEMORY.MemoryVector))
        self.graph.add((vector_uri, MEMORY.id, Literal(vector.id)))
        self.graph.add((vector_uri, MEMORY.content, Literal(str(vector.content))))
        self.graph.add((vector_uri, MEMORY.createdAt, Literal(vector.created_at.isoformat(), datatype=XSD.dateTime)))
        
        # Add embedding as a JSON string
        embedding_json = json.dumps(vector.embedding)
        self.graph.add((vector_uri, MEMORY.embedding, Literal(embedding_json)))
        
        # Add metadata as triples
        if vector.metadata:
            metadata_uri = URIRef(f"{MEMORY}metadata/{vector.id}")
            self.graph.add((vector_uri, MEMORY.hasMetadata, metadata_uri))
            self.graph.add((metadata_uri, RDF.type, MEMORY.Metadata))
            
            for key, value in vector.metadata.items():
                # Convert the key to a valid predicate name (replace spaces, etc.)
                predicate_name = key.replace(" ", "_").lower()
                predicate = MEMORY[predicate_name]
                
                # Add the metadata triple
                if isinstance(value, (int, float, bool)):
                    self.graph.add((metadata_uri, predicate, Literal(value)))
                else:
                    self.graph.add((metadata_uri, predicate, Literal(str(value))))

    def _triples_to_memory_vector(self, vector_uri: URIRef) -> Optional[MemoryVector]:
        """
        Convert RDF triples to a MemoryVector.

        Args:
            vector_uri: The URI of the memory vector

        Returns:
            The converted MemoryVector, or None if not found
        """
        # Check if the vector exists
        if (vector_uri, RDF.type, MEMORY.MemoryVector) not in self.graph:
            return None
        
        # Get the basic properties
        vector_id = str(self.graph.value(vector_uri, MEMORY.id))
        content = str(self.graph.value(vector_uri, MEMORY.content))
        embedding_json = str(self.graph.value(vector_uri, MEMORY.embedding))
        embedding = json.loads(embedding_json)
        created_at_str = str(self.graph.value(vector_uri, MEMORY.createdAt))
        created_at = datetime.fromisoformat(created_at_str)
        
        # Get the metadata
        metadata = {}
        metadata_uri = self.graph.value(vector_uri, MEMORY.hasMetadata)
        if metadata_uri:
            for s, p, o in self.graph.triples((metadata_uri, None, None)):
                if p != RDF.type:
                    # Extract the predicate name from the URI
                    predicate_name = p.split("#")[-1]
                    metadata[predicate_name] = o.toPython()
        
        # Create and return the MemoryVector
        return MemoryVector(
            id=vector_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            created_at=created_at
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
            raise MemoryStoreError("Failed to store item", 
                                  store_type="rdflib", 
                                  operation="store", 
                                  original_error=e)

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
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
            item_uri = URIRef(f"{MEMORY}item/{item_id}")
            
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
            raise MemoryStoreError("Error retrieving item", 
                                  store_type="rdflib", 
                                  operation="retrieve", 
                                  original_error=e)

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
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
                    ?item a <http://devsynth.org/ontology/memory#MemoryItem> .
            """
            
            # Add query conditions
            for key, value in query.items():
                if key == "memory_type" and isinstance(value, MemoryType):
                    sparql_query += f"""
                        ?item <http://devsynth.org/ontology/memory#memoryType> "{value.value}" .
                    """
                elif key == "content" and isinstance(value, str):
                    sparql_query += f"""
                        ?item <http://devsynth.org/ontology/memory#content> ?content .
                        FILTER(CONTAINS(LCASE(?content), LCASE("{value}")))
                    """
                elif key.startswith("metadata."):
                    field = key.split(".", 1)[1]
                    predicate_name = field.replace(" ", "_").lower()
                    sparql_query += f"""
                        ?item <http://devsynth.org/ontology/memory#hasMetadata> ?metadata .
                        ?metadata <http://devsynth.org/ontology/memory#{predicate_name}> ?value .
                        FILTER(?value = "{value}")
                    """
            
            sparql_query += "}"
            
            # Execute the SPARQL query
            results = self.graph.query(sparql_query)
            
            # Convert the results to MemoryItems
            items = []
            for row in results:
                item_uri = row[0]
                item = self._triples_to_memory_item(item_uri)
                if item:
                    items.append(item)
            
            # Update token count
            if items:
                token_count = sum(self._count_tokens(str(item)) for item in items)
                self.token_count += token_count
            
            logger.info(f"Found {len(items)} matching items in RDFLib graph")
            return items
        
        except Exception as e:
            logger.error(f"Error searching items in RDFLib graph: {e}")
            raise MemoryStoreError("Error searching items", 
                                  store_type="rdflib", 
                                  operation="search", 
                                  original_error=e)

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
            item_uri = URIRef(f"{MEMORY}item/{item_id}")
            
            # Check if the item exists
            if (item_uri, RDF.type, MEMORY.MemoryItem) not in self.graph:
                logger.warning(f"Item with ID {item_id} not found for deletion")
                return False
            
            # Get the metadata URI
            metadata_uri = self.graph.value(item_uri, MEMORY.hasMetadata)
            
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
            raise MemoryStoreError("Error deleting item", 
                                  store_type="rdflib", 
                                  operation="delete", 
                                  original_error=e)

    def get_token_usage(self) -> int:
        """
        Get the current token usage estimate.

        Returns:
            The estimated token usage
        """
        return self.token_count

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
            raise MemoryStoreError("Failed to store vector", 
                                  store_type="rdflib", 
                                  operation="store_vector", 
                                  original_error=e)

    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        """
        Retrieve a vector from the vector store by ID.

        Args:
            vector_id: The ID of the vector to retrieve

        Returns:
            The retrieved MemoryVector, or None if not found

        Raises:
            MemoryStoreError: If there is an error retrieving the vector
        """
        try:
            # Create a URI for the memory vector
            vector_uri = URIRef(f"{MEMORY}vector/{vector_id}")
            
            # Convert the RDF triples to a MemoryVector
            vector = self._triples_to_memory_vector(vector_uri)
            
            if vector:
                logger.info(f"Retrieved vector with ID {vector_id} from RDFLib graph")
            else:
                logger.warning(f"Vector with ID {vector_id} not found in RDFLib graph")
            
            return vector
        
        except Exception as e:
            logger.error(f"Error retrieving vector from RDFLib graph: {e}")
            raise MemoryStoreError("Error retrieving vector", 
                                  store_type="rdflib", 
                                  operation="retrieve_vector", 
                                  original_error=e)

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryVector]:
        """
        Search for vectors similar to the query embedding.

        Args:
            query_embedding: The embedding to search for
            top_k: The number of results to return

        Returns:
            A list of MemoryVectors similar to the query embedding

        Raises:
            MemoryStoreError: If there is an error performing the search
        """
        try:
            # Convert query_embedding to a numpy array
            query_embedding_np = np.array(query_embedding)
            
            # Get all vectors from the graph
            sparql_query = """
                SELECT ?vector
                WHERE {
                    ?vector a <http://devsynth.org/ontology/memory#MemoryVector> .
                }
            """
            results = self.graph.query(sparql_query)
            
            # Convert the results to MemoryVectors and compute distances
            vectors_with_distances = []
            for row in results:
                vector_uri = row[0]
                vector = self._triples_to_memory_vector(vector_uri)
                if vector:
                    # Compute cosine similarity
                    vector_embedding_np = np.array(vector.embedding)
                    similarity = np.dot(query_embedding_np, vector_embedding_np) / (
                        np.linalg.norm(query_embedding_np) * np.linalg.norm(vector_embedding_np)
                    )
                    # Convert similarity to distance (1 - similarity)
                    distance = 1 - similarity
                    vectors_with_distances.append((vector, distance))
            
            # Sort by distance and take top_k
            vectors_with_distances.sort(key=lambda x: x[1])
            vectors = [v for v, _ in vectors_with_distances[:top_k]]
            
            logger.info(f"Found {len(vectors)} similar vectors in RDFLib graph")
            return vectors
        
        except Exception as e:
            logger.error(f"Error performing similarity search in RDFLib graph: {e}")
            raise MemoryStoreError("Error performing similarity search", 
                                  store_type="rdflib", 
                                  operation="similarity_search", 
                                  original_error=e)

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
            vector_uri = URIRef(f"{MEMORY}vector/{vector_id}")
            
            # Check if the vector exists
            if (vector_uri, RDF.type, MEMORY.MemoryVector) not in self.graph:
                logger.warning(f"Vector with ID {vector_id} not found for deletion")
                return False
            
            # Get the metadata URI
            metadata_uri = self.graph.value(vector_uri, MEMORY.hasMetadata)
            
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
            raise MemoryStoreError("Error deleting vector", 
                                  store_type="rdflib", 
                                  operation="delete_vector", 
                                  original_error=e)

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            A dictionary of collection statistics

        Raises:
            MemoryStoreError: If there is an error getting collection statistics
        """
        try:
            # Get the number of vectors
            sparql_query = """
                SELECT (COUNT(?vector) as ?count)
                WHERE {
                    ?vector a <http://devsynth.org/ontology/memory#MemoryVector> .
                }
            """
            results = self.graph.query(sparql_query)
            num_vectors = int(list(results)[0][0])
            
            # Get the embedding dimension (from the first vector if available)
            embedding_dimension = 0
            if num_vectors > 0:
                sparql_query = """
                    SELECT ?embedding
                    WHERE {
                        ?vector a <http://devsynth.org/ontology/memory#MemoryVector> .
                        ?vector <http://devsynth.org/ontology/memory#embedding> ?embedding .
                    }
                    LIMIT 1
                """
                results = self.graph.query(sparql_query)
                embedding_json = str(list(results)[0][0])
                embedding = json.loads(embedding_json)
                embedding_dimension = len(embedding)
            
            # Get the total number of triples in the graph
            num_triples = len(self.graph)
            
            stats = {
                "num_vectors": num_vectors,
                "embedding_dimension": embedding_dimension,
                "num_triples": num_triples,
                "graph_file": self.graph_file
            }
            
            logger.info(f"Retrieved collection statistics: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error getting collection statistics from RDFLib graph: {e}")
            raise MemoryStoreError("Error getting collection statistics", 
                                  store_type="rdflib", 
                                  operation="get_collection_stats", 
                                  original_error=e)