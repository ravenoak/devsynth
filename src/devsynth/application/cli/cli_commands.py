import os
import json
from pathlib import Path
from typing import Optional, Union, List, Dict, Any


import typer
import importlib.util
from rich.console import Console

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

from devsynth.core import workflows
from devsynth.core.workflows import (
    filter_args,
    init_project,
    generate_specs,
    generate_tests,
    generate_code,
    run_pipeline,
    inspect_requirements,
    gather_requirements,
)
import uvicorn
from devsynth.logging_setup import configure_logging
from ..orchestration.adaptive_workflow import adaptive_workflow_manager
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError
from devsynth.config import (
    get_settings,
    config_key_autocomplete as loader_autocomplete,
)
from devsynth.config import load_project_config
from .commands.edrr_cycle_cmd import edrr_cycle_cmd
from .commands.doctor_cmd import doctor_cmd

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def _resolve_bridge(b: Optional[UXBridge]) -> UXBridge:
    """Return the provided bridge or fall back to the module default."""
    return b if b is not None else bridge


console = Console()
config_app = typer.Typer(help="Manage configuration settings")


def _check_services(bridge: Optional[UXBridge] = None) -> bool:
    """Verify required services are available."""
    bridge = _resolve_bridge(bridge)
    settings = get_settings()
    messages: List[str] = []

    # Check ChromaDB availability only when the feature flag is enabled
    chromadb_enabled = getattr(settings, "enable_chromadb", False)
    if (
        chromadb_enabled
        and settings.vector_store_enabled
        and settings.memory_store_type == "chromadb"
    ):
        if importlib.util.find_spec("chromadb") is None:
            messages.append(
                "ChromaDB support is enabled but the 'chromadb' package is missing."
            )
    # Check Kuzu availability when vector store is enabled
    if settings.vector_store_enabled and settings.memory_store_type == "kuzu":
        if importlib.util.find_spec("kuzu") is None:
            messages.append(
                "Kuzu support is enabled but the 'kuzu' package is missing."
            )

    # Check LLM provider configuration
    provider = settings.provider_type
    if provider == "openai" and not settings.openai_api_key:
        messages.append("OPENAI_API_KEY is not set for the OpenAI provider.")
    if provider == "lmstudio" and not settings.lm_studio_endpoint:
        messages.append(
            "LM_STUDIO_ENDPOINT is not configured for the LM Studio provider."
        )

    if messages:
        for msg in messages:
            bridge.display_result(f"[red]{msg}[/red]", highlight=False)
        bridge.display_result(
            "[yellow]Use 'devsynth config' or edit your project.yaml to update settings.[/yellow]"
        )
        return False

    return True


def config_key_autocomplete(ctx: typer.Context, incomplete: str):
    """Provide autocompletion for configuration keys."""
    return loader_autocomplete(ctx, incomplete)


def init_cmd(*, bridge: Optional[UXBridge] = None) -> None:
    """Interactively initialize a new project."""

    bridge = _resolve_bridge(bridge)
    try:
        config = load_project_config()
        if config.exists():
            bridge.display_result("Project already initialized")
            return

        root = bridge.ask_question("Project root directory?")
        language = bridge.ask_question("Primary language?")
        goals = bridge.ask_question("Project goals?")

        if not bridge.confirm_choice("Proceed with initialization?", default=True):
            return

        config.set_root(root)
        config.set_language(language)
        config.set_goals(goals)
        config.save()

        bridge.display_result("Initialization complete", highlight=True)
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


def spec_cmd(
    requirements_file: str = "requirements.md", *, bridge: Optional[UXBridge] = None
) -> None:
    """Generate specifications from a requirements file.

    Example:
        `devsynth spec --requirements-file requirements.md`
    """
    bridge = _resolve_bridge(bridge)
    try:
        if not _check_services(bridge):
            return
        args = filter_args({"requirements_file": requirements_file})
        result = generate_specs(**args)
        if result.get("success"):
            bridge.display_result(
                f"[green]Specifications generated from {requirements_file}.[/green]"
            )
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message')}", highlight=False
            )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


def test_cmd(spec_file: str = "specs.md", *, bridge: Optional[UXBridge] = None) -> None:
    """Generate tests based on specifications.

    Example:
        `devsynth test --spec-file specs.md`
    """
    bridge = _resolve_bridge(bridge)
    try:
        if not _check_services(bridge):
            return
        args = filter_args({"spec_file": spec_file})
        result = generate_tests(**args)
        if result.get("success"):
            bridge.display_result(f"[green]Tests generated from {spec_file}.[/green]")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message')}", highlight=False
            )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


def code_cmd(*, bridge: Optional[UXBridge] = None) -> None:
    """Generate implementation code from tests.

    Example:
        `devsynth code`
    """
    bridge = _resolve_bridge(bridge)
    try:
        if not _check_services(bridge):
            return
        result = generate_code()
        if result.get("success"):
            bridge.display_result("[green]Code generated successfully.[/green]")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message')}", highlight=False
            )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


def run_pipeline_cmd(
    target: Optional[str] = None,
    report: Optional[Dict[str, Any]] = None,
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Run the generated code or a specific target.

    Parameters
    ----------
    target:
        Execution target (e.g. ``unit-tests``).
    report:
        Optional report data that should be persisted with pipeline results.

    Example
    -------
    ``devsynth run-pipeline --target unit-tests``
    """
    bridge = _resolve_bridge(bridge)
    try:
        result = workflows.execute_command(
            "run-pipeline", {"target": target, "report": report}
        )
        if result["success"]:
            if target:
                bridge.display_result(f"[green]Executed target: {target}[/green]")
            else:
                bridge.display_result(f"[green]Execution complete.[/green]")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result['message']}", highlight=False
            )
    except Exception as err:
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


@config_app.callback(invoke_without_command=True)
def config_cmd(
    key: Optional[str] = typer.Option(None, autocompletion=config_key_autocomplete),
    value: Optional[str] = None,
    list_models: bool = False,
    *,
    ctx: Optional[typer.Context] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """View or set configuration options.

    Example:
        `devsynth config --key model --value gpt-4`
    """
    bridge = _resolve_bridge(bridge)
    if isinstance(key, typer.models.OptionInfo):
        key = None
    if isinstance(value, typer.models.OptionInfo):
        value = None

    if ctx is not None and ctx.invoked_subcommand is not None:
        return
    try:
        config = load_project_config()
        args = {"key": key, "value": value}
        if list_models:
            args["list_models"] = True
        result = workflows.execute_command("config", args)
        if result.get("success"):
            if key and value:
                setattr(config.config, key, value)
                config.save()
                bridge.display_result(
                    f"[green]Configuration updated: {key} = {value}[/green]"
                )
            elif key:
                bridge.display_result(f"[blue]{key}:[/blue] {result.get('value')}")
            else:
                bridge.display_result(f"[blue]DevSynth Configuration:[/blue]")
                for k, v in result.get("config", {}).items():
                    bridge.display_result(f"  [yellow]{k}:[/yellow] {v}")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message')}", highlight=False
            )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


@config_app.command("enable-feature")
def enable_feature_cmd(name: str, *, bridge: Optional[UXBridge] = None) -> None:
    """Enable a feature flag in the project configuration.

    Example:
        `devsynth config enable-feature code_generation`
    """
    bridge = _resolve_bridge(bridge)
    try:
        config = load_project_config()
        features = config.config.features or {}
        features[name] = True
        config.config.features = features
        config.save()

        bridge.display_result(f"Feature '{name}' enabled.")
    except Exception as err:
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


def gather_cmd(
    output_file: str = "requirements_plan.yaml", *, bridge: Optional[UXBridge] = None
) -> None:
    """Interactively gather project goals, constraints and priority."""

    bridge = _resolve_bridge(bridge)
    gather_requirements(bridge, output_file=output_file)


def refactor_cmd(
    path: Optional[str] = None, *, bridge: Optional[UXBridge] = None
) -> None:
    """
    Execute a refactor workflow based on the current project state.

    This command analyzes the current project state, determines the optimal workflow,
    and suggests appropriate next steps.

    Args:
        path: Path to the project root directory (default: current directory)

    Example:
        `devsynth refactor --path ./my-project`
    """
    bridge = _resolve_bridge(bridge)
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.markdown import Markdown

        console = Console()

        # Show a welcome message for the refactor command
        bridge.print(
            Panel(
                "[bold blue]DevSynth Refactor Workflow[/bold blue]\n\n"
                "This command will analyze your project state, determine the optimal workflow, "
                "and suggest appropriate next steps.",
                title="Refactor Workflow",
                border_style="blue",
            )
        )

        # Set the project path
        project_path = path or os.getcwd()

        # Execute the refactor workflow
        result = adaptive_workflow_manager.execute_adaptive_workflow(project_path)

        if result.get("success", False):
            # Display the workflow information
            bridge.print(f"[green]Workflow:[/green] {result['workflow']}")
            bridge.print(f"[green]Entry Point:[/green] {result['entry_point']}")

            # Display the suggestions
            bridge.print("\n[bold]Suggested Next Steps:[/bold]")

            # Create a table for the suggestions
            table = Table(show_header=True, header_style="bold")
            table.add_column("Priority", style="cyan")
            table.add_column("Command", style="green")
            table.add_column("Description")

            for suggestion in result["suggestions"]:
                table.add_row(
                    suggestion["priority"].upper(),
                    suggestion["command"],
                    suggestion["description"],
                )

            bridge.print(table)

            # Display the message
            bridge.print(f"\n[green]{result['message']}[/green]")
        else:
            bridge.print(f"[red]Error:[/red] {result.get('message', 'Unknown error')}")
    except Exception as e:
        bridge.print(f"[red]Error:[/red] {str(e)}")


def inspect_cmd(
    input_file: Optional[str] = None,
    interactive: bool = False,
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Inspect requirements from a file or interactively.

    Example:
        `devsynth inspect --input requirements.txt`
    """
    bridge = _resolve_bridge(bridge)
    try:
        if not _check_services(bridge):
            return
        args = filter_args({"input": input_file, "interactive": interactive})
        result = inspect_requirements(**args)
        if result.get("success"):
            bridge.display_result("[green]Requirements inspection completed.[/green]")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message')}", highlight=False
            )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


def webapp_cmd(
    framework: str = "flask",
    name: str = "webapp",
    path: str = ".",
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Generate a web application with the specified framework.

    Example:
        `devsynth webapp --framework flask --name myapp --path ./apps`
    """
    try:
        from rich.prompt import Prompt, Confirm
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.table import Table

        # Show a welcome message for the webapp command
        bridge.print(
            Panel(
                f"[bold blue]DevSynth Web Application Generator[/bold blue]\n\n"
                f"This command will generate a basic web application using the {framework} framework.",
                title="Web Application Generator",
                border_style="blue",
            )
        )

        # Validate and normalize the framework name
        framework = framework.lower()
        supported_frameworks = ["flask", "fastapi", "django", "express"]

        if framework not in supported_frameworks:
            bridge.print(
                f"[yellow]Warning: '{framework}' is not a recognized framework.[/yellow]"
            )
            bridge.print(
                f"[yellow]Supported frameworks: {', '.join(supported_frameworks)}[/yellow]"
            )

            # Ask user to select a framework
            framework_table = Table(title="Supported Frameworks")
            framework_table.add_column("Framework", style="cyan")
            framework_table.add_column("Description")
            framework_table.add_column("Language", style="green")

            framework_table.add_row(
                "flask", "Lightweight WSGI web application framework", "Python"
            )
            framework_table.add_row(
                "fastapi", "Modern, fast web framework for building APIs", "Python"
            )
            framework_table.add_row(
                "django", "High-level web framework with batteries included", "Python"
            )
            framework_table.add_row(
                "express", "Fast, unopinionated, minimalist web framework", "JavaScript"
            )

            bridge.print(framework_table)

            framework = bridge.prompt(
                "[blue]Select a framework[/blue]",
                choices=supported_frameworks,
                default="flask",
            )

        # Get project name if not provided
        if name == "webapp":
            name = bridge.prompt("[blue]Project name[/blue]", default="webapp")

        # Sanitize project name
        name = name.replace(" ", "_").lower()

        # Get project path if not provided
        if path == ".":
            path = bridge.prompt("[blue]Project path[/blue]", default=".")

        # Create full project path
        project_path = os.path.join(path, name)

        # Check if directory already exists
        if os.path.exists(project_path):
            if not bridge.confirm(
                f"[yellow]Directory {project_path} already exists. Overwrite?[/yellow]"
            ):
                bridge.print("[yellow]Operation cancelled.[/yellow]")
                return

            # Remove existing directory
            shutil.rmtree(project_path)

        # Create project directory
        os.makedirs(project_path, exist_ok=True)

        # Show progress during generation
        with bridge.create_progress(
            f"Generating {framework} project...", total=100
        ) as progress:

            # Generate Flask project (for now, we'll only implement Flask)
            if framework == "flask":
                # Create app directory
                app_dir = os.path.join(project_path, name)
                os.makedirs(app_dir, exist_ok=True)

                progress.update(advance=20, description="Creating Flask application...")

                # Create __init__.py
                with open(os.path.join(app_dir, "__init__.py"), "w") as f:
                    f.write(
                        """from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import and register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
"""
                    )

                # Create routes.py
                with open(os.path.join(app_dir, "routes.py"), "w") as f:
                    f.write(
                        """from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', title='Home')
"""
                    )

                # Create templates directory
                templates_dir = os.path.join(app_dir, "templates")
                os.makedirs(templates_dir, exist_ok=True)

                # Create index.html
                with open(os.path.join(templates_dir, "index.html"), "w") as f:
                    f.write(
                        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <h1>Welcome to {{ title }}</h1>
    </header>
    <main>
        <p>This is a Flask application generated by DevSynth.</p>
    </main>
    <footer>
        <p>&copy; 2023 DevSynth</p>
    </footer>
</body>
</html>
"""
                    )

                # Create static directory and CSS file
                static_dir = os.path.join(app_dir, "static", "css")
                os.makedirs(static_dir, exist_ok=True)

                with open(os.path.join(static_dir, "style.css"), "w") as f:
                    f.write(
                        """body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    color: #333;
}

header, footer {
    background-color: #4a5568;
    color: white;
    text-align: center;
    padding: 1rem;
}

main {
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
}
"""
                    )

                progress.update(advance=40, description="Creating application files...")

                # Create app.py
                with open(os.path.join(project_path, "app.py"), "w") as f:
                    f.write(
                        f"""from {name} import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
"""
                    )

                # Create requirements.txt
                with open(os.path.join(project_path, "requirements.txt"), "w") as f:
                    f.write(
                        """flask==2.3.3
python-dotenv==1.0.0
"""
                    )

                # Create README.md
                with open(os.path.join(project_path, "README.md"), "w") as f:
                    f.write(
                        f"""# {name.capitalize()} Flask Application

A Flask web application generated by DevSynth.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   flask run
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```
"""
                    )

                progress.update(
                    advance=40, description="Creating configuration files..."
                )
            else:
                # For other frameworks, just create a placeholder README
                with open(os.path.join(project_path, "README.md"), "w") as f:
                    f.write(
                        f"""# {name.capitalize()} {framework.capitalize()} Application

A {framework.capitalize()} web application generated by DevSynth.

Note: Full support for {framework} will be implemented in a future version.
"""
                    )
                progress.update(advance=100)

            # Mark task as complete
            progress.complete()

        bridge.print(
            f"[green]✓ Web application generated successfully at: {project_path}[/green]"
        )

        # Show next steps based on the framework
        bridge.print("\n[bold blue]Next Steps:[/bold blue]")

        if framework == "flask":
            bridge.print("1. Create a virtual environment:")
            bridge.print(f"   [green]cd {project_path} && python -m venv venv[/green]")
            bridge.print("2. Activate the virtual environment:")
            bridge.print(
                f"   [green]source venv/bin/activate  # On Windows: venv\\Scripts\\activate[/green]"
            )
            bridge.print("3. Install dependencies:")
            bridge.print(f"   [green]pip install -r requirements.txt[/green]")
            bridge.print("4. Run the application:")
            bridge.print(f"   [green]flask run[/green]")
        else:
            bridge.print(
                f"Support for {framework} will be implemented in a future version."
            )

        bridge.print("\n[bold blue]Access your application:[/bold blue]")
        bridge.print(
            "Open your browser and navigate to: [green]http://localhost:5000[/green]"
        )

    except Exception as err:
        bridge.print(f"[red]✗ Error:[/red] {str(err)}", highlight=False)
        bridge.print(
            "[red]An unexpected error occurred during web application generation.[/red]"
        )

        # Show detailed error information
        import traceback

        bridge.print(
            Panel(
                traceback.format_exc(),
                title="Detailed Error Information",
                border_style="red",
            )
        )


def serve_cmd(
    host: str = "0.0.0.0",
    port: int = 8000,
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Run the DevSynth API server.

    Example:
        `devsynth serve --host 127.0.0.1 --port 8080`
    """
    try:
        configure_logging()
        uvicorn.run("devsynth.api:app", host=host, port=port, log_level="info")
    except Exception as err:  # pragma: no cover - defensive
        bridge.print(f"[red]Error:[/red] {err}", highlight=False)


def dbschema_cmd(
    db_type: str = "sqlite",
    name: str = "database",
    path: str = ".",
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Generate a database schema for the specified database type.

    Example:
        `devsynth dbschema --db-type sqlite --name blog --path ./schema`
    """
    try:
        from rich.prompt import Prompt, Confirm
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.table import Table

        # Show a welcome message for the dbschema command
        bridge.print(
            Panel(
                f"[bold blue]DevSynth Database Schema Generator[/bold blue]\n\n"
                f"This command will generate a database schema for {db_type}.",
                title="Database Schema Generator",
                border_style="blue",
            )
        )

        # Validate and normalize the database type
        db_type = db_type.lower()
        supported_db_types = ["sqlite", "mysql", "postgresql", "mongodb"]

        if db_type not in supported_db_types:
            bridge.print(
                f"[yellow]Warning: '{db_type}' is not a recognized database type.[/yellow]"
            )
            bridge.print(
                f"[yellow]Supported database types: {', '.join(supported_db_types)}[/yellow]"
            )

            # Ask user to select a database type
            db_table = Table(title="Supported Database Types")
            db_table.add_column("Database", style="cyan")
            db_table.add_column("Description")
            db_table.add_column("Type", style="green")

            db_table.add_row("sqlite", "Lightweight disk-based database", "SQL")
            db_table.add_row("mysql", "Popular open-source relational database", "SQL")
            db_table.add_row(
                "postgresql", "Advanced open-source relational database", "SQL"
            )
            db_table.add_row("mongodb", "NoSQL document database", "NoSQL")

            bridge.print(db_table)

            db_type = bridge.prompt(
                "[blue]Select a database type[/blue]",
                choices=supported_db_types,
                default="sqlite",
            )

        # Get schema name if not provided
        if name == "database":
            name = bridge.prompt("[blue]Schema name[/blue]", default="database")

        # Sanitize schema name
        name = name.replace(" ", "_").lower()

        # Get schema path if not provided
        if path == ".":
            path = bridge.prompt("[blue]Schema path[/blue]", default=".")

        # Create full schema path
        schema_path = os.path.join(path, f"{name}_schema")

        # Check if directory already exists
        if os.path.exists(schema_path):
            if not bridge.confirm(
                f"[yellow]Directory {schema_path} already exists. Overwrite?[/yellow]"
            ):
                bridge.print("[yellow]Operation cancelled.[/yellow]")
                return

            # Remove existing directory
            shutil.rmtree(schema_path)

        # Create schema directory
        os.makedirs(schema_path, exist_ok=True)

        # Get entity information
        bridge.print("\n[bold]Entity Information[/bold]")
        bridge.print(
            "Let's define the entities (tables/collections) for your database schema."
        )

        entities = []
        while True:
            entity_name = bridge.prompt(
                "[blue]Entity name[/blue] (or press Enter to finish)"
            )
            if not entity_name:
                break

            # Sanitize entity name
            entity_name = entity_name.replace(" ", "_").lower()

            # Get entity fields
            bridge.print(f"\n[bold]Fields for {entity_name}[/bold]")
            fields = []
            while True:
                field_name = bridge.prompt(
                    "[blue]Field name[/blue] (or press Enter to finish)"
                )
                if not field_name:
                    break

                # Sanitize field name
                field_name = field_name.replace(" ", "_").lower()

                # Get field type
                if db_type in ["sqlite", "mysql", "postgresql"]:
                    field_type_choices = [
                        "integer",
                        "text",
                        "boolean",
                        "float",
                        "date",
                        "datetime",
                        "blob",
                    ]
                else:  # MongoDB
                    field_type_choices = [
                        "string",
                        "number",
                        "boolean",
                        "date",
                        "objectId",
                        "array",
                        "object",
                    ]

                field_type = bridge.prompt(
                    "[blue]Field type[/blue]",
                    choices=field_type_choices,
                    default=field_type_choices[0],
                )

                # Get field constraints
                constraints = []
                if db_type in ["sqlite", "mysql", "postgresql"]:
                    if bridge.confirm(
                        "[blue]Is this field a primary key?[/blue]", default=False
                    ):
                        constraints.append("PRIMARY KEY")
                    if bridge.confirm(
                        "[blue]Is this field required (NOT NULL)?[/blue]", default=False
                    ):
                        constraints.append("NOT NULL")
                    if bridge.confirm(
                        "[blue]Should this field be unique?[/blue]", default=False
                    ):
                        constraints.append("UNIQUE")
                else:  # MongoDB
                    if bridge.confirm(
                        "[blue]Is this field required?[/blue]", default=False
                    ):
                        constraints.append("required: true")
                    if bridge.confirm(
                        "[blue]Should this field be unique?[/blue]", default=False
                    ):
                        constraints.append("unique: true")

                fields.append(
                    {"name": field_name, "type": field_type, "constraints": constraints}
                )

            if fields:
                entities.append({"name": entity_name, "fields": fields})
            else:
                bridge.print(
                    "[yellow]Warning: Entity has no fields and will be skipped.[/yellow]"
                )

        if not entities:
            bridge.print(
                "[yellow]Warning: No entities defined. Creating a sample schema instead.[/yellow]"
            )

            # Create sample entities
            if db_type in ["sqlite", "mysql", "postgresql"]:
                entities = [
                    {
                        "name": "users",
                        "fields": [
                            {
                                "name": "id",
                                "type": "integer",
                                "constraints": ["PRIMARY KEY"],
                            },
                            {
                                "name": "username",
                                "type": "text",
                                "constraints": ["NOT NULL", "UNIQUE"],
                            },
                            {
                                "name": "email",
                                "type": "text",
                                "constraints": ["NOT NULL", "UNIQUE"],
                            },
                            {
                                "name": "password",
                                "type": "text",
                                "constraints": ["NOT NULL"],
                            },
                            {
                                "name": "created_at",
                                "type": "datetime",
                                "constraints": ["NOT NULL"],
                            },
                        ],
                    },
                    {
                        "name": "posts",
                        "fields": [
                            {
                                "name": "id",
                                "type": "integer",
                                "constraints": ["PRIMARY KEY"],
                            },
                            {
                                "name": "user_id",
                                "type": "integer",
                                "constraints": ["NOT NULL"],
                            },
                            {
                                "name": "title",
                                "type": "text",
                                "constraints": ["NOT NULL"],
                            },
                            {
                                "name": "content",
                                "type": "text",
                                "constraints": ["NOT NULL"],
                            },
                            {
                                "name": "created_at",
                                "type": "datetime",
                                "constraints": ["NOT NULL"],
                            },
                        ],
                    },
                ]
            else:  # MongoDB
                entities = [
                    {
                        "name": "users",
                        "fields": [
                            {"name": "_id", "type": "objectId", "constraints": []},
                            {
                                "name": "username",
                                "type": "string",
                                "constraints": ["required: true", "unique: true"],
                            },
                            {
                                "name": "email",
                                "type": "string",
                                "constraints": ["required: true", "unique: true"],
                            },
                            {
                                "name": "password",
                                "type": "string",
                                "constraints": ["required: true"],
                            },
                            {
                                "name": "created_at",
                                "type": "date",
                                "constraints": ["required: true"],
                            },
                        ],
                    },
                    {
                        "name": "posts",
                        "fields": [
                            {"name": "_id", "type": "objectId", "constraints": []},
                            {
                                "name": "user_id",
                                "type": "objectId",
                                "constraints": ["required: true"],
                            },
                            {
                                "name": "title",
                                "type": "string",
                                "constraints": ["required: true"],
                            },
                            {
                                "name": "content",
                                "type": "string",
                                "constraints": ["required: true"],
                            },
                            {
                                "name": "created_at",
                                "type": "date",
                                "constraints": ["required: true"],
                            },
                        ],
                    },
                ]

        # Show progress during generation
        with bridge.create_progress(
            f"Generating {db_type} schema...", total=100
        ) as progress:

            # Generate schema based on database type
            if db_type == "sqlite":
                # Create SQLite schema file
                schema_file = os.path.join(schema_path, f"{name}_schema.sql")
                with open(schema_file, "w") as f:
                    f.write(f"-- SQLite schema for {name}\n\n")

                    for entity in entities:
                        f.write(f"CREATE TABLE {entity['name']} (\n")

                        field_definitions = []
                        for field in entity["fields"]:
                            field_def = f"    {field['name']} {field['type'].upper()}"
                            if field["constraints"]:
                                field_def += f" {' '.join(field['constraints'])}"
                            field_definitions.append(field_def)

                        f.write(",\n".join(field_definitions))
                        f.write("\n);\n\n")

                progress.update(advance=100)

            elif db_type == "mysql":
                # Create MySQL schema file
                schema_file = os.path.join(schema_path, f"{name}_schema.sql")
                with open(schema_file, "w") as f:
                    f.write(f"-- MySQL schema for {name}\n\n")

                    f.write(f"CREATE DATABASE IF NOT EXISTS {name};\n")
                    f.write(f"USE {name};\n\n")

                    for entity in entities:
                        f.write(f"CREATE TABLE {entity['name']} (\n")

                        field_definitions = []
                        for field in entity["fields"]:
                            field_def = f"    {field['name']} {field['type'].upper()}"
                            if field["constraints"]:
                                field_def += f" {' '.join(field['constraints'])}"
                            field_definitions.append(field_def)

                        f.write(",\n".join(field_definitions))
                        f.write("\n);\n\n")

                progress.update(advance=100)

            elif db_type == "postgresql":
                # Create PostgreSQL schema file
                schema_file = os.path.join(schema_path, f"{name}_schema.sql")
                with open(schema_file, "w") as f:
                    f.write(f"-- PostgreSQL schema for {name}\n\n")

                    f.write(f"CREATE SCHEMA IF NOT EXISTS {name};\n\n")

                    for entity in entities:
                        f.write(f"CREATE TABLE {name}.{entity['name']} (\n")

                        field_definitions = []
                        for field in entity["fields"]:
                            # Map types to PostgreSQL types
                            pg_type = field["type"].upper()
                            if pg_type == "INTEGER":
                                pg_type = (
                                    "SERIAL"
                                    if "PRIMARY KEY" in field["constraints"]
                                    else "INTEGER"
                                )
                            elif pg_type == "TEXT":
                                pg_type = "VARCHAR(255)"

                            field_def = f"    {field['name']} {pg_type}"
                            if field["constraints"]:
                                field_def += f" {' '.join(field['constraints'])}"
                            field_definitions.append(field_def)

                        f.write(",\n".join(field_definitions))
                        f.write("\n);\n\n")

                progress.update(advance=100)

            elif db_type == "mongodb":
                # Create MongoDB schema file (using Mongoose schema format)
                schema_file = os.path.join(schema_path, f"{name}_schema.js")
                with open(schema_file, "w") as f:
                    f.write(f"// MongoDB schema for {name} using Mongoose\n\n")

                    f.write("const mongoose = require('mongoose');\n")
                    f.write("const Schema = mongoose.Schema;\n\n")

                    for entity in entities:
                        f.write(f"// {entity['name']} schema\n")
                        f.write(f"const {entity['name']}Schema = new Schema({{\n")

                        field_definitions = []
                        for field in entity["fields"]:
                            # Skip _id field as MongoDB adds it automatically
                            if field["name"] == "_id":
                                continue

                            # Map types to Mongoose types
                            mongoose_type = field["type"]
                            if mongoose_type == "string":
                                mongoose_type = "String"
                            elif mongoose_type == "number":
                                mongoose_type = "Number"
                            elif mongoose_type == "boolean":
                                mongoose_type = "Boolean"
                            elif mongoose_type == "date":
                                mongoose_type = "Date"
                            elif mongoose_type == "objectId":
                                mongoose_type = "Schema.Types.ObjectId"
                            elif mongoose_type == "array":
                                mongoose_type = "[]"
                            elif mongoose_type == "object":
                                mongoose_type = "{}"

                            if field["constraints"]:
                                field_def = f"    {field['name']}: {{\n"
                                field_def += f"        type: {mongoose_type},\n"
                                for constraint in field["constraints"]:
                                    field_def += f"        {constraint},\n"
                                field_def += "    }"
                            else:
                                field_def = f"    {field['name']}: {mongoose_type}"

                            field_definitions.append(field_def)

                        f.write(",\n".join(field_definitions))
                        f.write("\n}, { timestamps: true });\n\n")

                        f.write(
                            f"const {entity['name'].capitalize()} = mongoose.model('{entity['name'].capitalize()}', {entity['name']}Schema);\n\n"
                        )

                    f.write("module.exports = {\n")
                    exports = [
                        f"    {entity['name'].capitalize()}" for entity in entities
                    ]
                    f.write(",\n".join(exports))
                    f.write("\n};\n")

                progress.update(advance=100)

            # Mark task as complete
            progress.complete()

        bridge.print(
            f"[green]✓ Database schema generated successfully at: {schema_path}[/green]"
        )

        # Show next steps based on the database type
        bridge.print("\n[bold blue]Next Steps:[/bold blue]")

        if db_type == "sqlite":
            bridge.print("1. Use the schema to create your SQLite database:")
            bridge.print(f"   [green]sqlite3 {name}.db < {schema_file}[/green]")
        elif db_type == "mysql":
            bridge.print("1. Use the schema to create your MySQL database:")
            bridge.print(f"   [green]mysql -u username -p < {schema_file}[/green]")
        elif db_type == "postgresql":
            bridge.print("1. Use the schema to create your PostgreSQL database:")
            bridge.print(
                f"   [green]psql -U username -d {name} -f {schema_file}[/green]"
            )
        elif db_type == "mongodb":
            bridge.print("1. Install Mongoose in your Node.js project:")
            bridge.print(f"   [green]npm install mongoose[/green]")
            bridge.print("2. Import the schema in your application:")
            bridge.print(
                f"   [green]const {{ {', '.join([entity['name'].capitalize() for entity in entities])} }} = require('./path/to/{name}_schema.js');[/green]"
            )

    except Exception as err:
        bridge.print(f"[red]✗ Error:[/red] {str(err)}", highlight=False)
        bridge.print(
            "[red]An unexpected error occurred during database schema generation.[/red]"
        )

        # Show detailed error information
        import traceback

        bridge.print(
            Panel(
                traceback.format_exc(),
                title="Detailed Error Information",
                border_style="red",
            )
        )


def check_cmd(config_dir: str = "config") -> None:
    """Alias for :func:`doctor_cmd`.

    Example:
        `devsynth check`
    """
    doctor_cmd(config_dir)


def webui_cmd(*, bridge: UXBridge = bridge) -> None:
    """Launch the Streamlit WebUI."""
    try:
        from devsynth.interface.webui import run

        run()
    except Exception as err:  # pragma: no cover - defensive
        bridge.print(f"[red]Error:[/red] {err}")
