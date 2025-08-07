"""Shared utilities for CLI command modules."""

from __future__ import annotations

import json
import os
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from typer.models import OptionInfo

from devsynth.config import get_settings
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger, get_logger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def _resolve_bridge(b: Optional[UXBridge]) -> UXBridge:
    """Return the provided bridge or fall back to the module default."""

    return b if b is not None else bridge


def _env_flag(name: str) -> Optional[bool]:
    """Return boolean value for ``name`` if set, otherwise ``None``."""

    val = os.environ.get(name)
    if val is None:
        return None
    return val.lower() in {"1", "true", "yes"}


def _parse_features(value: Optional[Union[List[str], str]]) -> Dict[str, bool]:
    """Parse feature flags from list or JSON string."""

    if value is None or isinstance(value, OptionInfo):
        return {}
    if isinstance(value, list):
        if len(value) == 1:
            item = value[0]
            try:
                parsed = json.loads(item)
            except json.JSONDecodeError:
                return {item: True}
        else:
            return {f: True for f in value}
    else:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {f.strip(): True for f in value.split(";") if f.strip()}

    if isinstance(parsed, dict):
        return {k: bool(v) for k, v in parsed.items()}
    if isinstance(parsed, list):
        return {f: True for f in parsed}
    return {}


def _check_services(bridge: Optional[UXBridge] = None) -> bool:
    """Verify required services are available."""

    bridge = _resolve_bridge(bridge)
    settings = get_settings()
    messages: List[str] = []

    # Check ChromaDB availability only when the feature flag is enabled
    chromadb_enabled = getattr(settings, "enable_chromadb", False)
    if (
        chromadb_enabled
        and settings.vector_store_enabled
        and settings.memory_store_type == "chromadb"
    ):
        if importlib.util.find_spec("chromadb") is None:
            messages.append(
                "ChromaDB support is enabled but the 'chromadb' package is missing."
            )
    # Check Kuzu availability when vector store is enabled
    if settings.vector_store_enabled and settings.memory_store_type == "kuzu":
        if importlib.util.find_spec("kuzu") is None:
            messages.append(
                "Kuzu support is enabled but the 'kuzu' package is missing."
            )

    # Check LLM provider configuration
    provider = settings.provider_type
    if provider == "openai" and not settings.openai_api_key:
        messages.append("OPENAI_API_KEY is not set for the OpenAI provider.")
    if provider == "lmstudio" and not settings.lm_studio_endpoint:
        messages.append(
            "LM_STUDIO_ENDPOINT is not configured for the LM Studio provider."
        )

    if messages:
        for msg in messages:
            bridge.display_result(f"[red]{msg}[/red]", highlight=False)
        bridge.display_result(
            "[yellow]Use 'devsynth config' or edit your project.yaml to update settings.[/yellow]"
        )
        return False

    return True


def _handle_error(
    bridge: UXBridge, error: Union[Exception, Dict[str, Any], str]
) -> None:
    """Delegate to the bridge's enhanced error handler."""

    logger = get_logger("cli_commands")
    if isinstance(error, Exception):
        logger.error("Command error: %s", error, exc_info=True)
    else:
        logger.error("Command error: %s", error)
    bridge.handle_error(error)


def _validate_file_path(path: str, must_exist: bool = True) -> Optional[str]:
    """Validate a file path.

    Args:
        path: The file path to validate
        must_exist: Whether the file must exist

    Returns:
        An error message if validation fails, None otherwise
    """

    if not path:
        return "File path cannot be empty"

    file_path = Path(path)
    if must_exist and not file_path.exists():
        return f"File '{path}' does not exist"

    return None


__all__ = [
    "bridge",
    "_resolve_bridge",
    "_env_flag",
    "_parse_features",
    "_check_services",
    "_handle_error",
    "_validate_file_path",
]

