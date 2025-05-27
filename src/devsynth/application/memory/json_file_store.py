"""
JSON file-based implementation of MemoryStore.
"""

import os
import json
import uuid
import shutil
import errno
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import (
    DevSynthError, 
    MemoryError, 
    MemoryStoreError, 
    MemoryItemNotFoundError, 
    MemoryCorruptionError,
    FileSystemError,
    FileNotFoundError,
    FilePermissionError,
    FileOperationError
)
from devsynth.fallback import retry_with_exponential_backoff, with_fallback

# Create a logger for this module
logger = DevSynthLogger(__name__)

class JSONFileStore(MemoryStore):
    """JSON file-based implementation of MemoryStore."""

    def __init__(self, file_path: str, version_control: bool = True):
        """
        Initialize a JSONFileStore.

        Args:
            file_path: Base path for storing JSON files
            version_control: Whether to create backups when updating files
        """
        self.base_path = file_path
        self.version_control = version_control
        self.items_file = os.path.join(self.base_path, "memory_items.json")
        self.items = self._load_items()
        self.token_count = 0

    def _ensure_directory_exists(self) -> None:
        """Ensure the directory for storing files exists."""
        os.makedirs(self.base_path, exist_ok=True)

    @contextmanager
    def _safe_open_file(self, path: str, mode: str = "r", encoding: str = "utf-8") -> Any:
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
            if 'r' in mode and not os.path.exists(path):
                raise FileNotFoundError(
                    f"File not found: {path}",
                    file_path=path
                )

            # Check permissions
            if 'r' in mode and os.path.exists(path) and not os.access(path, os.R_OK):
                raise FilePermissionError(
                    f"Permission denied: Cannot read {path}",
                    file_path=path,
                    operation="read"
                )
            if 'w' in mode and os.path.exists(path) and not os.access(path, os.W_OK):
                raise FilePermissionError(
                    f"Permission denied: Cannot write to {path}",
                    file_path=path,
                    operation="write"
                )

            # Open the file
            file = open(path, mode, encoding=encoding)
            try:
                yield file
            finally:
                file.close()
        except OSError as e:
            # Convert OS errors to our custom exceptions
            if e.errno == errno.ENOENT:
                raise FileNotFoundError(
                    f"File not found: {path}",
                    file_path=path
                ) from e
            elif e.errno in (errno.EACCES, errno.EPERM):
                raise FilePermissionError(
                    f"Permission denied: {path}",
                    file_path=path,
                    operation=mode
                ) from e
            else:
                raise FileOperationError(
                    f"File operation failed: {str(e)}",
                    file_path=path,
                    operation=mode
                ) from e

    @retry_with_exponential_backoff(
        max_retries=3,
        retryable_exceptions=(OSError,)
    )
    def _load_items(self) -> Dict[str, MemoryItem]:
        """
        Load items from the JSON file.

        Returns:
            Dictionary of memory items

        Raises:
            MemoryCorruptionError: If the memory data is corrupted
        """
        if not os.path.exists(self.items_file):
            logger.info(f"Memory store file not found, creating new store", file_path=self.items_file)
            return {}

        try:
            with self._safe_open_file(self.items_file, 'r') as f:
                data = json.load(f)

            items = {}
            for item_data in data.get('items', []):
                try:
                    memory_type = MemoryType(item_data.get('memory_type'))
                    created_at = datetime.fromisoformat(item_data.get('created_at'))

                    item = MemoryItem(
                        id=item_data.get('id'),
                        content=item_data.get('content'),
                        memory_type=memory_type,
                        metadata=item_data.get('metadata', {}),
                        created_at=created_at
                    )
                    items[item.id] = item
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(
                        f"Skipping corrupted memory item: {str(e)}",
                        error=e,
                        item_data=item_data
                    )

            logger.info(f"Loaded {len(items)} memory items", file_path=self.items_file)
            return items
        except json.JSONDecodeError as e:
            logger.error(
                f"Memory store file is corrupted: {str(e)}",
                error=e,
                file_path=self.items_file
            )
            raise MemoryCorruptionError(
                f"Memory store file is corrupted: {str(e)}",
                store_type="json_file",
                item_id=self.items_file
            ) from e
        except (FileNotFoundError, FilePermissionError, FileOperationError) as e:
            logger.error(
                f"Error accessing memory store file: {str(e)}",
                error=e,
                file_path=self.items_file
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error loading memory items: {str(e)}",
                error=e,
                file_path=self.items_file
            )
            raise MemoryStoreError(
                f"Failed to load memory items: {str(e)}",
                store_type="json_file",
                operation="load",
                original_error=e
            ) from e

    @retry_with_exponential_backoff(
        max_retries=3,
        retryable_exceptions=(OSError,)
    )
    def _save_items(self) -> None:
        """
        Save items to the JSON file.

        Raises:
            FilePermissionError: If permission is denied
            FileOperationError: For other file operation errors
            MemoryStoreError: For other memory store errors
        """
        try:
            self._ensure_directory_exists()

            # Create backup if version control is enabled
            if self.version_control and os.path.exists(self.items_file):
                try:
                    backup_path = f"{self.items_file}.bak"
                    shutil.copy2(self.items_file, backup_path)
                    logger.debug(f"Created backup of memory store file", 
                                backup_path=backup_path)
                except OSError as e:
                    logger.warning(
                        f"Failed to create backup of memory store file: {str(e)}",
                        error=e,
                        file_path=self.items_file,
                        backup_path=f"{self.items_file}.bak"
                    )

            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'items': []
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
                            if hasattr(v, 'value') and isinstance(v, MemoryType):
                                serializable_content[k] = v.value
                            else:
                                serializable_content[k] = v
                        content = serializable_content
                    elif not isinstance(content, (str, int, float, bool, list, dict, type(None))):
                        content = str(content)

                    item_data = {
                        'id': item.id,
                        'content': content,
                        'memory_type': item.memory_type.value,
                        'metadata': item.metadata,
                        'created_at': item.created_at.isoformat()
                    }
                    data['items'].append(item_data)
                except Exception as e:
                    logger.warning(
                        f"Skipping item {item.id} due to serialization error: {str(e)}",
                        error=e,
                        item_id=item.id
                    )

            with self._safe_open_file(self.items_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(data['items'])} memory items", 
                        file_path=self.items_file)

        except (FileNotFoundError, FilePermissionError, FileOperationError) as e:
            logger.error(
                f"Error accessing memory store file: {str(e)}",
                error=e,
                file_path=self.items_file
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error saving memory items: {str(e)}",
                error=e,
                file_path=self.items_file
            )
            raise MemoryStoreError(
                f"Failed to save memory items: {str(e)}",
                store_type="json_file",
                operation="save",
                original_error=e
            ) from e

    def store(self, item: MemoryItem) -> str:
        """
        Store an item in memory and return its ID.

        Args:
            item: The memory item to store

        Returns:
            The ID of the stored item

        Raises:
            MemoryStoreError: If the item cannot be stored
        """
        try:
            if not item.id:
                item.id = str(uuid.uuid4())

            logger.debug(f"Storing memory item", item_id=item.id, memory_type=item.memory_type.value)
            self.items[item.id] = item
            self._save_items()

            # Update token count (rough estimate)
            self.token_count += len(str(item)) // 4

            return item.id
        except Exception as e:
            logger.error(
                f"Failed to store memory item: {str(e)}",
                error=e,
                item_id=item.id if item.id else "unknown"
            )
            raise MemoryStoreError(
                f"Failed to store memory item: {str(e)}",
                store_type="json_file",
                operation="store",
                original_error=e
            ) from e

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
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
                return item
            else:
                logger.debug(f"Memory item not found", item_id=item_id)
                return None
        except Exception as e:
            logger.error(
                f"Error retrieving memory item: {str(e)}",
                error=e,
                item_id=item_id
            )
            raise MemoryStoreError(
                f"Error retrieving memory item: {str(e)}",
                store_type="json_file",
                operation="retrieve",
                original_error=e
            ) from e

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
            logger.debug(f"Searching memory items", query=query)
            result = []

            for item in self.items.values():
                match = True
                for key, value in query.items():
                    if key == "memory_type":
                        if isinstance(value, str):
                            if item.memory_type.value != value:
                                match = False
                                break
                        elif hasattr(value, 'value'):  # Handle MemoryType enum
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
                    result.append(item)

            # Update token count (rough estimate)
            if result:
                self.token_count += sum(len(str(item)) for item in result) // 4

            logger.debug(f"Found {len(result)} matching memory items", query=query)
            return result
        except Exception as e:
            logger.error(
                f"Error searching memory items: {str(e)}",
                error=e,
                query=query
            )
            raise MemoryStoreError(
                f"Error searching memory items: {str(e)}",
                store_type="json_file",
                operation="search",
                original_error=e
            ) from e

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
            if item_id in self.items:
                logger.debug(f"Deleting memory item", item_id=item_id)
                del self.items[item_id]
                self._save_items()
                return True
            else:
                logger.debug(f"Memory item not found for deletion", item_id=item_id)
                return False
        except Exception as e:
            logger.error(
                f"Error deleting memory item: {str(e)}",
                error=e,
                item_id=item_id
            )
            raise MemoryStoreError(
                f"Error deleting memory item: {str(e)}",
                store_type="json_file",
                operation="delete",
                original_error=e
            ) from e

    def get_token_usage(self) -> int:
        """
        Get the current token usage estimate.

        Returns:
            The estimated token usage
        """
        return self.token_count
