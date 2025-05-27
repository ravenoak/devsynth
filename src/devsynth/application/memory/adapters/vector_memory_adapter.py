"""
Vector Memory Adapter Module

This module provides a memory adapter that handles vector-based operations
for similarity search.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from ....domain.models.memory import MemoryVector
from ....domain.interfaces.memory import VectorStore
from ....logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

class VectorMemoryAdapter(VectorStore):
    """
    Vector Memory Adapter handles vector-based operations for similarity search.
    
    It implements the VectorStore interface and provides methods for storing,
    retrieving, and searching vectors.
    """
    
    def __init__(self):
        """Initialize the Vector Memory Adapter."""
        self.vectors = {}  # Dictionary of memory vectors by ID
        self.embeddings = {}  # Dictionary of embeddings by ID for fast lookup
        logger.info("Vector Memory Adapter initialized")
    
    def store_vector(self, vector: MemoryVector) -> str:
        """
        Store a vector in the vector store.
        
        Args:
            vector: The memory vector to store
            
        Returns:
            The ID of the stored vector
        """
        # Generate an ID if not provided
        if not vector.id:
            vector.id = f"vector_{len(self.vectors) + 1}"
        
        # Store the vector
        self.vectors[vector.id] = vector
        
        # Store the embedding for fast lookup
        self.embeddings[vector.id] = np.array(vector.embedding)
        
        logger.info(f"Stored memory vector with ID {vector.id} in Vector Memory Adapter")
        return vector.id
    
    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        """
        Retrieve a vector from the vector store.
        
        Args:
            vector_id: The ID of the vector to retrieve
            
        Returns:
            The retrieved vector, or None if not found
        """
        return self.vectors.get(vector_id)
    
    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryVector]:
        """
        Search for vectors similar to the query embedding.
        
        Args:
            query_embedding: The query embedding
            top_k: The number of results to return
            
        Returns:
            A list of similar memory vectors
        """
        if not self.vectors:
            return []
        
        # Convert query embedding to numpy array
        query_embedding_np = np.array(query_embedding)
        
        # Calculate cosine similarity for all vectors
        similarities = {}
        for vector_id, embedding in self.embeddings.items():
            # Normalize embeddings
            query_norm = np.linalg.norm(query_embedding_np)
            embedding_norm = np.linalg.norm(embedding)
            
            # Avoid division by zero
            if query_norm == 0 or embedding_norm == 0:
                similarities[vector_id] = 0
            else:
                # Calculate cosine similarity
                similarity = np.dot(query_embedding_np, embedding) / (query_norm * embedding_norm)
                similarities[vector_id] = similarity
        
        # Sort by similarity (descending)
        sorted_ids = sorted(similarities.keys(), key=lambda x: similarities[x], reverse=True)
        
        # Get top-k results
        top_k_ids = sorted_ids[:top_k]
        
        # Return the corresponding vectors
        return [self.vectors[vector_id] for vector_id in top_k_ids]
    
    def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector from the vector store.
        
        Args:
            vector_id: The ID of the vector to delete
            
        Returns:
            True if the vector was deleted, False otherwise
        """
        if vector_id in self.vectors:
            # Remove the vector
            del self.vectors[vector_id]
            
            # Remove the embedding
            if vector_id in self.embeddings:
                del self.embeddings[vector_id]
            
            logger.info(f"Deleted memory vector with ID {vector_id} from Vector Memory Adapter")
            return True
        
        return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.
        
        Returns:
            A dictionary of statistics
        """
        return {
            "vector_count": len(self.vectors),
            "embedding_dimensions": len(next(iter(self.embeddings.values()))) if self.embeddings else 0
        }