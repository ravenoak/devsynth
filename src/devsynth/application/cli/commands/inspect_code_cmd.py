"""
Command to inspect a codebase and provide insights about its architecture, structure, and quality.

NOTE (mypy override): This module currently has relaxed mypy settings per
pyproject.toml [tool.mypy.overrides] to allow incremental stabilization.
TODO(typing): Restore disallow_untyped_defs and check_untyped_defs after
refining public API types and internal helpers. Target: 2025-10-01. See docs/tasks.md (Static analysis).
"""

import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devsynth.application.code_analysis.project_state_analyzer import (
    ProjectStateAnalyzer,
)
from devsynth.application.code_analysis.self_analyzer import SelfAnalyzer
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge, sanitize_output
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
cli_bridge: UXBridge = CLIUXBridge()


def inspect_code_cmd(
    path: Optional[str] = None,
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Inspect a codebase to understand its architecture and quality.

    Example:
        `devsynth inspect-code --path ./my-project`

    Args:
        path: Path to the codebase to inspect (default: current directory)
        bridge: Optional UXBridge for user feedback
    """
    bridge = bridge or cli_bridge
    console = Console()

    try:
        # Show a welcome message for the inspect-code command
        console.print(
            Panel(
                "[bold blue]DevSynth Code Inspection[/bold blue]\n\n"
                "This command will inspect a codebase and provide insights about its architecture, structure, and quality.",
                title="Code Inspection",
                border_style="blue",
            )
        )

        # Determine the path to inspect
        if path is None:
            path = os.getcwd()
        else:
            path = os.path.abspath(path)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

        console.print(f"[bold]Inspecting codebase at:[/bold] {sanitize_output(path)}")

        # Create a progress panel
        analysis_failed = False
        with console.status("[bold green]Inspecting codebase...[/bold green]"):
            try:
                analyzer = SelfAnalyzer(path)
                result = analyzer.analyze()
                # Detect per-file analysis errors and surface as a user-visible error
                files = result.get("code_analysis", {}).get("files", {})
                error_files = [
                    fp for fp, fa in files.items() if fa.get("metrics", {}).get("error")
                ]
                if error_files:
                    analysis_failed = True
                    msg = f"Detected analysis errors in {len(error_files)} file(s)."
                    logger.error(msg)
                    console.print(
                        f"[red]Error analyzing codebase: {sanitize_output(msg)}[/red]"
                    )
            except Exception as e:
                analysis_failed = True
                logger.error(f"Self analysis failed: {e}")
                console.print(
                    f"[red]Error analyzing codebase: {sanitize_output(str(e))}[/red]"
                )
                result = {
                    "insights": {
                        "architecture": {
                            "type": "unknown",
                            "confidence": 0.0,
                            "layers": {},
                            "architecture_violations": [],
                        },
                        "code_quality": {
                            "total_files": 0,
                            "total_classes": 0,
                            "total_functions": 0,
                            "docstring_coverage": {
                                "files": 0.0,
                                "classes": 0.0,
                                "functions": 0.0,
                            },
                        },
                        "test_coverage": {
                            "total_symbols": 0,
                            "tested_symbols": 0,
                            "coverage_percentage": 0.0,
                        },
                        "improvement_opportunities": [],
                    }
                }
            try:
                project_analyzer = ProjectStateAnalyzer(path)
                project_state = project_analyzer.analyze()
            except Exception as e:
                analysis_failed = True
                logger.error(f"Project state analysis failed: {e}")
                console.print(
                    f"[red]Error analyzing project state: {sanitize_output(str(e))}[/red]"
                )
                project_state = {}

        # Display the analysis results
        console.print("\n[bold]Inspection Results:[/bold]")

        # Display architecture information
        architecture = result["insights"]["architecture"]
        console.print(
            f"\n[bold]Architecture:[/bold] {sanitize_output(str(architecture['type']))} (confidence: {architecture['confidence']:.2f})"
        )

        # Display layers
        layers = architecture["layers"]
        if layers:
            console.print("\n[bold]Layers:[/bold]")
            layers_table = Table(show_header=True, header_style="bold")
            layers_table.add_column("Layer")
            layers_table.add_column("Components")

            for layer, components in layers.items():
                safe_layer = sanitize_output(str(layer))
                safe_components = (
                    ", ".join(sanitize_output(str(c)) for c in components)
                    if components
                    else "None"
                )
                layers_table.add_row(safe_layer, safe_components)

            console.print(layers_table)

        # Display architecture violations
        violations = architecture["architecture_violations"]
        if violations:
            console.print("\n[bold]Architecture Violations:[/bold]")
            violations_table = Table(show_header=True, header_style="bold")
            violations_table.add_column("Source Layer")
            violations_table.add_column("Target Layer")
            violations_table.add_column("Description")

            for violation in violations:
                violations_table.add_row(
                    sanitize_output(str(violation["source_layer"])),
                    sanitize_output(str(violation["target_layer"])),
                    sanitize_output(str(violation["description"])),
                )

            console.print(violations_table)

        # Display code quality metrics
        code_quality = result["insights"]["code_quality"]
        console.print("\n[bold]Code Quality Metrics:[/bold]")
        quality_table = Table(show_header=True, header_style="bold")
        quality_table.add_column("Metric")
        quality_table.add_column("Value")

        quality_table.add_row(
            "Total Files", sanitize_output(str(code_quality["total_files"]))
        )
        quality_table.add_row(
            "Total Classes", sanitize_output(str(code_quality["total_classes"]))
        )
        quality_table.add_row(
            "Total Functions", sanitize_output(str(code_quality["total_functions"]))
        )
        quality_table.add_row(
            "Docstring Coverage (Files)",
            sanitize_output(
                f"{code_quality['docstring_coverage']['files'] * 100:.1f}%"
            ),
        )
        quality_table.add_row(
            "Docstring Coverage (Classes)",
            sanitize_output(
                f"{code_quality['docstring_coverage']['classes'] * 100:.1f}%"
            ),
        )
        quality_table.add_row(
            "Docstring Coverage (Functions)",
            sanitize_output(
                f"{code_quality['docstring_coverage']['functions'] * 100:.1f}%"
            ),
        )

        console.print(quality_table)

        # Display test coverage
        test_coverage = result["insights"]["test_coverage"]
        console.print("\n[bold]Test Coverage:[/bold]")
        coverage_table = Table(show_header=True, header_style="bold")
        coverage_table.add_column("Metric")
        coverage_table.add_column("Value")

        coverage_table.add_row(
            "Total Symbols", sanitize_output(str(test_coverage["total_symbols"]))
        )
        coverage_table.add_row(
            "Tested Symbols", sanitize_output(str(test_coverage["tested_symbols"]))
        )
        coverage_table.add_row(
            "Coverage Percentage",
            sanitize_output(f"{test_coverage['coverage_percentage'] * 100:.1f}%"),
        )

        console.print(coverage_table)

        # Display project health score
        health_score = project_state.get("health_score", 0.0)
        console.print(
            f"\n[bold]Project Health Score:[/bold] {sanitize_output(f'{health_score:.2f}')}/10.0"
        )

        # Display improvement opportunities
        opportunities = result["insights"]["improvement_opportunities"]
        if opportunities:
            console.print("\n[bold]Improvement Opportunities:[/bold]")
            opportunities_table = Table(show_header=True, header_style="bold")
            opportunities_table.add_column("Priority")
            opportunities_table.add_column("Type")
            opportunities_table.add_column("Description")

            for opportunity in opportunities:
                opportunities_table.add_row(
                    sanitize_output(str(opportunity.get("priority", "")).upper()),
                    sanitize_output(str(opportunity.get("type", ""))),
                    sanitize_output(str(opportunity.get("description", ""))),
                )

            console.print(opportunities_table)

        # Display recommendations
        if "recommendations" in project_state:
            console.print("\n[bold]Recommendations:[/bold]")
            for recommendation in project_state["recommendations"]:
                console.print(f"- {sanitize_output(str(recommendation))}")

        if not analysis_failed:
            console.print("\n[green]Inspection completed successfully![/green]")

    except Exception as e:
        logger.error(f"Error analyzing codebase: {str(e)}")
        console.print(f"[red]Error analyzing codebase: {sanitize_output(str(e))}[/red]")
