"""Inspect requirements from a file or interactively."""

from __future__ import annotations

from typing import Optional

from devsynth.core.workflows import filter_args, inspect_requirements
from devsynth.interface.ux_bridge import UXBridge

from ..utils import _check_services, _resolve_bridge


def inspect_cmd(
    input_file: str | None = None,
    interactive: bool = False,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Inspect requirements from a file or interactively.

    Example:
        `devsynth inspect --input requirements.txt`
    """

    bridge = _resolve_bridge(bridge)
    try:
        if not _check_services(bridge):
            return
        args = filter_args({"input": input_file, "interactive": interactive})
        result = inspect_requirements(**args)
        if result.get("success"):
            bridge.display_result("[green]Requirements inspection completed.[/green]")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message')}", highlight=False
            )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


__all__ = ["inspect_cmd"]
