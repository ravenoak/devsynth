"""Generate specifications from a requirements file."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console

from devsynth.core.workflows import filter_args, generate_specs
from devsynth.interface.ux_bridge import UXBridge

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
    auto_confirm: bool | None = None,
    bridge: UXBridge | None = None,
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

        # Simple progress indicator with four logical steps
        steps = [
            "Analyzing requirements",
            "Generating specifications",
            "Validating output",
            "Finishing",
        ]
        progress = bridge.create_progress("Generating specifications", total=len(steps))

        try:
            progress.update(description=steps[0])
            args = filter_args({"requirements_file": requirements_file})

            progress.update(description=steps[1])
            result = generate_specs(**args)

            progress.update(description=steps[2])

            progress.update(description=steps[3])
        finally:
            progress.complete()

        # Handle result
        result = result if isinstance(result, dict) else {}

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
