from pathlib import Path

import pytest

from devsynth.application.prompts.models import PromptVariant
from devsynth.application.prompts.persistence import (
    PromptVariantStorageError,
    load_prompt_variants,
    save_prompt_variants,
)


@pytest.mark.medium
def test_save_and_load_round_trip(tmp_path: Path) -> None:
    """Prompt variant persistence round-trips serialized data."""

    variant = PromptVariant("example template")
    stored = {"template": [variant.to_dict()]}

    save_prompt_variants(tmp_path, stored)
    loaded = load_prompt_variants(tmp_path)

    assert loaded == stored


@pytest.mark.medium
def test_load_raises_for_missing_file(tmp_path: Path) -> None:
    """Loading without a persisted file raises a storage error."""

    with pytest.raises(PromptVariantStorageError):
        load_prompt_variants(tmp_path)


@pytest.mark.medium
def test_load_raises_for_invalid_json(tmp_path: Path) -> None:
    """Invalid JSON content is surfaced via the storage error."""

    (tmp_path / "prompt_variants.json").write_text("{", encoding="utf-8")

    with pytest.raises(PromptVariantStorageError):
        load_prompt_variants(tmp_path)
