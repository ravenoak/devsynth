"""JSON file-based implementation of MemoryStore."""

from __future__ import annotations

import errno
import json
import os
import shutil
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import BinaryIO, Literal, TextIO, cast

from devsynth.exceptions import (
    DevSynthError,
    FileNotFoundError,
    FileOperationError,
    FilePermissionError,
    FileSystemError,
    MemoryCorruptionError,
    MemoryError,
    MemoryItemNotFoundError,
    MemoryStoreError,
)
from devsynth.fallback import retry_with_exponential_backoff, with_fallback
from devsynth.logging_setup import DevSynthLogger
from devsynth.security.audit import audit_event
from devsynth.security.encryption import decrypt_bytes, encrypt_bytes

from ...domain.interfaces.memory import MemoryStore, SupportsTransactions
from ...domain.models.memory import MemoryItem, MemoryType
from .dto import (
    MemoryMetadata,
    MemoryRecord,
    MemorySearchQuery,
    build_memory_record,
)

# Create a logger for this module
logger = DevSynthLogger(__name__)

STORE_LABEL = "JSONFileStore"


@dataclass(slots=True)
class _TransactionChange:
    operation: Literal["store", "delete"]
    record: MemoryRecord

    @property
    def item_id(self) -> str:
        return self.record.id


@dataclass(slots=True)
class _TransactionState:
    snapshot: dict[str, MemoryRecord]
    changes: list[_TransactionChange] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)


class JSONFileStore(MemoryStore, SupportsTransactions):
    """JSON file-based implementation of MemoryStore."""

    def __init__(
        self,
        file_path: str,
        version_control: bool = True,
        *,
        encryption_enabled: bool = False,
        encryption_key: str | None = None,
    ):
        """
        Initialize a JSONFileStore.

        Args:
            file_path: Base path for storing JSON files
            version_control: Whether to create backups when updating files
        """
        self.base_path = file_path
        self.version_control = version_control
        self.encryption_enabled = encryption_enabled
        self.encryption_key = encryption_key
        self.items_file = os.path.join(self.base_path, "memory_items.json")
        self.no_file_logging = os.environ.get(
            "DEVSYNTH_NO_FILE_LOGGING", "0"
        ).lower() in ("1", "true", "yes")
        self.items: dict[str, MemoryItem] = self._load_items()
        self.token_count = 0

        # Transaction support
        self.active_transactions: dict[str, _TransactionState] = {}

    supports_transactions: bool = True

    def _encrypt(self, data: bytes) -> bytes:
        if not self.encryption_enabled:
            return data
        return encrypt_bytes(data, key=self.encryption_key)

    def _decrypt(self, data: bytes) -> bytes:
        if not self.encryption_enabled:
            return data
        return decrypt_bytes(data, key=self.encryption_key)

    def _ensure_directory_exists(self) -> None:
        """
        Ensure the directory for storing files exists.

        This method respects test isolation by checking for the DEVSYNTH_NO_FILE_LOGGING
        environment variable. In test environments with file operations disabled,
        it will avoid creating directories.
        """
        # Only create directories if not in a test environment with file operations disabled
        if not self.no_file_logging:
            os.makedirs(self.base_path, exist_ok=True)

    @contextmanager
    def _safe_open_file(
        self, path: str, mode: str = "r", encoding: str = "utf-8"
    ) -> Iterator[TextIO | BinaryIO]:
        """
        Safely open a file with proper error handling.

        Args:
            path: Path to the file
            mode: File mode ('r', 'w', etc.)
            encoding: File encoding

        Yields:
            The opened file object

        Raises:
            FileNotFoundError: If the file is not found
            FilePermissionError: If permission is denied
            FileOperationError: For other file operation errors
        """
        try:
            # Check if file exists for read operations
            if "r" in mode and not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}", file_path=path)

            # Check permissions
            if "r" in mode and os.path.exists(path) and not os.access(path, os.R_OK):
                raise FilePermissionError(
                    f"Permission denied: Cannot read {path}",
                    file_path=path,
                    operation="read",
                )
            if "w" in mode and os.path.exists(path) and not os.access(path, os.W_OK):
                raise FilePermissionError(
                    f"Permission denied: Cannot write to {path}",
                    file_path=path,
                    operation="write",
                )

            # Open the file
            if "b" in mode:
                file = cast(BinaryIO, open(path, mode))
            else:
                file = cast(TextIO, open(path, mode, encoding=encoding))
            try:
                yield file
            finally:
                file.close()
        except OSError as e:
            # Convert OS errors to our custom exceptions
            if e.errno == errno.ENOENT:
                raise FileNotFoundError(
                    f"File not found: {path}", file_path=path
                ) from e
            elif e.errno in (errno.EACCES, errno.EPERM):
                raise FilePermissionError(
                    f"Permission denied: {path}", file_path=path, operation=mode
                ) from e
            else:
                raise FileOperationError(
                    f"File operation failed: {str(e)}", file_path=path, operation=mode
                ) from e

    @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(OSError,))
    def _load_items(self) -> dict[str, MemoryItem]:
        """
        Load items from the JSON file.

        This method respects test isolation by checking for the DEVSYNTH_NO_FILE_LOGGING
        environment variable. In test environments with file operations disabled,
        it will avoid accessing the file system.

        Returns:
            Dictionary of memory items

        Raises:
            MemoryCorruptionError: If the memory data is corrupted
        """
        # In test environments with file operations disabled, return an empty dictionary
        if self.no_file_logging:
            logger.info(
                f"In test environment, using in-memory store", file_path=self.items_file
            )
            empty: dict[str, MemoryItem] = {}
            return empty

        if not os.path.exists(self.items_file):
            logger.info(
                f"Memory store file not found, creating new store",
                file_path=self.items_file,
            )
            empty: dict[str, MemoryItem] = {}
            return empty

        try:
            mode = "rb" if self.encryption_enabled else "r"
            with self._safe_open_file(self.items_file, mode) as f:
                raw = f.read()
                if isinstance(raw, bytes):
                    raw = self._decrypt(raw).decode("utf-8")
                data = json.loads(raw)

            items: dict[str, MemoryItem] = {}
            for item_data in data.get("items", []):
                try:
                    memory_type = MemoryType(item_data.get("memory_type"))
                    created_at = datetime.fromisoformat(item_data.get("created_at"))

                    item = MemoryItem(
                        id=item_data.get("id"),
                        content=item_data.get("content"),
                        memory_type=memory_type,
                        metadata=item_data.get("metadata", {}),
                        created_at=created_at,
                    )
                    items[item.id] = item
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(
                        f"Skipping corrupted memory item: {str(e)}",
                        error=e,
                        item_data=item_data,
                    )

            logger.info(f"Loaded {len(items)} memory items", file_path=self.items_file)
            return items
        except json.JSONDecodeError as e:
            logger.error(
                f"Memory store file is corrupted: {str(e)}",
                error=e,
                file_path=self.items_file,
            )
            raise MemoryCorruptionError(
                f"Memory store file is corrupted: {str(e)}",
                store_type="json_file",
                item_id=self.items_file,
            ) from e
        except (FileNotFoundError, FilePermissionError, FileOperationError) as e:
            logger.error(
                f"Error accessing memory store file: {str(e)}",
                error=e,
                file_path=self.items_file,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error loading memory items: {str(e)}",
                error=e,
                file_path=self.items_file,
            )
            raise MemoryStoreError(
                f"Failed to load memory items: {str(e)}",
                store_type="json_file",
                operation="load",
                original_error=e,
            ) from e

    @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(OSError,))
    def _save_items(self) -> None:
        """
        Save items to the JSON file.

        This method respects test isolation by checking for the DEVSYNTH_NO_FILE_LOGGING
        environment variable. In test environments with file operations disabled,
        it will avoid accessing the file system.

        Raises:
            FilePermissionError: If permission is denied
            FileOperationError: For other file operation errors
            MemoryStoreError: For other memory store errors
        """
        # In test environments with file operations disabled, do nothing
        if self.no_file_logging:
            logger.info(
                f"In test environment, skipping file save operation",
                file_path=self.items_file,
            )
            return

        try:
            self._ensure_directory_exists()

            # Create backup if version control is enabled
            if self.version_control and os.path.exists(self.items_file):
                try:
                    backup_path = f"{self.items_file}.bak"
                    shutil.copy2(self.items_file, backup_path)
                    logger.debug(
                        f"Created backup of memory store file", backup_path=backup_path
                    )
                except OSError as e:
                    logger.warning(
                        f"Failed to create backup of memory store file: {str(e)}",
                        error=e,
                        file_path=self.items_file,
                        backup_path=f"{self.items_file}.bak",
                    )

            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "items": [],
            }

            for item in self.items.values():
                try:
                    # Convert content to string if it's not serializable
                    content = item.content

                    # Handle MemoryType enums in content
                    if isinstance(content, dict):
                        # Create a new dictionary with serializable values
                        serializable_content = {}
                        for k, v in content.items():
                            # Convert MemoryType to string
                            if hasattr(v, "value") and isinstance(v, MemoryType):
                                serializable_content[k] = v.value
                            else:
                                serializable_content[k] = v
                        content = serializable_content
                    elif not isinstance(
                        content, (str, int, float, bool, list, dict, type(None))
                    ):
                        content = str(content)

                    item_data = {
                        "id": item.id,
                        "content": content,
                        "memory_type": item.memory_type.value,
                        "metadata": item.metadata,
                        "created_at": item.created_at.isoformat(),
                    }
                    data["items"].append(item_data)
                except Exception as e:
                    logger.warning(
                        f"Skipping item {item.id} due to serialization error: {str(e)}",
                        error=e,
                        item_id=item.id,
                    )

            mode = "wb" if self.encryption_enabled else "w"
            with self._safe_open_file(self.items_file, mode) as f:
                raw = json.dumps(data, indent=2).encode("utf-8")
                raw = self._encrypt(raw)
                if "b" in mode:
                    f.write(raw)
                else:
                    f.write(raw.decode("utf-8"))

            logger.debug(
                f"Saved {len(data['items'])} memory items", file_path=self.items_file
            )

        except (FileNotFoundError, FilePermissionError, FileOperationError) as e:
            logger.error(
                f"Error accessing memory store file: {str(e)}",
                error=e,
                file_path=self.items_file,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error saving memory items: {str(e)}",
                error=e,
                file_path=self.items_file,
            )
            raise MemoryStoreError(
                f"Failed to save memory items: {str(e)}",
                store_type="json_file",
                operation="save",
                original_error=e,
            ) from e

    def store(self, item: MemoryItem, transaction_id: str | None = None) -> str:
        """
        Store an item in memory and return its ID.

        Args:
            item: The memory item to store
            transaction_id: Optional transaction ID to use for this operation

        Returns:
            The ID of the stored item

        Raises:
            MemoryStoreError: If the item cannot be stored
            MemoryItemNotFoundError: If the transaction does not exist
        """
        try:
            if not item.id:
                item.id = str(uuid.uuid4())

            logger.debug(
                f"Storing memory item",
                item_id=item.id,
                memory_type=item.memory_type.value,
                transaction_id=transaction_id,
            )

            # Check if this operation is part of a transaction
            if transaction_id:
                # Check if the transaction exists
                if transaction_id not in self.active_transactions:
                    logger.warning(
                        f"Transaction not found", transaction_id=transaction_id
                    )
                    raise MemoryItemNotFoundError(
                        f"Transaction {transaction_id} not found",
                        store_type="json_file",
                        item_id=transaction_id,
                    )

                # Get the transaction
                transaction = self.active_transactions[transaction_id]

                # Add the change to the transaction
                transaction.changes.append(
                    _TransactionChange(
                        operation="store",
                        record=build_memory_record(deepcopy(item), source=STORE_LABEL),
                    )
                )

                # Apply the change
                self.items[item.id] = item

                # Don't save to disk yet - will be saved on commit
                audit_event(
                    "store_memory",
                    store=STORE_LABEL,
                    item_id=item.id,
                    transaction_id=transaction_id,
                )
            else:
                # Not part of a transaction, apply immediately
                self.items[item.id] = item
                self._save_items()
                audit_event(
                    "store_memory",
                    store=STORE_LABEL,
                    item_id=item.id,
                )

            # Update token count (rough estimate)
            self.token_count += len(str(item)) // 4

            return item.id
        except MemoryItemNotFoundError:
            # Re-raise the exception
            raise
        except Exception as e:
            logger.error(
                f"Failed to store memory item: {str(e)}",
                error=e,
                item_id=item.id if item.id else "unknown",
                transaction_id=transaction_id,
            )
            raise MemoryStoreError(
                f"Failed to store memory item: {str(e)}",
                store_type="json_file",
                operation="store",
                original_error=e,
            ) from e

    def retrieve(self, item_id: str) -> MemoryItem | None:
        """
        Retrieve an item from memory by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved memory item, or None if not found

        Raises:
            MemoryItemNotFoundError: If the item is not found and raise_if_not_found is True
        """
        try:
            item = self.items.get(item_id)

            if item:
                logger.debug(f"Retrieved memory item", item_id=item_id)
                # Update token count (rough estimate)
                self.token_count += len(str(item)) // 4
                audit_event(
                    "retrieve_memory",
                    store=STORE_LABEL,
                    item_id=item_id,
                    found=True,
                )
                return item
            else:
                logger.debug(f"Memory item not found", item_id=item_id)
                audit_event(
                    "retrieve_memory",
                    store=STORE_LABEL,
                    item_id=item_id,
                    found=False,
                )
                return None
        except Exception as e:
            logger.error(
                f"Error retrieving memory item: {str(e)}", error=e, item_id=item_id
            )
            raise MemoryStoreError(
                f"Error retrieving memory item: {str(e)}",
                store_type="json_file",
                operation="retrieve",
                original_error=e,
            ) from e

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
            logger.debug(f"Searching memory items", query=query)
            records: list[MemoryRecord] = []

            for item in self.items.values():
                match = True
                for key, value in query.items():
                    if key == "memory_type":
                        if isinstance(value, str):
                            if item.memory_type.value != value:
                                match = False
                                break
                        elif hasattr(value, "value"):  # Handle MemoryType enum
                            if item.memory_type != value:
                                match = False
                                break
                        else:
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
                    records.append(
                        build_memory_record(item, source=self.__class__.__name__)
                    )

            # Update token count (rough estimate)
            if records:
                self.token_count += (
                    sum(len(str(record.item)) for record in records) // 4
                )

            logger.debug(f"Found {len(records)} matching memory items", query=query)
            return records
        except Exception as e:
            logger.error(
                f"Error searching memory items: {str(e)}", error=e, query=query
            )
            raise MemoryStoreError(
                f"Error searching memory items: {str(e)}",
                store_type="json_file",
                operation="search",
                original_error=e,
            ) from e

    def delete(self, item_id: str, transaction_id: str | None = None) -> bool:
        """
        Delete an item from memory.

        Args:
            item_id: The ID of the item to delete
            transaction_id: Optional transaction ID to use for this operation

        Returns:
            True if the item was deleted, False if it was not found

        Raises:
            MemoryStoreError: If the delete operation fails
            MemoryItemNotFoundError: If the transaction does not exist
        """
        try:
            # Check if the item exists
            if item_id not in self.items:
                logger.debug(
                    f"Memory item not found for deletion",
                    item_id=item_id,
                    transaction_id=transaction_id,
                )
                audit_event(
                    "delete_memory",
                    store=STORE_LABEL,
                    item_id=item_id,
                    deleted=False,
                    transaction_id=transaction_id,
                )
                return False

            logger.debug(
                f"Deleting memory item", item_id=item_id, transaction_id=transaction_id
            )

            # Check if this operation is part of a transaction
            if transaction_id:
                # Check if the transaction exists
                if transaction_id not in self.active_transactions:
                    logger.warning(
                        f"Transaction not found", transaction_id=transaction_id
                    )
                    raise MemoryItemNotFoundError(
                        f"Transaction {transaction_id} not found",
                        store_type="json_file",
                        item_id=transaction_id,
                    )

                # Get the transaction
                transaction = self.active_transactions[transaction_id]

                # Add the change to the transaction
                transaction.changes.append(
                    _TransactionChange(
                        operation="delete",
                        record=build_memory_record(
                            deepcopy(self.items[item_id]), source=STORE_LABEL
                        ),
                    )
                )

                # Apply the change
                del self.items[item_id]

                # Don't save to disk yet - will be saved on commit
                audit_event(
                    "delete_memory",
                    store=STORE_LABEL,
                    item_id=item_id,
                    deleted=True,
                    transaction_id=transaction_id,
                )
            else:
                # Not part of a transaction, apply immediately
                del self.items[item_id]
                self._save_items()
                audit_event(
                    "delete_memory",
                    store=STORE_LABEL,
                    item_id=item_id,
                    deleted=True,
                )

            return True
        except MemoryItemNotFoundError:
            # Re-raise the exception
            raise
        except Exception as e:
            logger.error(
                f"Error deleting memory item: {str(e)}",
                error=e,
                item_id=item_id,
                transaction_id=transaction_id,
            )
            raise MemoryStoreError(
                f"Error deleting memory item: {str(e)}",
                store_type="json_file",
                operation="delete",
                original_error=e,
            ) from e

    def get_token_usage(self) -> int:
        """
        Get the current token usage estimate.

        Returns:
            The estimated token usage
        """
        return self.token_count

    def begin_transaction(self) -> str:
        """
        Begin a new transaction and return a transaction ID.

        Transactions provide atomicity for a series of operations.
        All operations within a transaction either succeed or fail together.

        Returns:
            The ID of the new transaction

        Raises:
            MemoryStoreError: If the transaction cannot be started
        """
        try:
            # Generate a unique transaction ID
            transaction_id = str(uuid.uuid4())

            # Create a snapshot of the current state
            snapshot = {
                item_id: build_memory_record(deepcopy(item), source=STORE_LABEL)
                for item_id, item in self.items.items()
            }

            # Initialize the transaction
            self.active_transactions[transaction_id] = _TransactionState(
                snapshot=snapshot
            )

            logger.debug(f"Started transaction", transaction_id=transaction_id)
            audit_event(
                "begin_transaction", store=STORE_LABEL, transaction_id=transaction_id
            )

            return transaction_id
        except Exception as e:
            logger.error(f"Failed to start transaction: {str(e)}", error=e)
            raise MemoryStoreError(
                f"Failed to start transaction: {str(e)}",
                store_type="json_file",
                operation="begin_transaction",
                original_error=e,
            ) from e

    def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction, making all its operations permanent.

        Args:
            transaction_id: The ID of the transaction to commit

        Returns:
            True if the transaction was committed successfully, False otherwise

        Raises:
            MemoryStoreError: If the transaction cannot be committed
            MemoryItemNotFoundError: If the transaction does not exist
        """
        try:
            # Check if the transaction exists
            if transaction_id not in self.active_transactions:
                logger.warning(f"Transaction not found", transaction_id=transaction_id)
                raise MemoryItemNotFoundError(
                    f"Transaction {transaction_id} not found",
                    store_type="json_file",
                    item_id=transaction_id,
                )

            # Get the transaction
            # Save the changes to disk
            self._save_items()

            # Remove the transaction
            del self.active_transactions[transaction_id]

            logger.debug(f"Committed transaction", transaction_id=transaction_id)
            audit_event(
                "commit_transaction", store=STORE_LABEL, transaction_id=transaction_id
            )

            return True
        except MemoryItemNotFoundError:
            # Re-raise the exception
            raise
        except Exception as e:
            logger.error(
                f"Failed to commit transaction: {str(e)}",
                error=e,
                transaction_id=transaction_id,
            )
            raise MemoryStoreError(
                f"Failed to commit transaction: {str(e)}",
                store_type="json_file",
                operation="commit_transaction",
                original_error=e,
            ) from e

    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction, undoing all its operations.

        Args:
            transaction_id: The ID of the transaction to rollback

        Returns:
            True if the transaction was rolled back successfully, False otherwise

        Raises:
            MemoryStoreError: If the transaction cannot be rolled back
            MemoryItemNotFoundError: If the transaction does not exist
        """
        try:
            # Check if the transaction exists
            if transaction_id not in self.active_transactions:
                logger.warning(f"Transaction not found", transaction_id=transaction_id)
                raise MemoryItemNotFoundError(
                    f"Transaction {transaction_id} not found",
                    store_type="json_file",
                    item_id=transaction_id,
                )

            # Get the transaction
            transaction = self.active_transactions[transaction_id]

            # Restore the snapshot
            self.items = {
                item_id: deepcopy(record.item)
                for item_id, record in transaction.snapshot.items()
            }

            # Remove the transaction
            del self.active_transactions[transaction_id]

            logger.debug(f"Rolled back transaction", transaction_id=transaction_id)
            audit_event(
                "rollback_transaction",
                store=STORE_LABEL,
                transaction_id=transaction_id,
            )

            return True
        except MemoryItemNotFoundError:
            # Re-raise the exception
            raise
        except Exception as e:
            logger.error(
                f"Failed to rollback transaction: {str(e)}",
                error=e,
                transaction_id=transaction_id,
            )
            raise MemoryStoreError(
                f"Failed to rollback transaction: {str(e)}",
                store_type="json_file",
                operation="rollback_transaction",
                original_error=e,
            ) from e

    def is_transaction_active(self, transaction_id: str) -> bool:
        """
        Check if a transaction is active.

        Args:
            transaction_id: The ID of the transaction to check

        Returns:
            True if the transaction is active, False otherwise
        """
        return transaction_id in self.active_transactions
