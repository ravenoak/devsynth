"""Persistence helpers for the EDRR coordinator."""

from __future__ import annotations

import copy
from typing import Any

from devsynth.domain.models.memory import MemoryType
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

logger = DevSynthLogger(__name__)


class PersistenceMixin:
    """Provide persistence utilities shared across coordinator implementations."""

    def _safe_store_with_edrr_phase(
        self,
        content: Any,
        memory_type: MemoryType,
        edrr_phase: str,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Safely store a memory item with an EDRR phase."""

        if not self.memory_manager:
            logger.warning("Memory manager not available for storing memory items")
            return None

        try:
            item_id = self.memory_manager.store_with_edrr_phase(
                content, memory_type, edrr_phase, metadata
            )
            try:
                self.memory_manager.flush_updates()
            except Exception as flush_error:  # pragma: no cover - defensive
                logger.debug(
                    f"Failed to flush memory updates for {memory_type}: {flush_error}"
                )
            return item_id
        except Exception as error:  # pragma: no cover - defensive
            logger.error("Failed to store memory item with EDRR phase: %s", error)
            return None

    def _safe_retrieve_with_edrr_phase(
        self,
        item_type: MemoryType,
        edrr_phase: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Safely retrieve an item stored with a specific EDRR phase."""

        if not self.memory_manager:
            logger.warning("Memory manager not available for retrieving memory items")
            return {}

        try:
            if hasattr(self.memory_manager, "retrieve_with_edrr_phase"):
                result = self.memory_manager.retrieve_with_edrr_phase(
                    item_type, edrr_phase, metadata
                )
                if isinstance(result, list):
                    return {"items": result}
                if isinstance(result, dict):
                    return result
                if result is None:
                    return {}
                logger.warning(
                    "Unexpected result type %s from retrieve_with_edrr_phase",
                    type(result),
                )
                return {"items": [result]}
            logger.warning("Memory manager does not support retrieve_with_edrr_phase")
            return {}
        except Exception as error:  # pragma: no cover - defensive
            logger.error("Failed to retrieve memory item with EDRR phase: %s", error)
            return {}

    def _persist_context_snapshot(self, phase: Phase) -> None:
        """Persist preserved context for a phase."""

        if not getattr(self, "_preserved_context", None):
            return

        metadata = {"cycle_id": self.cycle_id, "type": "CONTEXT_SNAPSHOT"}
        self._safe_store_with_edrr_phase(
            copy.deepcopy(self._preserved_context),
            MemoryType.CONTEXT,
            phase.value,
            metadata,
        )


__all__ = ["PersistenceMixin"]
