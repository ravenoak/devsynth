"""
Command to analyze test-first development metrics.

This command analyzes the commit history to determine if the project
follows test-first development practices, and generates metrics and reports.
"""

import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytest
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


@pytest.mark.medium
def test_metrics_cmd(
    days: int = 30,
    output_file: str | None = None,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Analyze test-first development metrics.

    Example:
        `devsynth test-metrics --days 14`

    Args:
        days: Number of days of commit history to analyze (default: 30)
        output_file: Path to output file for metrics report (default: None, prints to console)
    """
    console = Console()
    bridge = bridge or globals()["bridge"]

    try:
        # Show a welcome message for the test-metrics command
        bridge.print(
            Panel(
                "[bold blue]DevSynth Test-First Metrics[/bold blue]\n\n"
                "This command analyzes the commit history to determine if the project "
                "follows test-first development practices, and generates metrics and reports.",
                title="Test-First Metrics",
                border_style="blue",
            )
        )

        bridge.print(
            f"[bold]Analyzing commit history for the last {days} days...[/bold]"
        )

        # Get commit history
        with console.status("[bold green]Retrieving commit history...[/bold green]"):
            commits = get_commit_history(days)

        if not commits:
            bridge.print(
                "[yellow]No commits found in the specified time period.[/yellow]"
            )
            return

        bridge.print(f"[bold]Found {len(commits)} commits to analyze.[/bold]")

        # Analyze commits
        with console.status("[bold green]Analyzing commits...[/bold green]"):
            metrics = calculate_metrics(commits)

        # Generate report
        report = generate_metrics_report(metrics)

        # Output report
        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            bridge.print(f"[green]Metrics report written to {output_file}[/green]")
        else:
            bridge.print("\n[bold]Test-First Development Metrics:[/bold]")
            bridge.print(Markdown(report))

        # Display summary
        test_first_ratio = metrics["test_first_ratio"]
        bridge.print(f"\n[bold]Summary:[/bold]")
        bridge.print(f"Total commits analyzed: {metrics['total_commits']}")
        bridge.print(
            f"Test-first commits: {metrics['test_first_commits']} ({test_first_ratio:.1%})"
        )
        bridge.print(
            f"Code-first commits: {metrics['code_first_commits']} ({1 - test_first_ratio:.1%})"
        )

        # Provide recommendations
        if test_first_ratio >= 0.8:
            bridge.print(
                "\n[bold green]✓ Excellent test-first development practices![/bold green]"
            )
            bridge.print(
                "The project follows test-first development practices very well."
            )
        elif test_first_ratio >= 0.6:
            bridge.print(
                "\n[bold green]✓ Good test-first development practices.[/bold green]"
            )
            bridge.print(
                "The project generally follows test-first development, but there's room for improvement."
            )
        elif test_first_ratio >= 0.4:
            bridge.print(
                "\n[bold yellow]⚠ Moderate test-first development practices.[/bold yellow]"
            )
            bridge.print(
                "The project sometimes follows test-first development, but should improve consistency."
            )
        else:
            bridge.print(
                "\n[bold red]✗ Poor test-first development practices.[/bold red]"
            )
            bridge.print(
                "The project rarely follows test-first development. Consider adopting TDD/BDD practices."
            )

    except Exception as err:
        bridge.print(f"[red]Error:[/red] {err}", highlight=False)


def get_commit_history(days: int = 30) -> list[dict[str, Any]]:
    """
    Get the commit history for the specified number of days.

    Args:
        days: Number of days of history to retrieve

    Returns:
        A list of commit dictionaries
    """
    # Construct the git log command
    cmd = [
        "git",
        "log",
        f"--since={days} days ago",
        "--pretty=format:%H%n%an%n%at%n%s%n%b%n--END--",
        "--name-status",
    ]

    try:
        # Run the git command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        # Parse the output
        commits = []
        current_commit = None

        for line in output.split("\n"):
            if line == "--END--":
                if current_commit:
                    commits.append(current_commit)
                    current_commit = None
            elif current_commit is None:
                # Start a new commit
                current_commit = {"hash": line, "files": []}
            elif "author" not in current_commit:
                current_commit["author"] = line
            elif "timestamp" not in current_commit:
                current_commit["timestamp"] = int(line)
                current_commit["date"] = datetime.fromtimestamp(int(line)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            elif "subject" not in current_commit:
                current_commit["subject"] = line
            elif line.startswith(("A", "M", "D", "R")):
                # This is a file status line
                status, *file_path = line.split("\t")
                if file_path:
                    current_commit["files"].append(
                        {"status": status, "path": file_path[0]}
                    )

        # Add the last commit if it exists
        if current_commit:
            commits.append(current_commit)

        return commits

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git command: {e}")
        return []


def analyze_commit(commit: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze a commit to determine if it follows test-first development.

    Args:
        commit: The commit dictionary

    Returns:
        A dictionary with analysis results
    """
    result = {
        "hash": commit["hash"],
        "date": commit["date"],
        "subject": commit["subject"],
        "test_files": [],
        "code_files": [],
        "is_test_first": False,
        "is_code_first": False,
        "is_mixed": False,
    }

    # Categorize files
    for file in commit["files"]:
        path = file["path"]
        if path.endswith(
            (
                ".py",
                ".js",
                ".ts",
                ".java",
                ".rb",
                ".go",
                ".rs",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
            )
        ):
            if (
                "test" in path.lower()
                or "spec" in path.lower()
                or path.startswith("tests/")
            ):
                result["test_files"].append(path)
            else:
                result["code_files"].append(path)

    # Determine if the commit is test-first, code-first, or mixed
    has_tests = len(result["test_files"]) > 0
    has_code = len(result["code_files"]) > 0

    if has_tests and has_code:
        # If the commit message indicates test-first development
        subject_lower = result["subject"].lower()
        if any(
            term in subject_lower
            for term in ["test first", "tdd", "bdd", "test-driven", "behavior-driven"]
        ):
            result["is_test_first"] = True
        else:
            result["is_mixed"] = True
    elif has_tests and not has_code:
        result["is_test_first"] = True
    elif has_code and not has_tests:
        result["is_code_first"] = True

    return result


def calculate_metrics(commits: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate metrics based on commit analysis.

    Args:
        commits: List of commit dictionaries

    Returns:
        A dictionary with metrics
    """
    # Analyze each commit
    analyzed_commits = [analyze_commit(commit) for commit in commits]

    # Initialize metrics
    metrics = {
        "total_commits": len(analyzed_commits),
        "test_first_commits": 0,
        "code_first_commits": 0,
        "mixed_commits": 0,
        "test_first_ratio": 0.0,
        "code_first_ratio": 0.0,
        "mixed_ratio": 0.0,
        "test_files_count": 0,
        "code_files_count": 0,
        "test_to_code_ratio": 0.0,
        "commits_by_date": {},
        "test_first_by_date": {},
        "code_first_by_date": {},
        "mixed_by_date": {},
        "recent_test_first_commits": [],
        "recent_code_first_commits": [],
    }

    # Count commit types
    for commit in analyzed_commits:
        if commit["is_test_first"]:
            metrics["test_first_commits"] += 1
        elif commit["is_code_first"]:
            metrics["code_first_commits"] += 1
        elif commit["is_mixed"]:
            metrics["mixed_commits"] += 1

        # Count files
        metrics["test_files_count"] += len(commit["test_files"])
        metrics["code_files_count"] += len(commit["code_files"])

        # Group by date
        date = commit["date"].split()[0]  # Just the date part
        metrics["commits_by_date"][date] = metrics["commits_by_date"].get(date, 0) + 1

        if commit["is_test_first"]:
            metrics["test_first_by_date"][date] = (
                metrics["test_first_by_date"].get(date, 0) + 1
            )
        elif commit["is_code_first"]:
            metrics["code_first_by_date"][date] = (
                metrics["code_first_by_date"].get(date, 0) + 1
            )
        elif commit["is_mixed"]:
            metrics["mixed_by_date"][date] = metrics["mixed_by_date"].get(date, 0) + 1

    # Calculate ratios
    if metrics["total_commits"] > 0:
        metrics["test_first_ratio"] = (
            metrics["test_first_commits"] / metrics["total_commits"]
        )
        metrics["code_first_ratio"] = (
            metrics["code_first_commits"] / metrics["total_commits"]
        )
        metrics["mixed_ratio"] = metrics["mixed_commits"] / metrics["total_commits"]

    if metrics["code_files_count"] > 0:
        metrics["test_to_code_ratio"] = (
            metrics["test_files_count"] / metrics["code_files_count"]
        )

    # Get recent commits of each type (up to 5)
    metrics["recent_test_first_commits"] = [
        commit for commit in analyzed_commits if commit["is_test_first"]
    ][:5]

    metrics["recent_code_first_commits"] = [
        commit for commit in analyzed_commits if commit["is_code_first"]
    ][:5]

    return metrics


def generate_metrics_report(metrics: dict[str, Any]) -> str:
    """
    Generate a Markdown report of the metrics.

    Args:
        metrics: The metrics dictionary

    Returns:
        A Markdown string with the report
    """
    report = [
        "# Test-First Development Metrics Report",
        "",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- **Total Commits Analyzed**: {metrics['total_commits']}",
        f"- **Test-First Commits**: {metrics['test_first_commits']} ({metrics['test_first_ratio']:.1%})",
        f"- **Code-First Commits**: {metrics['code_first_commits']} ({metrics['code_first_ratio']:.1%})",
        f"- **Mixed Commits**: {metrics['mixed_commits']} ({metrics['mixed_ratio']:.1%})",
        f"- **Test Files**: {metrics['test_files_count']}",
        f"- **Code Files**: {metrics['code_files_count']}",
        f"- **Test-to-Code Ratio**: {metrics['test_to_code_ratio']:.2f}",
        "",
        "## Recommendations",
        "",
    ]

    # Add recommendations based on metrics
    test_first_ratio = metrics["test_first_ratio"]
    if test_first_ratio >= 0.8:
        report.append("✅ **Excellent test-first development practices!**")
        report.append("The project follows test-first development practices very well.")
    elif test_first_ratio >= 0.6:
        report.append("✅ **Good test-first development practices.**")
        report.append(
            "The project generally follows test-first development, but there's room for improvement."
        )
    elif test_first_ratio >= 0.4:
        report.append("⚠️ **Moderate test-first development practices.**")
        report.append(
            "The project sometimes follows test-first development, but should improve consistency."
        )
    else:
        report.append("❌ **Poor test-first development practices.**")
        report.append(
            "The project rarely follows test-first development. Consider adopting TDD/BDD practices."
        )

    report.extend(["", "### Improvement Suggestions", ""])

    if test_first_ratio < 0.8:
        report.append("1. **Write tests before implementing features or fixing bugs.**")
        report.append(
            "2. **Use the `devsynth test` command to generate test cases before writing code.**"
        )
        report.append(
            "3. **Consider using BDD with Gherkin feature files to define behavior before implementation.**"
        )
        report.append(
            "4. **Review the TDD/BDD approach documentation in `docs/developer_guides/tdd_bdd_approach.md`.**"
        )

    report.extend(["", "## Recent Test-First Commits", ""])

    if metrics["recent_test_first_commits"]:
        for commit in metrics["recent_test_first_commits"]:
            report.append(
                f"- **{commit['date']}**: {commit['subject']} ({commit['hash'][:7]})"
            )
    else:
        report.append("No test-first commits found in the analyzed period.")

    report.extend(["", "## Recent Code-First Commits", ""])

    if metrics["recent_code_first_commits"]:
        for commit in metrics["recent_code_first_commits"]:
            report.append(
                f"- **{commit['date']}**: {commit['subject']} ({commit['hash'][:7]})"
            )
    else:
        report.append("No code-first commits found in the analyzed period.")

    return "\n".join(report)
