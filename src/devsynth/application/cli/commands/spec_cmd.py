"""Generate specifications from a requirements file."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console

from devsynth.core.workflows import filter_args, generate_specs
from devsynth.interface.ux_bridge import UXBridge

from ..progress import create_enhanced_progress
from ..utils import (
    _check_services,
    _env_flag,
    _handle_error,
    _resolve_bridge,
    _validate_file_path,
)


def spec_cmd(
    requirements_file: str = "requirements.md",
    *,
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Generate specifications from a requirements file.

    This command analyzes a requirements file and generates detailed specifications
    that can be used for implementation.

    Args:
        requirements_file: Path to the requirements file (Markdown format)
        bridge: Optional UX bridge for interaction

    Examples:
        Generate specifications from the default requirements file:
        ```
        devsynth spec
        ```

        Generate specifications from a custom requirements file:
        ```
        devsynth spec --requirements-file custom_requirements.md
        ```
    """
    from devsynth.interface.progress_utils import run_with_progress

    console = Console()
    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Validate input file
        error = _validate_file_path(requirements_file)
        if error:
            bridge.display_result(f"[yellow]{error}[/yellow]")
            if auto_confirm or bridge.confirm_choice(
                f"Create empty '{requirements_file}' file?", default=False
            ):
                Path(requirements_file).touch()
                bridge.display_result(
                    f"[green]Created empty file: {requirements_file}[/green]"
                )
            else:
                return

        # Define subtasks for the specification generation process
        subtasks = [
            {"name": "Analyzing requirements", "total": 30},
            {"name": "Extracting key concepts", "total": 20},
            {"name": "Generating specifications", "total": 40},
            {"name": "Validating output", "total": 10},
        ]

        # Create a function to run with progress tracking
        def generate_specs_with_progress():
            # Create progress indicator for the main task
            progress = create_enhanced_progress(
                console, "Generating specifications", 100
            )

            try:
                # Add subtasks
                for subtask in subtasks:
                    progress.add_subtask(subtask["name"], subtask["total"])

                # Update progress for first subtask
                progress.update_subtask(
                    "Analyzing requirements",
                    advance=15,
                    description="Parsing requirements file",
                )

                # Generate specifications
                args = filter_args({"requirements_file": requirements_file})

                # Update progress for first subtask completion
                progress.update_subtask("Analyzing requirements", advance=15)
                progress.complete_subtask("Analyzing requirements")

                # Update progress for second subtask
                progress.update_subtask("Extracting key concepts", advance=20)
                progress.complete_subtask("Extracting key concepts")

                # Update progress for third subtask
                progress.update_subtask(
                    "Generating specifications",
                    advance=20,
                    description="Creating specification structure",
                )
                progress.update_subtask(
                    "Generating specifications",
                    advance=20,
                    description="Writing specification details",
                )

                # Call the actual generate_specs function
                result = generate_specs(**args)

                # Update progress for remaining subtasks
                progress.complete_subtask("Generating specifications")
                progress.update_subtask("Validating output", advance=10)
                progress.complete_subtask("Validating output")

                # Update main task progress
                progress.update(advance=100)

                return result
            finally:
                # Ensure progress is completed even if an error occurs
                progress.complete()

        # Run the specification generation with progress tracking
        result = generate_specs_with_progress()

        # Handle result
        if result.get("success"):
            output_file = result.get("output_file", "specs.md")

            # Create a summary table of what was generated
            from rich.table import Table

            summary_table = Table(title="Specification Generation Summary")
            summary_table.add_column("Item", style="cyan")
            summary_table.add_column("Value", style="green")

            summary_table.add_row("Input File", requirements_file)
            summary_table.add_row("Output File", output_file)
            if "stats" in result:
                stats = result["stats"]
                for key, value in stats.items():
                    summary_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(summary_table)

            bridge.display_result(
                f"[green]Specifications successfully generated from {requirements_file}.[/green]",
                highlight=True,
            )

            # Show next steps
            bridge.display_result("\n[bold]Next Steps:[/bold]")
            bridge.display_result(
                f"1. Review the generated specifications in {output_file}"
            )
            bridge.display_result("2. Generate tests: devsynth test")
            bridge.display_result("3. Generate code: devsynth code")
        else:
            _handle_error(bridge, result)
    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)


__all__ = ["spec_cmd"]
