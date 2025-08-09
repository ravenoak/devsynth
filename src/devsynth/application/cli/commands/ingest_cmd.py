"""CLI command to run the ingestion pipeline."""

from __future__ import annotations

import os
from typing import Optional

import typer

from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

from ..ingest_cmd import ingest_cmd as _ingest_cmd
from ..registry import register
from ..utils import _env_flag, _resolve_bridge

logger = DevSynthLogger(__name__)


def ingest_cmd(
    manifest_path: Optional[str] = typer.Argument(
        None, help="Path to the project manifest"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Perform a dry run"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    validate_only: bool = typer.Option(
        False, "--validate-only", help="Only validate the manifest"
    ),
    *,
    yes: Optional[bool] = None,
    priority: Optional[str] = typer.Option(
        None, "--priority", help="Persist project priority"
    ),
    auto_phase_transitions: bool = typer.Option(
        True,
        "--auto-phase-transitions/--no-auto-phase-transitions",
        help="Automatically advance EDRR phases",
    ),
    defaults: bool = typer.Option(
        False, "--defaults", help="Use default values and skip prompts"
    ),
    non_interactive: Optional[bool] = None,
    bridge: Optional[UXBridge] = typer.Option(None, hidden=True),
) -> None:
    """Ingest a project into DevSynth."""

    bridge = _resolve_bridge(bridge if isinstance(bridge, UXBridge) else None)

    manifest_path = manifest_path or os.environ.get("DEVSYNTH_MANIFEST_PATH")

    env_dry_run = _env_flag("DEVSYNTH_INGEST_DRY_RUN")
    if env_dry_run is not None and not dry_run:
        dry_run = env_dry_run

    env_verbose = _env_flag("DEVSYNTH_INGEST_VERBOSE")
    if env_verbose is not None and not verbose:
        verbose = env_verbose

    env_validate = _env_flag("DEVSYNTH_INGEST_VALIDATE_ONLY")
    if env_validate is not None and not validate_only:
        validate_only = env_validate

    yes = _env_flag("DEVSYNTH_AUTO_CONFIRM") if yes is None else yes
    priority = priority or os.environ.get("DEVSYNTH_INGEST_PRIORITY")

    env_auto_phase = _env_flag("DEVSYNTH_INGEST_AUTO_PHASE_TRANSITIONS")
    if env_auto_phase is not None:
        auto_phase_transitions = env_auto_phase

    non_interactive = (
        _env_flag("DEVSYNTH_INGEST_NONINTERACTIVE")
        if non_interactive is None
        else non_interactive
    )
    if defaults:
        yes = True
        non_interactive = True

    _ingest_cmd(
        manifest_path=manifest_path,
        dry_run=dry_run,
        verbose=verbose,
        validate_only=validate_only,
        yes=yes or False,
        priority=priority,
        bridge=bridge,
        auto_phase_transitions=auto_phase_transitions,
        non_interactive=non_interactive or False,
    )


register("ingest", ingest_cmd)

__all__ = ["ingest_cmd"]
