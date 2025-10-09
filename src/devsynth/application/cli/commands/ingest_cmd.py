"""CLI command to run the ingestion pipeline."""

from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import typer
from typer.models import OptionInfo

from devsynth.application.memory.adapters.enhanced_graph_memory_adapter import (
    EnhancedGraphMemoryAdapter,
)
from devsynth.exceptions import MemoryItemNotFoundError
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

from ..ingest_cmd import ingest_cmd as _ingest_cmd
from ..registry import register
from ..utils import _env_flag, _resolve_bridge

logger = DevSynthLogger(__name__)


@dataclass(slots=True)
class IngestCLIOptions:
    """Typed configuration payload for the ingestion command."""

    manifest_path: Path | None
    dry_run: bool
    verbose: bool
    validate_only: bool
    yes: bool
    priority: Optional[str]
    bridge: UXBridge
    auto_phase_transitions: bool
    non_interactive: bool
    defaults: bool

    def to_kwargs(self) -> Dict[str, object]:
        """Return a shallow mapping suitable for ``_ingest_cmd``."""

        return {
            "manifest_path": self.manifest_path,
            "dry_run": self.dry_run,
            "verbose": self.verbose,
            "validate_only": self.validate_only,
            "yes": self.yes,
            "priority": self.priority,
            "bridge": self.bridge,
            "auto_phase_transitions": self.auto_phase_transitions,
            "non_interactive": self.non_interactive,
            "defaults": self.defaults,
        }


def ingest_cmd(
    manifest_path: Optional[Path] = typer.Argument(
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
    non_interactive: Optional[bool] = typer.Option(
        None, "--non-interactive", help="Run without interactive prompts"
    ),
    bridge: Optional[UXBridge] = typer.Option(None, hidden=True),
    research_artifact: Optional[List[Path]] = typer.Option(
        None,
        "--research-artifact",
        help=(
            "Summarise and persist a research artefact before ingestion. "
            "Specify multiple times to ingest several artefacts."
        ),
    ),
    verify_research_hash: Optional[List[str]] = typer.Option(
        None,
        "--verify-research-hash",
        help=(
            "Verify an artefact hash using <expected>=<path> syntax. "
            "Repeat for multiple artefacts."
        ),
    ),
) -> None:
    """Ingest a project into DevSynth."""

    resolved_bridge = _resolve_bridge(bridge if isinstance(bridge, UXBridge) else None)

    manifest_path = manifest_path or (
        Path(os.environ["DEVSYNTH_MANIFEST_PATH"])
        if os.environ.get("DEVSYNTH_MANIFEST_PATH")
        else None
    )

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

    adapter: EnhancedGraphMemoryAdapter | None = None

    def _ensure_adapter() -> EnhancedGraphMemoryAdapter:
        nonlocal adapter
        if adapter is None:
            base_dir = Path(
                os.environ.get(
                    "DEVSYNTH_GRAPH_MEMORY_PATH",
                    Path.cwd() / ".devsynth" / "memory",
                )
            )
            base_dir.mkdir(parents=True, exist_ok=True)
            adapter = EnhancedGraphMemoryAdapter(
                base_path=str(base_dir), use_rdflib_store=True
            )
        return adapter

    if isinstance(research_artifact, OptionInfo):
        research_artifact = None

    if isinstance(verify_research_hash, OptionInfo):
        verify_research_hash = None

    if research_artifact:
        graph_adapter = _ensure_adapter()
        for artifact_path in research_artifact:
            if not artifact_path.exists():
                raise typer.BadParameter(
                    f"Research artefact not found: {artifact_path}",
                    param_name="research_artifact",
                )
            try:
                published_at = datetime.datetime.fromtimestamp(
                    artifact_path.stat().st_mtime,
                    tz=datetime.timezone.utc,
                )
            except OSError:
                published_at = datetime.datetime.now(datetime.timezone.utc)

            artifact = graph_adapter.ingest_research_artifact_from_path(
                artifact_path,
                title=artifact_path.stem,
                citation_url=str(artifact_path),
                published_at=published_at,
            )
            logger.info(
                "Stored research artefact %s with evidence hash %s",
                artifact_path,
                artifact.evidence_hash,
            )
            try:
                provenance = graph_adapter.get_artifact_provenance(artifact.identifier)
            except MemoryItemNotFoundError:  # pragma: no cover - defensive
                provenance = {"supports": (), "derived_from": (), "roles": ()}
            logger.info(
                "Provenance summary for %s — supports=%s derived_from=%s roles=%s",
                artifact.identifier,
                ", ".join(provenance.get("supports", ())) or "none",
                ", ".join(provenance.get("derived_from", ())) or "none",
                ", ".join(provenance.get("roles", ())) or "none",
            )

    if verify_research_hash:
        graph_adapter = _ensure_adapter()
        for verification in verify_research_hash:
            expected, separator, raw_path = verification.partition("=")
            if not separator:
                raise typer.BadParameter(
                    "Expected <hash>=<path> format",
                    param_name="verify_research_hash",
                )

            file_path = Path(raw_path).expanduser().resolve()
            computed = graph_adapter.compute_evidence_hash(file_path)
            if computed != expected:
                raise typer.BadParameter(
                    (
                        "Hash mismatch for %s: expected %s but computed %s"
                        % (file_path, expected, computed)
                    ),
                    param_name="verify_research_hash",
                )
            logger.info("Verified research artefact %s (hash %s)", file_path, computed)

    options = IngestCLIOptions(
        manifest_path=manifest_path,
        dry_run=dry_run,
        verbose=verbose,
        validate_only=validate_only,
        yes=yes or False,
        priority=priority,
        bridge=resolved_bridge,
        auto_phase_transitions=auto_phase_transitions,
        non_interactive=non_interactive or False,
        defaults=defaults,
    )

    _ingest_cmd(**options.to_kwargs())


register("ingest", ingest_cmd)

__all__ = ["ingest_cmd"]
