"""Execute a refactor workflow based on the current project state."""

from __future__ import annotations

import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devsynth.interface.ux_bridge import UXBridge

from ...orchestration.refactor_workflow import refactor_workflow_manager
from ..utils import _resolve_bridge


def refactor_cmd(
    path: str | None = None, *, bridge: UXBridge | None = None
) -> None:
    """
    Execute a refactor workflow based on the current project state.

    This command analyzes the current project state, determines the optimal workflow,
    and suggests appropriate next steps.

    Args:
        path: Path to the project root directory (default: current directory)

    Example:
        `devsynth refactor --path ./my-project`
    """

    bridge = _resolve_bridge(bridge)
    try:
        console = Console()

        # Show a welcome message for the refactor command
        bridge.print(
            Panel(
                "[bold blue]DevSynth Refactor Workflow[/bold blue]\n\n"
                "This command will analyze your project state, determine the optimal workflow, "
                "and suggest appropriate next steps.",
                title="Refactor Workflow",
                border_style="blue",
            )
        )

        # Set the project path
        project_path = path or os.getcwd()

        # Execute the refactor workflow
        result = refactor_workflow_manager.execute_refactor_workflow(project_path)

        if result.get("success", False):
            # Display the workflow information
            bridge.display_result(f"[green]Workflow:[/green] {result['workflow']}")
            bridge.display_result(
                f"[green]Entry Point:[/green] {result['entry_point']}"
            )

            # Display the suggestions
            bridge.display_result("\n[bold]Suggested Next Steps:[/bold]")

            # Create a table for the suggestions
            table = Table(show_header=True, header_style="bold")
            table.add_column("Priority", style="cyan")
            table.add_column("Command", style="green")
            table.add_column("Description")

            for suggestion in result["suggestions"]:
                table.add_row(
                    suggestion["priority"].upper(),
                    suggestion["command"],
                    suggestion["description"],
                )

            bridge.print(table)

            # Display the message
            bridge.display_result(f"\n[green]{result['message']}[/green]")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message', 'Unknown error')}"
            )
    except Exception as e:
        bridge.display_result(f"[red]Error:[/red] {str(e)}")


__all__ = ["refactor_cmd"]
