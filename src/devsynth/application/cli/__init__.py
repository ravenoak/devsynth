from __future__ import annotations

"""Package initialisation for the DevSynth CLI."""

from typing import Callable

from devsynth.logging_setup import DevSynthLogger

from ._command_exports import COMMAND_ATTRIBUTE_NAMES, COMMAND_ATTRIBUTE_TO_SLUG
from .registry import COMMAND_REGISTRY

logger = DevSynthLogger(__name__)

CommandCallable = Callable[..., object] | object

_COMMANDS_LOADED = False

# Placeholders populated when command modules import successfully.
config_app: CommandCallable | None = None
inspect_code_cmd: CommandCallable | None = None
ingest_cmd: CommandCallable | None = None


def _registered_command(slug: str) -> CommandCallable:
    """Return the callable registered for ``slug``."""

    try:
        return COMMAND_REGISTRY[slug]
    except KeyError as exc:  # pragma: no cover - defensive guardrail
        raise RuntimeError(f"CLI command '{slug}' is not registered") from exc


def _register_commands() -> None:
    """Ensure CLI command modules are imported and registered."""

    global _COMMANDS_LOADED, config_app, inspect_code_cmd, ingest_cmd

    if _COMMANDS_LOADED:
        return

    try:  # pragma: no cover - exercised indirectly via attribute access
        from .commands import (
            config_cmds,
            diagnostics_cmds,
            documentation_cmds,
            extra_cmds,
            generation_cmds,
            interface_cmds,
            metrics_cmds,
            pipeline_cmds,
            validation_cmds,
        )
        from .commands.config_cmds import config_app as loaded_config_app
        from .commands.inspect_code_cmd import inspect_code_cmd as loaded_inspect
        from .ingest_cmd import ingest_cmd as loaded_ingest
    except ModuleNotFoundError as exc:
        logger.debug(
            "Skipping CLI command registration due to missing optional dependency: %s",
            exc,
        )
        _COMMANDS_LOADED = True
        return

    config_app = loaded_config_app
    inspect_code_cmd = loaded_inspect
    ingest_cmd = loaded_ingest

    for attr_name in COMMAND_ATTRIBUTE_NAMES:
        slug = COMMAND_ATTRIBUTE_TO_SLUG.get(attr_name)
        if slug is None:
            continue
        try:
            globals()[attr_name] = _registered_command(slug)
        except RuntimeError as exc:  # pragma: no cover - optional commands
            logger.debug(
                "Skipping CLI export for %s: %s",
                slug,
                exc,
            )
            globals()[attr_name] = None

    _COMMANDS_LOADED = True


def __getattr__(name: str) -> object:
    """Lazily expose CLI command callables when requested."""

    if (
        name
        in {
            "config_app",
            "inspect_code_cmd",
            "ingest_cmd",
        }
        or name in COMMAND_ATTRIBUTE_NAMES
    ):
        _register_commands()
        if name in globals() and globals()[name] is not None:
            return globals()[name]
        raise AttributeError(f"CLI command '{name}' is unavailable")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "config_app",
    "inspect_code_cmd",
    "ingest_cmd",
    "COMMAND_REGISTRY",
] + list(COMMAND_ATTRIBUTE_NAMES)


_register_commands()
