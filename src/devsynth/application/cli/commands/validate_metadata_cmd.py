"""
Command to validate metadata in Markdown files.

This command validates the front-matter metadata in Markdown files,
checking for required fields, date formats, version formats, and other constraints.
"""

import os
import pathlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def validate_metadata_cmd(
    directory: str | None = None,
    file: str | None = None,
    verbose: bool = False,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Validate metadata in Markdown files.

    Example:
        `devsynth validate-metadata --directory docs`

    Args:
        directory: Directory containing Markdown files to validate (default: docs/)
        file: Single Markdown file to validate
        verbose: Whether to show detailed validation results
    """
    console = Console()
    bridge = bridge or globals()["bridge"]

    try:
        # Show a welcome message for the validate-metadata command
        bridge.print(
            Panel(
                "[bold blue]DevSynth Metadata Validation[/bold blue]\n\n"
                "This command validates the front-matter metadata in Markdown files, "
                "checking for required fields, date formats, version formats, and other constraints.",
                title="Metadata Validation",
                border_style="blue",
            )
        )

        # Determine the paths
        project_root = pathlib.Path(os.getcwd()).resolve()

        if directory is None and file is None:
            directory = "docs"

        files_to_validate = []

        if file:
            file_path = pathlib.Path(file).resolve()
            if not file_path.exists():
                bridge.print(f"[red]Error: File not found: {file_path}[/red]")
                return
            files_to_validate.append(file_path)

        if directory:
            dir_path = pathlib.Path(directory).resolve()
            if not dir_path.exists():
                bridge.print(f"[red]Error: Directory not found: {dir_path}[/red]")
                return

            # Find all Markdown files in the directory and its subdirectories
            for root, _, files in os.walk(dir_path):
                for filename in files:
                    if filename.endswith(".md"):
                        files_to_validate.append(pathlib.Path(root) / filename)

        if not files_to_validate:
            bridge.print("[yellow]No Markdown files found to validate.[/yellow]")
            return

        bridge.print(
            f"[bold]Found {len(files_to_validate)} Markdown files to validate.[/bold]"
        )

        # Validate each file
        validation_results = []

        with console.status("[bold green]Validating metadata...[/bold green]"):
            for file_path in files_to_validate:
                result = validate_file_metadata(file_path)
                validation_results.append((file_path, result))

        # Display results
        success_count = sum(1 for _, result in validation_results if result["valid"])
        error_count = len(validation_results) - success_count

        bridge.print(
            f"\n[bold]Validation Results:[/bold] {success_count} valid, {error_count} with errors"
        )

        if error_count > 0:
            # Create a table for files with errors
            error_table = Table(show_header=True, header_style="bold")
            error_table.add_column("File")
            error_table.add_column("Errors")

            for file_path, result in validation_results:
                if not result["valid"]:
                    rel_path = file_path.relative_to(project_root)
                    error_table.add_row(str(rel_path), "\n".join(result["errors"]))

            bridge.print("\n[bold]Files with errors:[/bold]")
            bridge.print(error_table)

        if verbose:
            # Create a table for all files
            all_table = Table(show_header=True, header_style="bold")
            all_table.add_column("File")
            all_table.add_column("Status")
            all_table.add_column("Details")

            for file_path, result in validation_results:
                rel_path = file_path.relative_to(project_root)
                status = (
                    "[green]Valid[/green]" if result["valid"] else "[red]Invalid[/red]"
                )
                details = (
                    ", ".join(result.get("metadata", {}).keys())
                    if result["valid"]
                    else "\n".join(result["errors"])
                )

                all_table.add_row(str(rel_path), status, details)

            bridge.print("\n[bold]All files:[/bold]")
            bridge.print(all_table)

        # Overall validation result
        if error_count == 0:
            bridge.print("\n[bold green]✓ All metadata is valid![/bold green]")
        else:
            bridge.print("\n[bold red]✗ Some files have metadata errors.[/bold red]")
            bridge.print(
                "[yellow]Please fix the errors in the files listed above.[/yellow]"
            )

    except Exception as err:
        bridge.print(f"[red]Error:[/red] {err}", highlight=False)


def validate_file_metadata(file_path: pathlib.Path) -> dict[str, Any]:
    """
    Validate metadata in a single Markdown file.

    Args:
        file_path: Path to the Markdown file

    Returns:
        A dictionary with validation results
    """
    result = {"valid": False, "errors": [], "metadata": None}

    try:
        # Read the file
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Extract front matter
        metadata = extract_front_matter(content)

        if metadata is None:
            result["errors"].append("No front-matter metadata found")
            return result

        # Validate metadata
        errors = validate_metadata(file_path, metadata)

        if errors:
            result["errors"] = errors
            return result

        # If we got here, the metadata is valid
        result["valid"] = True
        result["metadata"] = metadata
        return result

    except Exception as e:
        result["errors"].append(f"Error processing file: {str(e)}")
        return result


def extract_front_matter(content: str) -> dict[str, Any] | None:
    """
    Extract front-matter metadata from Markdown content.

    Args:
        content: The content of the Markdown file

    Returns:
        The extracted metadata as a dictionary, or None if no front-matter is found
    """
    # Check if the content starts with ---
    if not content.startswith("---"):
        return None

    # Find the end of the front matter
    end_index = content.find("---", 3)
    if end_index == -1:
        return None

    # Extract the front matter
    front_matter = content[3:end_index].strip()

    # Parse the front matter as YAML
    try:
        metadata = yaml.safe_load(front_matter)
        return metadata
    except Exception:
        return None


def validate_metadata(file_path: pathlib.Path, metadata: dict[str, Any]) -> list[str]:
    """
    Validate metadata against requirements.

    Args:
        file_path: Path to the file being validated
        metadata: The metadata dictionary

    Returns:
        A list of error messages, or an empty list if the metadata is valid
    """
    errors = []

    # Check required fields
    required_fields = ["title", "date", "version"]
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")

    # Validate date format
    if "date" in metadata:
        date_error = validate_date(metadata["date"])
        if date_error:
            errors.append(date_error)

    # Validate version format
    if "version" in metadata:
        version_error = validate_version(metadata["version"])
        if version_error:
            errors.append(version_error)

    # Validate tags
    if "tags" in metadata:
        tags = metadata["tags"]
        if not isinstance(tags, list):
            errors.append("Tags must be a list")
        elif not all(isinstance(tag, str) for tag in tags):
            errors.append("All tags must be strings")

    # Validate status
    if "status" in metadata:
        status = metadata["status"]
        if not isinstance(status, str):
            errors.append("Status must be a string")
        elif status not in ["draft", "review", "published", "archived"]:
            errors.append(
                f"Invalid status: {status}. Must be one of: draft, review, published, archived"
            )

    # Validate author
    if "author" in metadata and not isinstance(metadata["author"], str):
        errors.append("Author must be a string")

    # Validate last_reviewed
    if "last_reviewed" in metadata:
        date_error = validate_date(metadata["last_reviewed"])
        if date_error:
            errors.append(f"Invalid last_reviewed: {date_error}")

    return errors


def validate_date(date_str: Any) -> str | None:
    """
    Validate a date string.

    Args:
        date_str: The date string to validate

    Returns:
        An error message if the date is invalid, or None if it's valid
    """
    if not isinstance(date_str, str):
        return f"Date must be a string, got {type(date_str).__name__}"

    try:
        # Try to parse the date
        datetime.strptime(date_str, "%Y-%m-%d")
        return None
    except ValueError:
        return f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD"


def validate_version(version_str: Any) -> str | None:
    """
    Validate a version string.

    Args:
        version_str: The version string to validate

    Returns:
        An error message if the version is invalid, or None if it's valid
    """
    if not isinstance(version_str, str):
        return f"Version must be a string, got {type(version_str).__name__}"

    if not re.match(r"^\d+\.\d+\.\d+$", version_str):
        return f"Invalid version format: {version_str}. Expected format: X.Y.Z"

    return None
