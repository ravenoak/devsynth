"""
TinyDB Memory Adapter Module

This module provides a memory adapter that handles structured data queries
using TinyDB.
"""
from typing import Dict, List, Any, Optional
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from ....domain.models.memory import MemoryItem, MemoryType
from ....domain.interfaces.memory import MemoryStore
from ....logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

class TinyDBMemoryAdapter(MemoryStore):
    """
    TinyDB Memory Adapter handles structured data queries using TinyDB.

    It implements the MemoryStore interface and provides additional methods
    for structured data queries.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize the TinyDB Memory Adapter.

        Args:
            db_path: Path to the TinyDB database file. If None, an in-memory database is used.
        """
        # Use in-memory storage if no path is provided
        if db_path is None:
            self.db = TinyDB(storage=MemoryStorage)
        else:
            self.db = TinyDB(db_path)

        # Create a table for memory items
        self.items_table = self.db.table('memory_items')

        logger.info("TinyDB Memory Adapter initialized")

    def _memory_item_to_dict(self, item: MemoryItem) -> Dict[str, Any]:
        """
        Convert a MemoryItem to a dictionary for storage in TinyDB.

        Args:
            item: The memory item to convert

        Returns:
            A dictionary representation of the memory item
        """
        # Handle both enum and string types for memory_type
        memory_type_value = item.memory_type
        if hasattr(item.memory_type, 'value'):
            memory_type_value = item.memory_type.value

        return {
            'id': item.id,
            'content': item.content,
            'memory_type': memory_type_value,
            'metadata': item.metadata,
            'created_at': item.created_at.isoformat() if item.created_at else None
        }

    def _dict_to_memory_item(self, item_dict: Dict[str, Any]) -> MemoryItem:
        """
        Convert a dictionary from TinyDB to a MemoryItem.

        Args:
            item_dict: The dictionary to convert

        Returns:
            A MemoryItem
        """
        from datetime import datetime

        return MemoryItem(
            id=item_dict['id'],
            content=item_dict['content'],
            memory_type=MemoryType(item_dict['memory_type']),
            metadata=item_dict['metadata'],
            created_at=datetime.fromisoformat(item_dict['created_at']) if item_dict['created_at'] else None
        )

    def store(self, item: MemoryItem) -> str:
        """
        Store a memory item in TinyDB.

        Args:
            item: The memory item to store

        Returns:
            The ID of the stored memory item
        """
        # Generate an ID if not provided
        if not item.id:
            item.id = f"tinydb_{len(self.items_table) + 1}"

        # Convert to dictionary
        item_dict = self._memory_item_to_dict(item)

        # Check if the item already exists
        existing = self.items_table.get(Query().id == item.id)
        if existing:
            # Update the existing item
            self.items_table.update(item_dict, Query().id == item.id)
        else:
            # Insert a new item
            self.items_table.insert(item_dict)

        logger.info(f"Stored memory item with ID {item.id} in TinyDB Memory Adapter")
        return item.id

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from TinyDB.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        item_dict = self.items_table.get(Query().id == item_id)
        if item_dict:
            return self._dict_to_memory_item(item_dict)
        return None

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Search for memory items in TinyDB matching the query.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        # Build TinyDB query
        tinydb_query = Query()
        query_conditions = None

        for key, value in query.items():
            if key == "type":
                # Handle memory_type specially
                condition = (tinydb_query.memory_type == value.value)
            elif key.startswith("metadata."):
                # Handle nested metadata fields
                metadata_key = key.split(".", 1)[1]
                condition = (tinydb_query.metadata[metadata_key] == value)
            elif key in ["id", "content", "created_at"]:
                # Handle direct fields
                condition = (getattr(tinydb_query, key) == value)
            else:
                # Assume it's a metadata field
                condition = (tinydb_query.metadata[key] == value)

            # Combine conditions with AND
            if query_conditions is None:
                query_conditions = condition
            else:
                query_conditions &= condition

        # If no conditions, return all items
        if query_conditions is None:
            results = self.items_table.all()
        else:
            results = self.items_table.search(query_conditions)

        # Convert to MemoryItem objects
        return [self._dict_to_memory_item(item_dict) for item_dict in results]

    def delete(self, item_id: str) -> bool:
        """
        Delete a memory item from TinyDB.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the item was deleted, False otherwise
        """
        removed = self.items_table.remove(Query().id == item_id)
        if removed:
            logger.info(f"Deleted memory item with ID {item_id} from TinyDB Memory Adapter")
            return True
        return False

    def query_structured_data(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Query structured data in TinyDB.

        This method provides a more flexible way to query TinyDB than the standard search method.
        It supports complex queries with nested fields and operators.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        # For now, this is just a wrapper around search
        # In a real implementation, this could support more complex queries
        return self.search(query)

    def close(self):
        """Close the TinyDB database."""
        self.db.close()
