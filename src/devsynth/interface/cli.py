"""CLI implementation of the UXBridge."""

from rich.console import Console
from rich.prompt import Confirm, Prompt
from typing import Optional, Sequence

from .ux_bridge import UXBridge


class CLIUXBridge(UXBridge):
    """Bridge for command line interactions using Rich."""

    def __init__(self) -> None:
        self.console = Console()

    def prompt(
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

    def confirm(self, message: str, *, default: bool = False) -> bool:
        return Confirm.ask(message, default=default)

    def print(self, message: str, *, highlight: bool = False) -> None:
        self.console.print(message, highlight=highlight)
