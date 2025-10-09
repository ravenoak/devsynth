"""Structured logging utilities for memory adapter failures."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypedDict

from ...logging_setup import DevSynthLogger
from .dto import MemoryMetadataValue

logger = DevSynthLogger(__name__)


ErrorContext = dict[str, MemoryMetadataValue]
"""Normalized error context payload."""


def _coerce_context(
    context: Mapping[str, MemoryMetadataValue] | None,
) -> ErrorContext:
    if context is None:
        return {}
    return {str(key): value for key, value in context.items()}


@dataclass(slots=True)
class ErrorRecord:
    """Structured representation of a memory operation error."""

    timestamp: datetime
    operation: str
    adapter_name: str
    error_type: str
    error_message: str
    context: ErrorContext

    def serialize(self) -> dict[str, object]:
        """Return a JSON-serializable mapping for persistence."""

        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "adapter_name": self.adapter_name,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "context": self.context,
        }


class ErrorSummary(TypedDict):
    """Aggregate statistics describing captured memory errors."""

    total_errors: int
    by_adapter: dict[str, int]
    by_operation: dict[str, int]
    by_error_type: dict[str, int]


class MemoryErrorLogger:
    """Capture, persist, and analyse memory adapter errors."""

    def __init__(
        self,
        max_errors: int = 100,
        log_dir: Optional[str] = None,
        persist_errors: bool = True,
    ) -> None:
        self.max_errors = max_errors
        self.errors: list[ErrorRecord] = []
        self.persist_errors = persist_errors

        if log_dir is None:
            home_dir = os.path.expanduser("~")
            self.log_dir = os.path.join(home_dir, ".devsynth", "logs", "memory")
        else:
            self.log_dir = log_dir

        if self.persist_errors:
            os.makedirs(self.log_dir, exist_ok=True)

    def log_error(
        self,
        operation: str,
        adapter_name: str,
        error: Exception,
        context: Mapping[str, MemoryMetadataValue] | None = None,
    ) -> ErrorRecord:
        """Log an error that occurred during a memory operation."""

        record = ErrorRecord(
            timestamp=datetime.now(),
            operation=operation,
            adapter_name=adapter_name,
            error_type=type(error).__name__,
            error_message=str(error),
            context=_coerce_context(context),
        )

        self.errors.append(record)
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors :]

        logger.error(
            "Memory operation '%s' failed on adapter '%s': %s: %s",
            operation,
            adapter_name,
            record.error_type,
            record.error_message,
        )

        if self.persist_errors:
            self._persist_error(record)

        return record

    def _persist_error(self, record: ErrorRecord) -> None:
        """Persist an error entry to disk."""

        try:
            timestamp = record.timestamp
            filename = f"memory_error_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
            filepath = os.path.join(self.log_dir, filename)
            with open(filepath, "w", encoding="utf-8") as handle:
                json.dump(record.serialize(), handle, indent=2)
        except Exception as exc:  # pragma: no cover - persistence failure is non-fatal
            logger.error("Failed to persist error log: %s", exc)

    def get_recent_errors(
        self,
        operation: Optional[str] = None,
        adapter_name: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[ErrorRecord]:
        """Get recent errors, optionally filtered by criteria."""

        filtered: list[ErrorRecord] = list(self.errors)

        if operation is not None:
            filtered = [record for record in filtered if record.operation == operation]

        if adapter_name is not None:
            filtered = [
                record for record in filtered if record.adapter_name == adapter_name
            ]

        if error_type is not None:
            filtered = [
                record for record in filtered if record.error_type == error_type
            ]

        return sorted(filtered, key=lambda record: record.timestamp, reverse=True)[
            :limit
        ]

    def get_error_summary(self) -> ErrorSummary:
        """Get a summary of errors by type, adapter, and operation."""

        if not self.errors:
            summary: ErrorSummary = {
                "total_errors": 0,
                "by_adapter": {},
                "by_operation": {},
                "by_error_type": {},
            }
            return summary

        by_adapter: dict[str, int] = {}
        by_operation: dict[str, int] = {}
        by_error_type: dict[str, int] = {}

        for record in self.errors:
            by_adapter[record.adapter_name] = by_adapter.get(record.adapter_name, 0) + 1
            by_operation[record.operation] = by_operation.get(record.operation, 0) + 1
            by_error_type[record.error_type] = (
                by_error_type.get(record.error_type, 0) + 1
            )

        summary: ErrorSummary = {
            "total_errors": len(self.errors),
            "by_adapter": by_adapter,
            "by_operation": by_operation,
            "by_error_type": by_error_type,
        }
        return summary

    def clear_errors(self) -> None:
        """Clear the in-memory error log."""

        self.errors = []


memory_error_logger = MemoryErrorLogger()
