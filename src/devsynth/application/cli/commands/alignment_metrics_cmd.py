"""
Command handler for the 'alignment-metrics' command.

This module provides functionality to collect and report on alignment metrics.
"""

import datetime
import json
import os
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table

from devsynth.application.cli.commands.align_cmd import (
    CODE_FILES,
    REQ_REF_PATTERN,
    REQUIREMENT_FILES,
    SPEC_REF_PATTERN,
    SPECIFICATION_FILES,
    TEST_FILES,
    TEST_REF_PATTERN,
    extract_references,
    get_all_files,
    is_file_of_type,
)
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Console for rich output
bridge: UXBridge = CLIUXBridge()
console = Console()


def calculate_alignment_coverage(files: list[str]) -> dict:
    """Calculate alignment coverage metrics."""
    metrics = {
        "total_files": len(files),
        "requirement_files": 0,
        "specification_files": 0,
        "test_files": 0,
        "code_files": 0,
        "requirements_with_specs": 0,
        "total_requirements": 0,
        "specs_with_tests": 0,
        "total_specs": 0,
        "tests_with_code": 0,
        "total_tests": 0,
        "code_with_tests": 0,
        "total_code_files": 0,
    }

    # Count files by type
    for file in files:
        if is_file_of_type(file, REQUIREMENT_FILES):
            metrics["requirement_files"] += 1
        elif is_file_of_type(file, SPECIFICATION_FILES):
            metrics["specification_files"] += 1
        elif is_file_of_type(file, TEST_FILES):
            metrics["test_files"] += 1
        elif is_file_of_type(file, CODE_FILES) and file.endswith(".py"):
            metrics["code_files"] += 1

    # Extract all requirements, specifications, and tests
    all_requirements = set()
    all_specifications = set()
    all_tests = set()

    for file in files:
        if is_file_of_type(file, REQUIREMENT_FILES):
            all_requirements.update(extract_references(file, REQ_REF_PATTERN))
        elif is_file_of_type(file, SPECIFICATION_FILES):
            all_specifications.update(extract_references(file, SPEC_REF_PATTERN))
        elif is_file_of_type(file, TEST_FILES):
            all_tests.update(extract_references(file, TEST_REF_PATTERN))

    metrics["total_requirements"] = len(all_requirements)
    metrics["total_specs"] = len(all_specifications)
    metrics["total_tests"] = len(all_tests)
    metrics["total_code_files"] = len(
        [f for f in files if is_file_of_type(f, CODE_FILES) and f.endswith(".py")]
    )

    # Check requirements with specifications
    requirements_with_specs = set()
    for file in files:
        if is_file_of_type(file, SPECIFICATION_FILES):
            spec_requirements = extract_references(file, REQ_REF_PATTERN)
            requirements_with_specs.update(spec_requirements)

    metrics["requirements_with_specs"] = len(requirements_with_specs)

    # Check specifications with tests
    specs_with_tests = set()
    for file in files:
        if is_file_of_type(file, TEST_FILES):
            test_specifications = extract_references(file, SPEC_REF_PATTERN)
            specs_with_tests.update(test_specifications)

    metrics["specs_with_tests"] = len(specs_with_tests)

    # Check tests with code
    tests_with_code = set()
    code_with_tests = 0
    for file in files:
        if is_file_of_type(file, CODE_FILES) and file.endswith(".py"):
            code_tests = extract_references(file, TEST_REF_PATTERN)
            tests_with_code.update(code_tests)
            if code_tests:
                code_with_tests += 1

    metrics["tests_with_code"] = len(tests_with_code)
    metrics["code_with_tests"] = code_with_tests

    # Calculate coverage percentages
    if metrics["total_requirements"] > 0:
        metrics["requirements_coverage"] = (
            metrics["requirements_with_specs"] / metrics["total_requirements"]
        ) * 100
    else:
        metrics["requirements_coverage"] = 0

    if metrics["total_specs"] > 0:
        metrics["specs_coverage"] = (
            metrics["specs_with_tests"] / metrics["total_specs"]
        ) * 100
    else:
        metrics["specs_coverage"] = 0

    if metrics["total_tests"] > 0:
        metrics["tests_coverage"] = (
            metrics["tests_with_code"] / metrics["total_tests"]
        ) * 100
    else:
        metrics["tests_coverage"] = 0

    if metrics["total_code_files"] > 0:
        metrics["code_coverage"] = (
            metrics["code_with_tests"] / metrics["total_code_files"]
        ) * 100
    else:
        metrics["code_coverage"] = 0

    # Calculate overall coverage
    metrics["overall_coverage"] = (
        metrics["requirements_coverage"]
        + metrics["specs_coverage"]
        + metrics["tests_coverage"]
        + metrics["code_coverage"]
    ) / 4

    return metrics


def calculate_alignment_issues(files: list[str]) -> dict:
    """Calculate alignment issues metrics."""
    from devsynth.application.cli.commands.align_cmd import (
        check_requirement_references,
        check_specification_references,
        check_terminology_consistency,
        check_test_references,
    )

    # Run checks
    requirement_issues = check_requirement_references(files)
    specification_issues = check_specification_references(files)
    test_issues = check_test_references(files)
    terminology_issues = check_terminology_consistency(files)

    # Count issues by severity
    # For simplicity, we'll consider all requirement and specification issues as high severity,
    # test issues as medium severity, and terminology issues as low severity
    high_severity = len(requirement_issues) + len(specification_issues)
    medium_severity = len(test_issues)
    low_severity = len(terminology_issues)

    return {
        "total_issues": high_severity + medium_severity + low_severity,
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "low_severity": low_severity,
        "requirement_issues": len(requirement_issues),
        "specification_issues": len(specification_issues),
        "test_issues": len(test_issues),
        "terminology_issues": len(terminology_issues),
    }


def load_historical_metrics(metrics_file: str) -> list[dict]:
    """Load historical metrics from a file."""
    try:
        if os.path.exists(metrics_file):
            with open(metrics_file, encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading historical metrics: {e}")
        return []


def save_metrics(metrics: dict, metrics_file: str, historical_metrics: list[dict]):
    """Save metrics to a file."""
    try:
        # Add timestamp to metrics
        metrics["timestamp"] = datetime.datetime.now().isoformat()

        # Add metrics to historical data
        historical_metrics.append(metrics)

        # Save to file
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(historical_metrics, f, indent=2)

        logger.info(f"Metrics saved to {metrics_file}")
    except Exception as e:
        logger.error(f"Error saving metrics: {e}")


def display_metrics(
    metrics: dict,
    historical_metrics: list[dict],
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Display alignment metrics."""
    bridge.print("\n[bold]Alignment Metrics[/bold]\n")

    # Coverage metrics
    coverage_table = Table(title="Alignment Coverage")
    coverage_table.add_column("Metric", style="cyan")
    coverage_table.add_column("Value", style="green")
    coverage_table.add_column("Coverage", style="yellow")

    coverage_table.add_row(
        "Requirements with Specifications",
        f"{metrics['requirements_with_specs']} / {metrics['total_requirements']}",
        f"{metrics['requirements_coverage']:.1f}%",
    )
    coverage_table.add_row(
        "Specifications with Tests",
        f"{metrics['specs_with_tests']} / {metrics['total_specs']}",
        f"{metrics['specs_coverage']:.1f}%",
    )
    coverage_table.add_row(
        "Tests with Code",
        f"{metrics['tests_with_code']} / {metrics['total_tests']}",
        f"{metrics['tests_coverage']:.1f}%",
    )
    coverage_table.add_row(
        "Code with Tests",
        f"{metrics['code_with_tests']} / {metrics['total_code_files']}",
        f"{metrics['code_coverage']:.1f}%",
    )
    coverage_table.add_row(
        "Overall Coverage", "", f"{metrics['overall_coverage']:.1f}%"
    )

    bridge.print(coverage_table)

    # Issues metrics
    issues_table = Table(title="Alignment Issues")
    issues_table.add_column("Severity", style="cyan")
    issues_table.add_column("Count", style="green")

    issues_table.add_row("High", str(metrics["high_severity"]))
    issues_table.add_row("Medium", str(metrics["medium_severity"]))
    issues_table.add_row("Low", str(metrics["low_severity"]))
    issues_table.add_row("Total", str(metrics["total_issues"]))

    bridge.print(issues_table)

    # Trend analysis
    if len(historical_metrics) > 1:
        bridge.print("\n[bold]Trend Analysis[/bold]\n")

        # Get previous metrics
        previous_metrics = historical_metrics[-2]

        # Calculate changes
        coverage_change = (
            metrics["overall_coverage"] - previous_metrics["overall_coverage"]
        )
        issues_change = previous_metrics["total_issues"] - metrics["total_issues"]

        # Display changes
        if coverage_change > 0:
            bridge.print(f"[green]Coverage increased by {coverage_change:.1f}%[/green]")
        elif coverage_change < 0:
            bridge.print(
                f"[red]Coverage decreased by {abs(coverage_change):.1f}%[/red]"
            )
        else:
            bridge.print(f"[yellow]Coverage unchanged[/yellow]")

        if issues_change > 0:
            bridge.print(f"[green]Issues decreased by {issues_change}[/green]")
        elif issues_change < 0:
            bridge.print(f"[red]Issues increased by {abs(issues_change)}[/red]")
        else:
            bridge.print(f"[yellow]Issues unchanged[/yellow]")


def generate_metrics_report(
    metrics: dict,
    historical_metrics: list[dict],
    output_file: str,
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Generate a metrics report in Markdown format."""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Alignment Metrics Report\n\n")
            f.write(
                f"**Generated**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            # Coverage metrics
            f.write("## Alignment Coverage\n\n")
            f.write("| Metric | Value | Coverage |\n")
            f.write("|--------|-------|----------|\n")
            f.write(
                f"| Requirements with Specifications | {metrics['requirements_with_specs']} / {metrics['total_requirements']} | {metrics['requirements_coverage']:.1f}% |\n"
            )
            f.write(
                f"| Specifications with Tests | {metrics['specs_with_tests']} / {metrics['total_specs']} | {metrics['specs_coverage']:.1f}% |\n"
            )
            f.write(
                f"| Tests with Code | {metrics['tests_with_code']} / {metrics['total_tests']} | {metrics['tests_coverage']:.1f}% |\n"
            )
            f.write(
                f"| Code with Tests | {metrics['code_with_tests']} / {metrics['total_code_files']} | {metrics['code_coverage']:.1f}% |\n"
            )
            f.write(f"| Overall Coverage | | {metrics['overall_coverage']:.1f}% |\n\n")

            # Issues metrics
            f.write("## Alignment Issues\n\n")
            f.write("| Severity | Count |\n")
            f.write("|----------|-------|\n")
            f.write(f"| High | {metrics['high_severity']} |\n")
            f.write(f"| Medium | {metrics['medium_severity']} |\n")
            f.write(f"| Low | {metrics['low_severity']} |\n")
            f.write(f"| Total | {metrics['total_issues']} |\n\n")

            # Trend analysis
            if len(historical_metrics) > 1:
                f.write("## Trend Analysis\n\n")

                # Get previous metrics
                previous_metrics = historical_metrics[-2]

                # Calculate changes
                coverage_change = (
                    metrics["overall_coverage"] - previous_metrics["overall_coverage"]
                )
                issues_change = (
                    previous_metrics["total_issues"] - metrics["total_issues"]
                )

                # Display changes
                if coverage_change > 0:
                    f.write(f"- Coverage increased by {coverage_change:.1f}%\n")
                elif coverage_change < 0:
                    f.write(f"- Coverage decreased by {abs(coverage_change):.1f}%\n")
                else:
                    f.write(f"- Coverage unchanged\n")

                if issues_change > 0:
                    f.write(f"- Issues decreased by {issues_change}\n")
                elif issues_change < 0:
                    f.write(f"- Issues increased by {abs(issues_change)}\n")
                else:
                    f.write(f"- Issues unchanged\n")

        bridge.print(f"[green]Metrics report saved to {output_file}[/green]")
    except Exception as e:
        logger.error(f"Error generating metrics report: {e}")
        bridge.print(f"[red]Error generating metrics report: {e}[/red]")


def alignment_metrics_cmd(
    path: str = ".",
    metrics_file: str = ".devsynth/alignment_metrics.json",
    output: str | None = None,
    *,
    bridge: UXBridge | None = None,
) -> bool:
    """Collect and report on alignment metrics.

    Example:
        `devsynth alignment-metrics --path .`

    Args:
        path: Path to the project directory
        metrics_file: Path to the metrics file
        output: Path to output file for metrics report
    """
    ux_bridge = bridge or globals()["bridge"]
    try:
        ux_bridge.print("[bold]Collecting alignment metrics...[/bold]")

        # Ensure metrics directory exists
        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)

        # Get all files
        files = get_all_files(path)

        # Only check files that exist
        existing_files = [f for f in files if os.path.isfile(f)]

        # Calculate metrics
        with ux_bridge.create_progress("Calculating metrics...", total=2) as progress:
            coverage_metrics = calculate_alignment_coverage(existing_files)
            progress.update(advance=1, description="Calculating issues metrics...")
            issues_metrics = calculate_alignment_issues(existing_files)
            progress.update(advance=1)

        # Combine metrics
        metrics = {**coverage_metrics, **issues_metrics}

        # Load historical metrics
        historical_metrics = load_historical_metrics(metrics_file)

        # Save metrics
        save_metrics(metrics, metrics_file, historical_metrics)

        # Display metrics
        display_metrics(metrics, historical_metrics, bridge=ux_bridge)

        # Generate report if output file specified
        if output:
            generate_metrics_report(
                metrics, historical_metrics, output, bridge=ux_bridge
            )

        return True

    except Exception as e:
        logger.error(f"Error collecting alignment metrics: {e}")
        ux_bridge.print(f"[red]Error collecting alignment metrics: {e}[/red]")
        return False
