"""
Vector Memory Adapter Module

This module provides a memory adapter that handles vector-based operations
for similarity search.
"""
import numpy as np
import uuid
from typing import Dict, List, Any, Optional
from copy import deepcopy
from ....domain.models.memory import MemoryVector
from ....domain.interfaces.memory import VectorStore
from ....logging_setup import DevSynthLogger
from ....exceptions import MemoryTransactionError

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
        
    def get_all(self) -> List[MemoryVector]:
        """
        Get all vectors from the vector store.
        
        Returns:
            A list of all memory vectors
        """
        return list(self.vectors.values())
        
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
        logger.debug(f"Beginning transaction {transaction_id} in VectorMemoryAdapter")
        
        # Store the transaction ID
        if not hasattr(self, '_active_transactions'):
            self._active_transactions = {}
            
        # Create a snapshot of the current state
        snapshot = {
            'vectors': deepcopy(self.vectors),
            'embeddings': deepcopy(self.embeddings)
        }
        
        # Store the snapshot with the transaction ID
        self._active_transactions[transaction_id] = {
            'snapshot': snapshot,
            'prepared': False
        }
        
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
        logger.debug(f"Preparing to commit transaction {transaction_id} in VectorMemoryAdapter")
        
        # Check if this is an active transaction
        if not hasattr(self, '_active_transactions') or transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="VectorMemoryAdapter",
                operation="prepare_commit"
            )
            
        # Mark the transaction as prepared
        self._active_transactions[transaction_id]['prepared'] = True
        
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
        logger.debug(f"Committing transaction {transaction_id} in VectorMemoryAdapter")
        
        # Check if this is an active transaction
        if not hasattr(self, '_active_transactions') or transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="VectorMemoryAdapter",
                operation="commit_transaction"
            )
            
        # Remove the transaction from the active transactions
        del self._active_transactions[transaction_id]
        
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
        logger.debug(f"Rolling back transaction {transaction_id} in VectorMemoryAdapter")
        
        # Check if this is an active transaction
        if not hasattr(self, '_active_transactions') or transaction_id not in self._active_transactions:
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="VectorMemoryAdapter",
                operation="rollback_transaction"
            )
            
        # Get the snapshot
        snapshot = self._active_transactions[transaction_id]['snapshot']
        
        # Restore from the snapshot
        self.vectors = snapshot['vectors']
        self.embeddings = snapshot['embeddings']
        
        # Remove the transaction from the active transactions
        del self._active_transactions[transaction_id]
        
        return True
        
    def snapshot(self) -> Dict[str, Any]:
        """
        Create a snapshot of the current state.
        
        Returns:
            A dictionary containing the current state
        """
        return {
            'vectors': deepcopy(self.vectors),
            'embeddings': deepcopy(self.embeddings)
        }
        
    def restore(self, snapshot: Dict[str, Any]) -> bool:
        """
        Restore from a snapshot.
        
        Args:
            snapshot: A dictionary containing the state to restore
            
        Returns:
            True if the restore was successful
        """
        if snapshot is None:
            return False
            
        try:
            self.vectors = snapshot['vectors']
            self.embeddings = snapshot['embeddings']
            return True
        except Exception as e:
            logger.error(f"Failed to restore from snapshot: {e}")
            return False