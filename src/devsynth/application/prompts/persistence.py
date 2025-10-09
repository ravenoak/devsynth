"""Persistence helpers for prompt auto-tuning data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .models import StoredPromptVariant

PromptVariantsDocument = Dict[str, List[StoredPromptVariant]]


class PromptVariantStorageError(Exception):
    """Raised when prompt variant persistence fails."""


def load_prompt_variants(storage_dir: Path) -> PromptVariantsDocument:
    """Load prompt variants from ``prompt_variants.json`` within ``storage_dir``."""

    path = storage_dir / "prompt_variants.json"
    try:
        with path.open("r", encoding="utf-8") as file:
            data: PromptVariantsDocument = json.load(file)
    except FileNotFoundError as exc:  # pragma: no cover - handled by caller logging
        raise PromptVariantStorageError(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise PromptVariantStorageError(str(exc)) from exc
    return data


def save_prompt_variants(storage_dir: Path, data: PromptVariantsDocument) -> None:
    """Persist prompt variants to ``prompt_variants.json`` within ``storage_dir``."""

    path = storage_dir / "prompt_variants.json"
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
    except OSError as exc:  # pragma: no cover - handled by caller logging
        raise PromptVariantStorageError(str(exc)) from exc
