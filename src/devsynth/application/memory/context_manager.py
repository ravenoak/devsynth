import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.memory import ContextManager, MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class InMemoryStore(MemoryStore):
    """In-memory implementation of MemoryStore."""

    def __init__(self):
        self.items = {}
        # Simple transaction support: map tx_id -> snapshot of items
        # This lightweight approach avoids heavy copy-on-write mechanisms
        # while satisfying the MemoryStore protocol required by tests.
        self._transactions: Dict[str, Dict[str, MemoryItem]] = {}

    def store(self, item: MemoryItem) -> str:
        """Store an item in memory and return its ID."""
        if not item.id:
            item.id = str(uuid.uuid4())
        self.items[item.id] = item
        return item.id

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from memory by ID."""
        return self.items.get(item_id)

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """Search for items in memory matching the query."""
        result = []
        for item in self.items.values():
            match = True
            for key, value in query.items():
                if key == "memory_type" and isinstance(value, str):
                    if item.memory_type.value != value:
                        match = False
                        break
                elif key == "content" and isinstance(value, str):
                    if value.lower() not in str(item.content).lower():
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
                result.append(item)
        return result

    def delete(self, item_id: str) -> bool:
        """Delete an item from memory."""
        if item_id in self.items:
            del self.items[item_id]
            return True
        return False

    # ------------------------------------------------------------------
    # Transaction management
    # ------------------------------------------------------------------
    def begin_transaction(self) -> str:
        """Begin a new transaction and return its ID."""
        tx_id = str(uuid.uuid4())
        # Store a shallow copy of current items as the transaction snapshot
        self._transactions[tx_id] = self.items.copy()
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction, discarding its snapshot."""
        return self._transactions.pop(transaction_id, None) is not None

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction, restoring its snapshot."""
        snapshot = self._transactions.pop(transaction_id, None)
        if snapshot is None:
            return False
        self.items = snapshot
        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return True if the transaction is still active."""
        return transaction_id in self._transactions

    def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get an item from memory by ID.

        This is an alias for retrieve() to maintain compatibility with other memory stores.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The memory item, or None if not found
        """
        return self.retrieve(item_id)

    def update_item(self, item: MemoryItem) -> bool:
        """
        Update an existing item in memory.

        Args:
            item: The item to update

        Returns:
            True if the item was updated, False if the item was not found
        """
        if not item.id or item.id not in self.items:
            return False
        self.items[item.id] = item
        return True


class SimpleContextManager(ContextManager):
    """Simple implementation of ContextManager."""

    def __init__(self):
        self.context = {}

    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        self.context[key] = value

    def get_from_context(self, key: str) -> Optional[Any]:
        """Get a value from the current context."""
        return self.context.get(key)

    def get_full_context(self) -> Dict[str, Any]:
        """Get the full current context."""
        return self.context.copy()

    def clear_context(self) -> None:
        """Clear the current context."""
        self.context.clear()
