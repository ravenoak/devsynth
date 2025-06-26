from pathlib import Path
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.core import run_pipeline
from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError
from devsynth.config import load_project_config

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def edrr_cycle_cmd(manifest: str, auto: bool = True) -> None:
    """Run an EDRR cycle from a manifest file.

    Example:
        `devsynth edrr-cycle manifest.yaml`

    Args:
        manifest: Path to the manifest file.
        auto: Whether to automatically progress through phases.
    """
    try:
        manifest_path = Path(manifest)
        if not manifest_path.exists():
            msg = f"[red]Manifest file not found:[/red] {manifest_path}"
            bridge.print(msg)
            return

        bridge.print("[bold]Starting EDRR cycle[/bold]")
        memory_adapter = TinyDBMemoryAdapter()
        memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
        wsde_team = WSDETeam()
        code_analyzer = CodeAnalyzer()
        ast_transformer = AstTransformer()
        prompt_manager = PromptManager()
        documentation_manager = DocumentationManager(memory_manager)

        project_cfg = load_project_config().config.as_dict()
        edrr_cfg = project_cfg.get("edrr", {})
        edrr_cfg.setdefault("phase_transition", {})["auto"] = auto
        project_cfg["edrr"] = edrr_cfg

        coordinator = EDRRCoordinator(
            memory_manager=memory_manager,
            wsde_team=wsde_team,
            code_analyzer=code_analyzer,
            ast_transformer=ast_transformer,
            prompt_manager=prompt_manager,
            documentation_manager=documentation_manager,
            config=project_cfg,
        )

        coordinator.start_cycle_from_manifest(manifest_path, is_file=True)

        for phase in [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]:
            coordinator.progress_to_phase(phase)

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

        bridge.print(
            "[green]EDRR cycle completed.[/green] "
            f"Results stored with id {result_id}"
        )
    except DevSynthError as err:
        bridge.print(f"[red]Error:[/red] {err}")
    except Exception as exc:
        bridge.print(f"[red]Unexpected error:[/red] {exc}")
        logger.error(f"Unexpected error running EDRR cycle: {exc}")
