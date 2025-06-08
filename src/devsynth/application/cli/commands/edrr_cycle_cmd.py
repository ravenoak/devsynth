from pathlib import Path
from rich.console import Console

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

logger = DevSynthLogger(__name__)


def edrr_cycle_cmd(manifest: str) -> None:
    """Run an EDRR cycle from a manifest file."""
    console = Console()
    try:
        manifest_path = Path(manifest)
        if not manifest_path.exists():
            console.print(f"[red]Manifest file not found:[/red] {manifest_path}")
            return

        console.print("[bold]Starting EDRR cycle[/bold]")
        memory_adapter = TinyDBMemoryAdapter()
        memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
        wsde_team = WSDETeam()
        code_analyzer = CodeAnalyzer()
        ast_transformer = AstTransformer()
        prompt_manager = PromptManager()
        documentation_manager = DocumentationManager(memory_manager)

        coordinator = EDRRCoordinator(
            memory_manager=memory_manager,
            wsde_team=wsde_team,
            code_analyzer=code_analyzer,
            ast_transformer=ast_transformer,
            prompt_manager=prompt_manager,
            documentation_manager=documentation_manager,
        )

        coordinator.start_cycle_from_manifest(manifest_path, is_file=True)

        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            coordinator.progress_to_phase(phase)

        result_id = memory_manager.store_with_edrr_phase(
            coordinator.results,
            "EDRR_CYCLE_RESULTS",
            Phase.RETROSPECT.value,
            {"cycle_id": coordinator.cycle_id},
        )

        console.print(
            f"[green]EDRR cycle completed.[/green] Results stored with id {result_id}"
        )
    except DevSynthError as err:
        console.print(f"[red]Error:[/red] {err}")
    except Exception as exc:
        console.print(f"[red]Unexpected error:[/red] {exc}")
        logger.error(f"Unexpected error running EDRR cycle: {exc}")
