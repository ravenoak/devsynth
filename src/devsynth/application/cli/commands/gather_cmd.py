"""Interactively gather project requirements."""

from __future__ import annotations

from typing import Optional

from devsynth.core.workflows import gather_requirements
from devsynth.interface.ux_bridge import UXBridge

from ..utils import _resolve_bridge


def gather_cmd(
    output_file: str = "requirements_plan.yaml", *, bridge: Optional[UXBridge] = None
) -> None:
    """Interactively gather project goals, constraints and priority."""

    bridge = _resolve_bridge(bridge)
    gather_requirements(bridge, output_file=output_file)


__all__ = ["gather_cmd"]
