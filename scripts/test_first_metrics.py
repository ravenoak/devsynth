#!/usr/bin/env python
"""
Script to generate metrics for test-first development adherence.

This script analyzes the git commit history to determine if tests were written
before implementation, and generates metrics on test-first development adherence.
"""
import argparse
import json
import subprocess
from typing import Any


def get_commit_history(days: int = 30) -> list[dict[str, Any]]:
    """
    Get the commit history from git for the specified number of days.

    Args:
        days: Number of days to look back in the commit history

    Returns:
        List of commit dictionaries with hash, author, date, and message
    """
    # Get the commit history from git
    result = subprocess.run(
        [
            "git",
            "log",
            "--pretty=format:%H|%an|%ad|%s",
            "--date=short",
            f"--since={days} days ago",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse the commit history
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        parts = line.split("|")
        if len(parts) < 4:
            continue

        commit = {
            "hash": parts[0],
            "author": parts[1],
            "date": parts[2],
            "message": parts[3],
        }
        commits.append(commit)

    return commits


def analyze_commit(commit: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze a commit to determine if it follows test-first development.

    Args:
        commit: Commit dictionary with hash, author, date, and message

    Returns:
        Updated commit dictionary with files list
    """
    # Get the files changed in the commit
    result = subprocess.run(
        ["git", "show", "--name-status", "--format=", commit["hash"]],
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse the files changed
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) < 2:
            continue

        status = parts[0]
        path = parts[1]

        files.append({"path": path, "status": status})

    # Add the files to the commit
    commit["files"] = files

    return commit


def calculate_metrics(commits: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate metrics from commit data.

    Args:
        commits: List of commit dictionaries with files

    Returns:
        Dictionary of metrics
    """
    # Initialize metrics
    metrics = {
        "total_commits": 0,
        "test_first_commits": 0,
        "implementation_first_commits": 0,
        "test_first_percentage": 0.0,
        "by_author": {},
        "by_date": {},
    }

    # Process each commit
    for commit in commits:
        # Skip commits with no files
        if "files" not in commit or not commit["files"]:
            continue

        # Check if the commit has both implementation and test files
        has_implementation = False
        has_test = False
        for file in commit["files"]:
            path = file["path"]
            if (
                path.startswith("src/")
                and path.endswith(".py")
                and not path.endswith("__init__.py")
            ):
                has_implementation = True
            elif path.startswith("tests/") and (
                path.endswith(".py") or path.endswith(".feature")
            ):
                has_test = True

        # Skip commits that don't have both implementation and test files
        if not has_implementation:
            continue

        # Update overall metrics
        metrics["total_commits"] += 1

        # Determine if the commit follows test-first development
        is_test_first = has_test

        if is_test_first:
            metrics["test_first_commits"] += 1
        else:
            metrics["implementation_first_commits"] += 1

        # Update author metrics
        author = commit["author"]
        if author not in metrics["by_author"]:
            metrics["by_author"][author] = {
                "total_commits": 0,
                "test_first_commits": 0,
                "implementation_first_commits": 0,
                "test_first_percentage": 0.0,
            }

        metrics["by_author"][author]["total_commits"] += 1
        if is_test_first:
            metrics["by_author"][author]["test_first_commits"] += 1
        else:
            metrics["by_author"][author]["implementation_first_commits"] += 1

        # Update date metrics
        date = commit["date"]
        if date not in metrics["by_date"]:
            metrics["by_date"][date] = {
                "total_commits": 0,
                "test_first_commits": 0,
                "implementation_first_commits": 0,
                "test_first_percentage": 0.0,
            }

        metrics["by_date"][date]["total_commits"] += 1
        if is_test_first:
            metrics["by_date"][date]["test_first_commits"] += 1
        else:
            metrics["by_date"][date]["implementation_first_commits"] += 1

    # Calculate percentages
    if metrics["total_commits"] > 0:
        metrics["test_first_percentage"] = round(
            metrics["test_first_commits"] / metrics["total_commits"] * 100, 2
        )

    for author in metrics["by_author"]:
        if metrics["by_author"][author]["total_commits"] > 0:
            metrics["by_author"][author]["test_first_percentage"] = round(
                metrics["by_author"][author]["test_first_commits"]
                / metrics["by_author"][author]["total_commits"]
                * 100,
                2,
            )

    for date in metrics["by_date"]:
        if metrics["by_date"][date]["total_commits"] > 0:
            metrics["by_date"][date]["test_first_percentage"] = round(
                metrics["by_date"][date]["test_first_commits"]
                / metrics["by_date"][date]["total_commits"]
                * 100,
                2,
            )

    return metrics


def generate_metrics_report(metrics: dict[str, Any]) -> str:
    """
    Generate a human-readable report from the metrics.

    Args:
        metrics: Dictionary of metrics

    Returns:
        Human-readable report
    """
    report = []

    # Add header
    report.append("# Test-First Development Metrics")
    report.append("")

    # Add overall metrics
    report.append("## Overall Metrics")
    report.append("")
    report.append(f"Total commits: {metrics['total_commits']}")
    report.append(f"Test-first commits: {metrics['test_first_commits']}")
    report.append(
        f"Implementation-first commits: {metrics['implementation_first_commits']}"
    )
    report.append(f"Test-first percentage: {metrics['test_first_percentage']}%")
    report.append("")

    # Add author metrics
    report.append("## Metrics by Author")
    report.append("")
    for author, author_metrics in metrics["by_author"].items():
        report.append(f"### {author}")
        report.append("")
        report.append(f"Total commits: {author_metrics['total_commits']}")
        report.append(f"Test-first commits: {author_metrics['test_first_commits']}")
        report.append(
            "Implementation-first commits: "
            f"{author_metrics['implementation_first_commits']}"
        )
        report.append(
            f"Test-first percentage: {author_metrics['test_first_percentage']}%"
        )
        report.append("")

    # Add date metrics
    report.append("## Metrics by Date")
    report.append("")
    for date, date_metrics in sorted(metrics["by_date"].items()):
        report.append(f"### {date}")
        report.append("")
        report.append(f"Total commits: {date_metrics['total_commits']}")
        report.append(f"Test-first commits: {date_metrics['test_first_commits']}")
        report.append(
            "Implementation-first commits: "
            f"{date_metrics['implementation_first_commits']}"
        )
        report.append(
            f"Test-first percentage: {date_metrics['test_first_percentage']}%"
        )
        report.append("")

    return "\n".join(report)


def main(days: int = 30, output_file: str | None = None) -> None:
    """
    Main function to generate test-first development metrics.

    Args:
        days: Number of days to look back in the commit history
        output_file: Path to the output file for the metrics JSON
    """
    # Get the commit history
    commits = get_commit_history(days=days)

    # Analyze each commit
    analyzed_commits = []
    for commit in commits:
        analyzed_commit = analyze_commit(commit)
        analyzed_commits.append(analyzed_commit)

    # Calculate metrics
    metrics = calculate_metrics(analyzed_commits)

    # Generate report
    report = generate_metrics_report(metrics)

    # Print the report
    print(report)

    # Save the metrics to a file if specified
    if output_file:
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nMetrics saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate test-first development metrics"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back in the commit history",
    )
    parser.add_argument(
        "--output", type=str, help="Path to the output file for the metrics JSON"
    )
    args = parser.parse_args()

    main(days=args.days, output_file=args.output)
