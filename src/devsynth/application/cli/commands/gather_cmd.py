"""Interactively gather project requirements."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from devsynth.config import get_project_config
from devsynth.core.workflows import gather_requirements
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logger import get_logger

from ..utils import _resolve_bridge


def gather_cmd(
    output_file: str = "requirements_plan.yaml", *, bridge: UXBridge | None = None
) -> None:
    """Interactively gather project goals, constraints and priority.

    After gathering requirements the project configuration is loaded to ensure
    that the ``priority`` field was persisted.  If the field is missing a warning
    is emitted to aid debugging."""

    bridge = _resolve_bridge(bridge)
    gather_requirements(bridge, output_file=output_file)

    cfg = get_project_config(Path("."))
    if getattr(cfg, "priority", None) is None:
        logger = get_logger(__name__)
        logger.warning("Priority not persisted to project configuration")


__all__ = ["gather_cmd"]
