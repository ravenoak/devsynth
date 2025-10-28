"""Persistent context manager implementation with DTO-aligned typing."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import cast

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .context_manager import ContextState, ContextValue, StructuredContextManager

logger = DevSynthLogger(__name__)


class PersistentContextManager(StructuredContextManager):
    """Persistent implementation of ContextManager."""

    def __init__(
        self, file_path: str, max_context_size: int = 1000, expiration_days: int = 7
    ) -> None:
        """
        Initialize a PersistentContextManager.

        Args:
            file_path: Base path for storing context files
            max_context_size: Maximum size of context in tokens (approximate)
            expiration_days: Number of days after which context items expire
        """
        self.base_path = file_path
        self.context_file = os.path.join(self.base_path, "context.json")
        self.max_context_size = max_context_size
        self.expiration_days = expiration_days
        self.context: ContextState = self._load_context()
        self.token_count = 0

    def _ensure_directory_exists(self) -> None:
        """Ensure the directory for storing files exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def _load_context(self) -> ContextState:
        """Load context from the JSON file."""
        if not os.path.exists(self.context_file):
            return {}

        try:
            with open(self.context_file) as f:
                data = json.load(f)

            # Prune expired context items
            now = datetime.now()
            context: ContextState = {}
            for key, item in data.get("context", {}).items():
                if "timestamp" in item:
                    timestamp = datetime.fromisoformat(item["timestamp"])
                    if (now - timestamp).days <= self.expiration_days:
                        context[key] = cast(ContextValue, item["value"])
                else:
                    context[key] = cast(ContextValue, item.get("value"))

            return context
        except Exception as e:
            # Log error and return empty dict
            logger.info(f"Error loading context: {str(e)}")
            return {}

    def _save_context(self) -> None:
        """Save context to the JSON file."""
        self._ensure_directory_exists()

        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "context": {},
        }

        for key, value in self.context.items():
            # Convert value to string if it's not serializable
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                serialized_value = str(value)
            else:
                serialized_value = value

            data["context"][key] = {
                "value": serialized_value,
                "timestamp": datetime.now().isoformat(),
            }

        with open(self.context_file, "w") as f:
            json.dump(data, f, indent=2)

    def _prune_context(self) -> None:
        """Prune context to stay within token budget."""
        if (
            len(str(self.context)) <= self.max_context_size * 4
        ):  # Rough estimate of 4 chars per token
            return

        # Get context items with timestamps
        context_with_timestamps: dict[str, datetime] = {}
        try:
            with open(self.context_file) as f:
                data = json.load(f)

            for key, item in data.get("context", {}).items():
                if key in self.context and "timestamp" in item:
                    context_with_timestamps[key] = datetime.fromisoformat(
                        item["timestamp"]
                    )
        except Exception:
            # If we can't load timestamps, use current time for all items
            now = datetime.now()
            for key in self.context:
                context_with_timestamps[key] = now

        # Sort keys by timestamp (oldest first)
        sorted_keys = sorted(
            self.context.keys(),
            key=lambda k: context_with_timestamps.get(k, datetime.min),
        )

        # Remove oldest items until we're under the limit
        while len(str(self.context)) > self.max_context_size * 4 and sorted_keys:
            key = sorted_keys.pop(0)
            del self.context[key]

    def add_to_context(self, key: str, value: ContextValue) -> None:
        """Add a value to the current context."""
        self.context[key] = value
        self._prune_context()
        self._save_context()

        # Update token count (rough estimate)
        self.token_count += len(str({key: value})) // 4

    def get_from_context(self, key: str) -> ContextValue | None:
        """Get a value from the current context."""
        value = self.context.get(key)

        # Update token count (rough estimate)
        if value is not None:
            self.token_count += len(str({key: value})) // 4

        return value

    def get_full_context(self) -> ContextState:
        """Get the full current context."""
        # Update token count (rough estimate)
        self.token_count += len(str(self.context)) // 4

        return self.context.copy()

    def clear_context(self) -> None:
        """Clear the current context."""
        self.context.clear()
        self._save_context()

    def get_relevant_context(self, query: str, max_items: int = 5) -> ContextState:
        """
        Get context items relevant to the query.

        Args:
            query: The query string to match against context keys and values
            max_items: Maximum number of items to return

        Returns:
            Dictionary of relevant context items
        """
        # Simple relevance implementation based on string matching
        scores: dict[str, int] = {}
        for key, value in self.context.items():
            # Calculate simple relevance score based on substring matching
            score = 0
            str_value = str(value).lower()
            str_key = str(key).lower()
            query_lower = query.lower()

            if query_lower in str_key:
                score += 3
            if query_lower in str_value:
                score += 1

            if score > 0:
                scores[key] = score

        # Sort by score (descending) and take top max_items
        relevant_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[
            :max_items
        ]
        result: ContextState = {k: self.context[k] for k in relevant_keys}

        # Update token count (rough estimate)
        if result:
            self.token_count += len(str(result)) // 4

        return result

    def get_token_usage(self) -> int:
        """Get the current token usage estimate."""
        return self.token_count
