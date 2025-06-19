"""CLI implementation of the UXBridge using Typer and Rich."""

from typing import Optional, Sequence

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from devsynth.interface.ux_bridge import UXBridge, ProgressIndicator


class CLIProgressIndicator(ProgressIndicator):
    """Rich progress indicator wrapper."""

    def __init__(self, console: Console, description: str, total: int) -> None:
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            console=console,
        )
        self._progress.start()
        self._task = self._progress.add_task(description, total=total)

    def update(self, *, advance: float = 1, description: Optional[str] = None) -> None:
        self._progress.update(self._task, advance=advance, description=description)

    def complete(self) -> None:
        self._progress.update(self._task, completed=True)
        self._progress.stop()



class CLIUXBridge(UXBridge):
    """Bridge for command line interactions.

    This implementation uses Rich for formatted output and Typer-compatible
    prompts so that the same workflow logic can be reused by different
    frontends.
    """

    def __init__(self) -> None:
        self.console = Console()

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        return Prompt.ask(
            message,
            choices=list(choices) if choices else None,
            default=default,
            show_default=show_default,
        )

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return Confirm.ask(message, default=default)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        self.console.print(message, highlight=highlight)

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return CLIProgressIndicator(self.console, description, total)
