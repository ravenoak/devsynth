"""
Graph Memory Adapter Module

This module provides a memory adapter that handles relationships between memory items
using a graph-based approach.
"""
from typing import Dict, List, Any, Optional, Set
from ....domain.models.memory import MemoryItem, MemoryType
from ....domain.interfaces.memory import MemoryStore
from ....logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

class GraphMemoryAdapter(MemoryStore):
    """
    Graph Memory Adapter handles relationships between memory items using a graph-based approach.
    
    It implements the MemoryStore interface and provides additional methods for querying
    relationships between items.
    """
    
    def __init__(self):
        """Initialize the Graph Memory Adapter."""
        self.items = {}  # Dictionary of memory items by ID
        self.relationships = {}  # Dictionary of relationships by item ID
        logger.info("Graph Memory Adapter initialized")
    
    def store(self, item: MemoryItem) -> str:
        """
        Store a memory item and process its relationships.
        
        Args:
            item: The memory item to store
            
        Returns:
            The ID of the stored memory item
        """
        # Generate an ID if not provided
        if not item.id:
            item.id = f"graph_{len(self.items) + 1}"
        
        # Store the item
        self.items[item.id] = item
        
        # Process relationships
        related_to = item.metadata.get("related_to")
        if related_to:
            # Initialize relationships for this item if not exists
            if item.id not in self.relationships:
                self.relationships[item.id] = set()
            
            # Add the relationship
            self.relationships[item.id].add(related_to)
            
            # Add the reverse relationship
            if related_to not in self.relationships:
                self.relationships[related_to] = set()
            self.relationships[related_to].add(item.id)
        
        logger.info(f"Stored memory item with ID {item.id} in Graph Memory Adapter")
        return item.id
    
    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.
        
        Args:
            item_id: The ID of the memory item to retrieve
            
        Returns:
            The retrieved memory item, or None if not found
        """
        return self.items.get(item_id)
    
    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Search for memory items matching the query.
        
        Args:
            query: The query dictionary
            
        Returns:
            A list of matching memory items
        """
        results = []
        
        for item in self.items.values():
            match = True
            
            for key, value in query.items():
                if key == "type":
                    if item.memory_type != value:
                        match = False
                        break
                elif key in item.metadata:
                    if item.metadata[key] != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                results.append(item)
        
        return results
    
    def delete(self, item_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            item_id: The ID of the memory item to delete
            
        Returns:
            True if the item was deleted, False otherwise
        """
        if item_id in self.items:
            # Remove the item
            del self.items[item_id]
            
            # Remove relationships
            if item_id in self.relationships:
                # Get all related items
                related_items = self.relationships[item_id]
                
                # Remove the reverse relationships
                for related_id in related_items:
                    if related_id in self.relationships:
                        self.relationships[related_id].discard(item_id)
                
                # Remove the relationships for this item
                del self.relationships[item_id]
            
            logger.info(f"Deleted memory item with ID {item_id} from Graph Memory Adapter")
            return True
        
        return False
    
    def query_related_items(self, item_id: str) -> List[MemoryItem]:
        """
        Query for items related to a given item ID.
        
        Args:
            item_id: The ID of the item to find related items for
            
        Returns:
            A list of related memory items
        """
        if item_id not in self.relationships:
            return []
        
        related_ids = self.relationships[item_id]
        related_items = []
        
        for related_id in related_ids:
            item = self.retrieve(related_id)
            if item:
                related_items.append(item)
        
        return related_items
    
    def get_all_relationships(self) -> Dict[str, Set[str]]:
        """
        Get all relationships in the graph.
        
        Returns:
            A dictionary of relationships by item ID
        """
        return self.relationships