"""
Command handler for the 'align' command.

This module provides functionality to check alignment between SDLC artifacts.
"""

import os
import re
from typing import Dict, List, Optional, Set

from rich.console import Console
from rich.table import Table

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Console for rich output
bridge: UXBridge = CLIUXBridge()
console = Console()

# Regular expressions for finding references
REQ_REF_PATTERN = re.compile(r"FR-\d+|NFR-\d+")
SPEC_REF_PATTERN = re.compile(r"SPEC-\d+")
TEST_REF_PATTERN = re.compile(r"TEST-\d+")

# File patterns for different artifact types
REQUIREMENT_FILES = ["docs/requirements/", "docs/system_requirements_specification.md"]
SPECIFICATION_FILES = ["docs/specifications/"]
TEST_FILES = ["tests/"]
CODE_FILES = ["src/"]


def is_file_of_type(file_path: str, type_patterns: list[str]) -> bool:
    """Check if a file matches any of the given patterns."""
    return any(pattern in file_path for pattern in type_patterns)


def extract_references(file_path: str, pattern: re.Pattern) -> set[str]:
    """Extract references matching the given pattern from a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        return set(pattern.findall(content))
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return set()


def get_all_files(directory: str = ".", exclude_dirs: list[str] = None) -> list[str]:
    """Get all files in the given directory and its subdirectories."""
    if exclude_dirs is None:
        exclude_dirs = [
            ".git",
            ".github",
            "__pycache__",
            "venv",
            ".venv",
            "node_modules",
        ]

    all_files = []
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            all_files.append(os.path.join(root, file))

    return all_files


def check_requirement_references(files: list[str]) -> list[dict]:
    """Check if specifications reference requirements."""
    issues = []

    # Get all requirement IDs
    all_requirements = set()
    for file in files:
        if is_file_of_type(file, REQUIREMENT_FILES):
            all_requirements.update(extract_references(file, REQ_REF_PATTERN))

    # Check specifications for requirement references
    for file in files:
        if is_file_of_type(file, SPECIFICATION_FILES):
            spec_requirements = extract_references(file, REQ_REF_PATTERN)
            if not spec_requirements:
                issues.append(
                    {
                        "type": "requirement_reference",
                        "file": file,
                        "message": f"Specification does not reference any requirements",
                    }
                )

    return issues


def check_specification_references(files: list[str]) -> list[dict]:
    """Check if tests reference specifications."""
    issues = []

    # Get all specification IDs
    all_specifications = set()
    for file in files:
        if is_file_of_type(file, SPECIFICATION_FILES):
            all_specifications.update(extract_references(file, SPEC_REF_PATTERN))

    # Check tests for specification references
    for file in files:
        if is_file_of_type(file, TEST_FILES):
            test_specifications = extract_references(file, SPEC_REF_PATTERN)
            if not test_specifications:
                issues.append(
                    {
                        "type": "specification_reference",
                        "file": file,
                        "message": f"Test does not reference any specifications",
                    }
                )

    return issues


def check_test_references(files: list[str]) -> list[dict]:
    """Check if code references tests."""
    issues = []

    # Get all test IDs
    all_tests = set()
    for file in files:
        if is_file_of_type(file, TEST_FILES):
            all_tests.update(extract_references(file, TEST_REF_PATTERN))

    # Check code for test references
    for file in files:
        if is_file_of_type(file, CODE_FILES) and file.endswith(".py"):
            code_tests = extract_references(file, TEST_REF_PATTERN)
            if not code_tests:
                issues.append(
                    {
                        "type": "test_reference",
                        "file": file,
                        "message": f"Code does not reference any tests",
                    }
                )

    return issues


def check_terminology_consistency(files: list[str]) -> list[dict]:
    """Check for terminology consistency across artifacts."""
    issues = []

    # This is a simplified check - in a real implementation, you would
    # load a glossary of terms and check for consistent usage

    # For now, just check for common inconsistencies
    term_variants = {
        "specification": ["spec", "specification"],
        "requirement": ["req", "requirement"],
        "implementation": ["impl", "implementation"],
        "configuration": ["config", "configuration"],
    }

    for file in files:
        try:
            with open(file, encoding="utf-8") as f:
                content = f.read().lower()

                for term, variants in term_variants.items():
                    found_variants = [v for v in variants if v in content]
                    if len(found_variants) > 1:
                        issues.append(
                            {
                                "type": "terminology_consistency",
                                "file": file,
                                "message": f"Inconsistent terminology: found multiple variants of '{term}': {', '.join(found_variants)}",
                            }
                        )
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")

    return issues


def check_alignment(
    path: str = ".",
    verbose: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> list[dict]:
    """Check alignment between SDLC artifacts."""
    logger.info(f"Checking alignment in {path}")

    # Get all files
    files = get_all_files(path)

    # Only check files that exist
    existing_files = [f for f in files if os.path.isfile(f)]

    if verbose:
        bridge.print(f"Found {len(existing_files)} files to check")

    # Run checks
    issues = []
    issues.extend(check_requirement_references(existing_files))
    issues.extend(check_specification_references(existing_files))
    issues.extend(check_test_references(existing_files))
    issues.extend(check_terminology_consistency(existing_files))

    return issues


def display_issues(issues: list[dict], *, bridge: UXBridge = bridge) -> None:
    """Display alignment issues in a table."""
    if not issues:
        bridge.print("[green]No alignment issues found![/green]")
        return

    # Group issues by type
    issues_by_type = {}
    for issue in issues:
        issue_type = issue["type"]
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)

    # Display summary
    bridge.print(f"[yellow]Found {len(issues)} alignment issues:[/yellow]")
    for issue_type, type_issues in issues_by_type.items():
        bridge.print(f"  - {len(type_issues)} {issue_type.replace('_', ' ')} issues")

    # Display detailed table
    table = Table(title="Alignment Issues")
    table.add_column("Type", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Message", style="yellow")

    for issue in issues:
        table.add_row(
            issue["type"].replace("_", " ").title(), issue["file"], issue["message"]
        )

    bridge.print(table)


def align_cmd(
    path: str = ".",
    verbose: bool = False,
    quiet: bool = False,
    output: str | None = None,
    *,
    bridge: UXBridge | None = None,
) -> bool:
    """Check alignment between SDLC artifacts.

    Example:
        `devsynth align --path . --verbose`

    Args:
        path: Path to the project directory
        verbose: Whether to show verbose output
        output: Path to output file for alignment report
    """
    ux_bridge = bridge or globals()["bridge"]
    # Quiet flag is accepted for CLI compatibility but currently unused
    _ = quiet
    try:
        ux_bridge.print("[bold]Checking alignment between SDLC artifacts...[/bold]")

        # Check alignment
        issues = check_alignment(path, verbose, bridge=ux_bridge)

        # Display issues
        display_issues(issues, bridge=ux_bridge)

        # Output to file if specified
        if output:
            try:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(f"# Alignment Report\n\n")
                    f.write(f"Found {len(issues)} alignment issues.\n\n")

                    for issue in issues:
                        f.write(f"## {issue['type'].replace('_', ' ').title()}\n\n")
                        f.write(f"File: {issue['file']}\n\n")
                        f.write(f"Message: {issue['message']}\n\n")

                ux_bridge.print(f"[green]Alignment report saved to {output}[/green]")
            except Exception as e:
                logger.error(f"Error writing to output file: {e}")
                ux_bridge.print(f"[red]Error writing to output file: {e}[/red]")

        # Return success or failure
        return len(issues) == 0

    except Exception as e:
        logger.error(f"Error checking alignment: {e}")
        ux_bridge.print(f"[red]Error checking alignment: {e}[/red]")
        return False
