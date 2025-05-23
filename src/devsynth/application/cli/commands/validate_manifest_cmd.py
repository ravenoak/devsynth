"""
Command to validate the manifest.yaml file against its schema and project structure.

This command validates the manifest.yaml file against its JSON schema,
checks that referenced paths exist, validates dates and version formats,
and ensures the project structure is correctly represented.
"""
import json
import jsonschema
import yaml
import os
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devsynth.exceptions import DevSynthError, ManifestError
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

def validate_manifest_cmd(manifest_path: Optional[str] = None, schema_path: Optional[str] = None) -> None:
    """
    Validate the manifest.yaml file against its schema and project structure.
    
    Args:
        manifest_path: Path to the manifest.yaml file (default: manifest.yaml in current directory)
        schema_path: Path to the manifest schema JSON file (default: docs/manifest_schema.json)
    """
    console = Console()
    
    try:
        # Show a welcome message for the validate-manifest command
        console.print(Panel(
            "[bold blue]DevSynth Manifest Validation[/bold blue]\n\n"
            "This command validates the manifest.yaml file against its JSON schema, "
            "checks that referenced paths exist, validates dates and version formats, "
            "and ensures the project structure is correctly represented.",
            title="Manifest Validation",
            border_style="blue"
        ))
        
        # Determine the paths
        project_root = Path(os.getcwd()).resolve()
        
        if manifest_path is None:
            manifest_path = str(project_root / "manifest.yaml")
        
        if schema_path is None:
            schema_path = str(project_root / "docs" / "manifest_schema.json")
        
        manifest_path_obj = Path(manifest_path).resolve()
        schema_path_obj = Path(schema_path).resolve()
        
        console.print(f"[bold]Validating manifest:[/bold] {manifest_path_obj}")
        console.print(f"[bold]Using schema:[/bold] {schema_path_obj}")
        
        # Check if files exist
        if not manifest_path_obj.exists():
            console.print(f"[red]Error: Manifest file not found at {manifest_path_obj}[/red]")
            console.print("[yellow]Run 'devsynth init' to create a manifest.yaml file.[/yellow]")
            return
        
        if not schema_path_obj.exists():
            console.print(f"[red]Error: Schema file not found at {schema_path_obj}[/red]")
            return
        
        # Load the manifest and schema
        with open(manifest_path_obj, "r") as f:
            manifest = yaml.safe_load(f)
        
        with open(schema_path_obj, "r") as f:
            schema = json.load(f)
        
        # Validate against schema
        with console.status("[bold green]Validating against schema...[/bold green]"):
            try:
                jsonschema.validate(manifest, schema)
                console.print("[green]✓ Manifest is valid according to schema[/green]")
            except jsonschema.exceptions.ValidationError as e:
                console.print(f"[red]✗ Schema validation error: {e.message}[/red]")
                return
        
        # Validate paths exist
        with console.status("[bold green]Validating paths...[/bold green]"):
            path_errors = validate_paths_exist(manifest, project_root)
            if not path_errors:
                console.print("[green]✓ All referenced paths exist[/green]")
            else:
                console.print("[red]✗ Some referenced paths do not exist:[/red]")
                for error in path_errors:
                    console.print(f"  - {error}")
        
        # Validate dates
        with console.status("[bold green]Validating dates...[/bold green]"):
            date_errors = validate_dates(manifest)
            if not date_errors:
                console.print("[green]✓ All dates are valid[/green]")
            else:
                console.print("[red]✗ Some dates are invalid:[/red]")
                for error in date_errors:
                    console.print(f"  - {error}")
        
        # Validate version formats
        with console.status("[bold green]Validating version formats...[/bold green]"):
            version_errors = validate_version_format(manifest)
            if not version_errors:
                console.print("[green]✓ All version formats are valid[/green]")
            else:
                console.print("[red]✗ Some version formats are invalid:[/red]")
                for error in version_errors:
                    console.print(f"  - {error}")
        
        # Validate project structure
        with console.status("[bold green]Validating project structure...[/bold green]"):
            structure_errors = validate_project_structure(manifest, project_root)
            if not structure_errors:
                console.print("[green]✓ Project structure is valid[/green]")
            else:
                console.print("[red]✗ Project structure validation errors:[/red]")
                for error in structure_errors:
                    console.print(f"  - {error}")
        
        # Overall validation result
        if not path_errors and not date_errors and not version_errors and not structure_errors:
            console.print("\n[bold green]✓ Manifest is valid![/bold green]")
        else:
            console.print("\n[bold red]✗ Manifest has validation errors.[/bold red]")
            console.print("[yellow]Run 'devsynth analyze-manifest --update' to update the manifest.[/yellow]")
    
    except Exception as err:
        console.print(f"[red]Error:[/red] {err}", highlight=False)

def validate_paths_exist(manifest: dict, project_root: Path) -> list:
    """
    Validate that paths referenced in the manifest exist in the project.
    
    Args:
        manifest: The manifest dictionary
        project_root: The root directory of the project
    
    Returns:
        A list of error messages for paths that don't exist
    """
    errors = []
    
    # Check key artifacts
    if "keyArtifacts" in manifest:
        for artifact_type, artifacts in manifest["keyArtifacts"].items():
            for artifact in artifacts:
                if "path" in artifact:
                    path = project_root / artifact["path"]
                    if not path.exists():
                        errors.append(f"Key artifact path does not exist: {artifact['path']}")
    
    # Check structure directories
    if "structure" in manifest and "directories" in manifest["structure"]:
        for dir_type, dirs in manifest["structure"]["directories"].items():
            for dir_path in dirs:
                path = project_root / dir_path
                if not path.exists():
                    errors.append(f"Structure directory does not exist: {dir_path}")
    
    # Check entry points
    if "structure" in manifest and "entryPoints" in manifest["structure"]:
        for entry_point in manifest["structure"]["entryPoints"]:
            path = project_root / entry_point
            if not path.exists():
                errors.append(f"Entry point does not exist: {entry_point}")
    
    return errors

def validate_dates(manifest: dict) -> list:
    """
    Validate date formats in the manifest.
    
    Args:
        manifest: The manifest dictionary
    
    Returns:
        A list of error messages for invalid dates
    """
    errors = []
    
    # Check lastUpdated
    if "lastUpdated" in manifest:
        try:
            # Try to parse the date
            date_str = manifest["lastUpdated"]
            if isinstance(date_str, str):
                import dateutil.parser
                dateutil.parser.parse(date_str)
        except Exception:
            errors.append(f"Invalid lastUpdated date format: {manifest['lastUpdated']}")
    
    return errors

def validate_version_format(manifest: dict) -> list:
    """
    Validate version formats in the manifest.
    
    Args:
        manifest: The manifest dictionary
    
    Returns:
        A list of error messages for invalid version formats
    """
    errors = []
    
    # Check version
    if "version" in manifest:
        version = manifest["version"]
        if not isinstance(version, str):
            errors.append(f"Version must be a string, got {type(version).__name__}")
        elif not re.match(r"^\d+\.\d+\.\d+$", version):
            errors.append(f"Invalid version format: {version}. Expected format: X.Y.Z")
    
    return errors

def validate_project_structure(manifest: dict, project_root: Path) -> list:
    """
    Validate the project structure defined in the manifest.
    
    Args:
        manifest: The manifest dictionary
        project_root: The root directory of the project
    
    Returns:
        A list of error messages for structure validation errors
    """
    errors = []
    
    # Check if structure is defined
    if "structure" not in manifest:
        errors.append("No 'structure' section defined in manifest")
        return errors
    
    structure = manifest["structure"]
    
    # Check required structure fields
    required_fields = ["type", "primaryLanguage", "directories"]
    for field in required_fields:
        if field not in structure:
            errors.append(f"Missing required field in structure: {field}")
    
    # Check directories
    if "directories" in structure:
        directories = structure["directories"]
        if not isinstance(directories, dict):
            errors.append("'directories' must be a dictionary")
        else:
            # Check common directory types
            common_types = ["source", "tests", "docs"]
            for dir_type in common_types:
                if dir_type not in directories:
                    errors.append(f"Missing common directory type: {dir_type}")
                elif not isinstance(directories[dir_type], list):
                    errors.append(f"Directory type '{dir_type}' must be a list of paths")
    
    return errors

# Add missing import
import re