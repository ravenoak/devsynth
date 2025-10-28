import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from tqdm import tqdm

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.core import run_pipeline
from devsynth.core.config_loader import load_config
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.exceptions import DevSynthError
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

logger = DevSynthLogger(__name__)
# Default bridge for CLI output
bridge: UXBridge = CLIUXBridge()


def edrr_cycle_cmd(
    manifest: str | None = None,
    prompt: str | None = None,
    context: str | None = None,
    max_iterations: int = 3,
    auto: bool = True,
    bridge: UXBridge | None = None,
) -> None:
    """Run an enhanced EDRR cycle from a manifest file or a prompt.

    This command executes an Expand-Differentiate-Refine-Retrospect (EDRR) cycle, which is a
    structured approach to problem-solving and development. The cycle can be initiated either
    from a manifest file that defines the task and constraints, or directly from a prompt.

    This implementation uses the EnhancedEDRRCoordinator which provides improved phase transitions,
    quality metrics, and safeguards against infinite loops.

    Examples:
        Run from a manifest file:
        `devsynth edrr-cycle --manifest manifest.yaml`

        Run from a prompt:
        `devsynth edrr-cycle --prompt "Improve error handling in the API endpoints"`

        Run with additional context:
        `devsynth edrr-cycle --prompt "Optimize database queries" --context "Focus on reducing N+1 queries"`

        Control the maximum number of iterations:
        `devsynth edrr-cycle --prompt "Refactor the authentication system" --max-iterations 5`

        Disable automatic phase transitions:
        `devsynth edrr-cycle --prompt "Implement authentication" --auto false`

    Args:
        manifest: Path to the manifest file. If provided, the cycle will be run from this file.
        prompt: A text prompt describing the task. Required if manifest is not provided.
        context: Additional context for the prompt. Optional.
        max_iterations: Maximum number of iterations for the cycle. Default is 3.
        auto: Whether to automatically progress through phases. Default is True.
        bridge: UX bridge for output. If not provided, the default CLI bridge will be used.
    """
    # Use the provided bridge or the global default bridge
    ux_bridge = bridge if bridge is not None else globals()["bridge"]

    try:
        # Validate input parameters
        if not manifest and not prompt:
            ux_bridge.print(
                "[red]Error:[/red] Either manifest or prompt must be provided"
            )
            return

        # Initialize components
        ux_bridge.print("[bold]Starting Enhanced EDRR cycle[/bold]")
        memory_adapter = TinyDBMemoryAdapter()
        memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
        wsde_team = WSDETeam(name="EdrrCycleCmdTeam")
        code_analyzer = CodeAnalyzer()
        ast_transformer = AstTransformer()
        prompt_manager = PromptManager()
        documentation_manager = DocumentationManager(memory_manager)

        # Configure EDRR
        project_cfg = load_config().as_dict()
        edrr_cfg = project_cfg.get("edrr", {})
        edrr_cfg.setdefault("phase_transition", {})["auto"] = auto

        # Add enhanced configuration
        edrr_cfg.setdefault("quality_based_transitions", True)
        edrr_cfg.setdefault("phase_transition_timeout", 3600)  # 1 hour default
        project_cfg["edrr"] = edrr_cfg

        # Create enhanced coordinator
        coordinator = EnhancedEDRRCoordinator(
            memory_manager=memory_manager,
            wsde_team=wsde_team,
            code_analyzer=code_analyzer,
            ast_transformer=ast_transformer,
            prompt_manager=prompt_manager,
            documentation_manager=documentation_manager,
            config=project_cfg,
        )

        # Start cycle from manifest or prompt
        if manifest:
            manifest_path = Path(manifest)
            if not manifest_path.exists():
                ux_bridge.print(f"[red]Manifest file not found:[/red] {manifest_path}")
                return

            ux_bridge.print(
                f"[bold]Starting EDRR cycle from manifest:[/bold] {manifest}"
            )
            coordinator.start_cycle_from_manifest(manifest_path, is_file=True)
        else:
            # Create a task dictionary from the prompt and context
            task = {
                "description": prompt,
                "context": context or "",
                "max_iterations": max_iterations,
                "created_at": time.time(),
            }

            ux_bridge.print(f"[bold]Starting EDRR cycle from prompt:[/bold] {prompt}")
            if context:
                ux_bridge.print(f"[bold]Context:[/bold] {context}")

            coordinator.start_cycle(task)

        # Progress through phases with progress reporting
        phases = [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]

        # Create a progress bar for the phases
        with tqdm(total=len(phases), desc="EDRR Cycle Progress", unit="phase") as pbar:
            for phase in phases:
                phase_name = phase.name.capitalize()
                pbar.set_description(f"Phase: {phase_name}")
                ux_bridge.print(f"[bold]Executing {phase_name} phase[/bold]")

                # Execute the phase
                coordinator.progress_to_phase(phase)

                # Update progress
                pbar.update(1)

                # Report phase completion
                ux_bridge.print(f"[green]Completed {phase_name} phase[/green]")

        # Generate and store the final report
        ux_bridge.print("[bold]Generating final report[/bold]")
        final_report = coordinator.generate_report()
        result_id = memory_manager.store_with_edrr_phase(
            final_report,
            "EDRR_CYCLE_RESULTS",
            Phase.RETROSPECT.value,
            {"cycle_id": coordinator.cycle_id},
        )

        # Persist report through the standard pipeline workflow
        try:
            run_pipeline(report=final_report)
        except Exception as pipeline_err:  # pragma: no cover - best effort
            logger.error(
                "Failed to persist report via pipeline: %s",
                pipeline_err,
            )

        # Print summary
        ux_bridge.print(
            "[green]EDRR cycle completed.[/green] "
            f"Results stored with id {result_id}"
        )

        # Print key insights from the report
        if "insights" in final_report:
            ux_bridge.print("\n[bold]Key Insights:[/bold]")
            for i, insight in enumerate(final_report["insights"], 1):
                ux_bridge.print(f"{i}. {insight}")

        # Print next steps if available
        if "next_steps" in final_report:
            ux_bridge.print("\n[bold]Recommended Next Steps:[/bold]")
            for i, step in enumerate(final_report["next_steps"], 1):
                ux_bridge.print(f"{i}. {step}")

    except DevSynthError as err:
        ux_bridge.print(f"[red]Error:[/red] {err}")
    except Exception as exc:
        ux_bridge.print(f"[red]Unexpected error:[/red] {exc}")
        logger.error(f"Unexpected error running EDRR cycle: {exc}")
