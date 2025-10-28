"""
Command to generate API reference documentation for a project.

This command generates API reference documentation for a project based on the manifest.yaml file,
creating a page for each module in the project.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def generate_docs_cmd(
    path: str | None = None,
    output_dir: str | None = None,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Generate API reference documentation for a project.

    Example:
        `devsynth generate-docs --path .`

    This command generates API reference documentation for a project based on the manifest.yaml file,
    creating a page for each module in the project.

    Args:
        path: Path to the project directory (default: current directory)
        output_dir: Directory where the documentation should be generated (default: docs/api_reference)
    """
    console = Console()
    bridge = bridge or globals()["bridge"]

    try:
        # Show a welcome message for the generate-docs command
        bridge.print(
            Panel(
                "[bold blue]DevSynth Documentation Generator[/bold blue]\n\n"
                "This command will generate API reference documentation for your project "
                "based on the manifest.yaml file.",
                title="Documentation Generator",
                border_style="blue",
            )
        )

        # Determine the path to analyze
        if path is None:
            path = os.getcwd()

        project_path = Path(path).resolve()
        manifest_path = project_path / "manifest.yaml"

        bridge.print(f"[bold]Analyzing project at:[/bold] {project_path}")

        # Check if manifest.yaml exists
        if not manifest_path.exists():
            bridge.print(
                "[yellow]Warning: manifest.yaml not found. Run 'devsynth init' to create it.[/yellow]"
            )
            return

        # Load the manifest.yaml file
        try:
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            bridge.print(f"[red]Error loading manifest: {e}[/red]")
            return

        # Determine the output directory
        if output_dir is None:
            output_dir = os.path.join(project_path, "docs", "api_reference")
        else:
            output_dir = os.path.join(project_path, output_dir)

        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Get source directories from project structure if available
        src_dirs = []
        if (
            "structure" in manifest
            and "directories" in manifest["structure"]
            and "source" in manifest["structure"]["directories"]
        ):
            for src_dir in manifest["structure"]["directories"]["source"]:
                src_dirs.append(project_path / src_dir)

        # Check for custom layouts and monorepos
        if "structure" in manifest and "customLayouts" in manifest["structure"]:
            custom = manifest["structure"]["customLayouts"]
            if (
                "type" in custom
                and custom["type"] == "monorepo"
                and "packages" in custom
            ):
                for package in custom["packages"]:
                    if "path" in package and "source" in package:
                        src_dirs.append(
                            project_path / package["path"] / package["source"]
                        )

        # If no source directories specified, default to src/
        if not src_dirs:
            src_dirs = [project_path / "src"]

        # Process each source directory
        for src in src_dirs:
            if not src.exists():
                bridge.print(
                    f"[yellow]Warning: Source directory {src} does not exist[/yellow]"
                )
                continue

            bridge.print(f"[green]Generating API reference for {src}[/green]")

            # Create a summary file for navigation
            summary_path = Path(output_dir) / "SUMMARY.md"
            with open(summary_path, "w") as summary_file:
                summary_file.write("# API Reference\n\n")

            # Process each Python file
            for path in sorted(src.rglob("*.py")):
                module_path = path.relative_to(src).with_suffix("")
                doc_path = path.relative_to(src).with_suffix(".md")
                full_doc_path = Path(output_dir) / doc_path

                parts = tuple(module_path.parts)

                if parts[-1] == "__init__":
                    parts = parts[:-1]
                    doc_path = doc_path.with_name("index.md")
                    full_doc_path = full_doc_path.with_name("index.md")
                elif parts[-1] == "__main__":
                    continue

                # Create the directory for the module
                os.makedirs(full_doc_path.parent, exist_ok=True)

                # Create the documentation file
                with open(full_doc_path, "w") as f:
                    identifier = ".".join(parts)
                    f.write(f"# {identifier}\n\n")
                    f.write(f"```python\n")
                    f.write(f"import {identifier}\n")
                    f.write(f"```\n\n")
                    f.write(f"## Module Documentation\n\n")
                    f.write(
                        f"This documentation is generated from the source code.\n\n"
                    )

                    # Add the module to the summary
                    with open(summary_path, "a") as summary_file:
                        summary_file.write(f"* [{identifier}]({doc_path})\n")

        bridge.print(
            f"[green]✓ Documentation generated successfully at: {output_dir}[/green]"
        )
        bridge.print("\n[bold blue]Next Steps:[/bold blue]")
        bridge.print("1. Review the generated documentation")
        bridge.print("2. Build the documentation site with MkDocs")
        bridge.print("3. Deploy the documentation site")

    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        bridge.print(f"[red]Error generating documentation: {str(e)}[/red]")
