"""Generate tests based on specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from devsynth.core.workflows import filter_args, generate_tests
from devsynth.interface.ux_bridge import UXBridge

from ..progress import create_enhanced_progress
from ..utils import (
    _check_services,
    _env_flag,
    _handle_error,
    _resolve_bridge,
    _validate_file_path,
)
from .spec_cmd import spec_cmd


def test_cmd(
    spec_file: str = "specs.md",
    *,
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Generate tests based on specifications.

    This command analyzes a specifications file and generates test cases
    that can be used to validate the implementation.

    Args:
        spec_file: Path to the specifications file (Markdown format)
        bridge: Optional UX bridge for interaction

    Examples:
        Generate tests from the default specifications file:
        ```
        devsynth test
        ```

        Generate tests from a custom specifications file:
        ```
        devsynth test --spec-file custom_specs.md
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
        error = _validate_file_path(spec_file)
        if error:
            bridge.display_result(f"[yellow]{error}[/yellow]")
            if auto_confirm or bridge.confirm_choice(
                f"Run 'devsynth spec' to generate {spec_file}?", default=True
            ):
                spec_cmd(bridge=bridge, auto_confirm=auto_confirm)
            else:
                return

        # Define subtasks for the test generation process
        subtasks = [
            {"name": "Analyzing specifications", "total": 25},
            {"name": "Identifying test cases", "total": 25},
            {"name": "Generating unit tests", "total": 20},
            {"name": "Generating integration tests", "total": 15},
            {"name": "Generating behavior tests", "total": 15},
        ]

        # Create a function to run with progress tracking
        def generate_tests_with_progress():
            # Create progress indicator for the main task
            progress = create_enhanced_progress(console, "Generating tests", 100)

            try:
                # Add subtasks
                for subtask in subtasks:
                    progress.add_subtask(subtask["name"], subtask["total"])

                # Update progress for first subtask
                progress.update_subtask(
                    "Analyzing specifications",
                    advance=15,
                    description="Parsing specification file",
                )

                # Generate tests
                args = filter_args({"spec_file": spec_file})

                # Update progress for first subtask completion
                progress.update_subtask("Analyzing specifications", advance=10)
                progress.complete_subtask("Analyzing specifications")

                # Update progress for second subtask
                progress.update_subtask(
                    "Identifying test cases",
                    advance=15,
                    description="Extracting testable requirements",
                )
                progress.update_subtask(
                    "Identifying test cases",
                    advance=10,
                    description="Defining test boundaries",
                )
                progress.complete_subtask("Identifying test cases")

                # Update progress for remaining subtasks
                progress.update_subtask("Generating unit tests", advance=20)
                progress.complete_subtask("Generating unit tests")

                progress.update_subtask("Generating integration tests", advance=15)
                progress.complete_subtask("Generating integration tests")

                progress.update_subtask("Generating behavior tests", advance=15)
                progress.complete_subtask("Generating behavior tests")

                # Call the actual generate_tests function
                result = generate_tests(**args)

                # Update main task progress
                progress.update(advance=100)

                return result
            finally:
                # Ensure progress is completed even if an error occurs
                progress.complete()

        # Run the test generation with progress tracking
        result = generate_tests_with_progress()

        # Handle result
        if result.get("success"):
            output_dir = result.get("output_dir", "tests")

            # Create a summary table of what was generated
            summary_table = Table(title="Test Generation Summary")
            summary_table.add_column("Test Type", style="cyan")
            summary_table.add_column("Location", style="blue")

            # Add rows for each test type
            test_types = {
                "Unit Tests": f"{output_dir}/unit",
                "Integration Tests": f"{output_dir}/integration",
                "Behavior Tests": f"{output_dir}/behavior",
            }

            for test_type, location in test_types.items():
                summary_table.add_row(test_type, location)

            console.print(summary_table)

            bridge.display_result(
                f"[green]Tests successfully generated from {spec_file}.[/green]",
                highlight=True,
            )

            # Show next steps
            bridge.display_result("\n[bold]Next Steps:[/bold]")
            bridge.display_result("1. Review the generated tests")
            bridge.display_result("2. Generate code: devsynth code")
            bridge.display_result("3. Run tests: devsynth run-pipeline")
        else:
            _handle_error(bridge, result)
    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)


__all__ = ["test_cmd"]
