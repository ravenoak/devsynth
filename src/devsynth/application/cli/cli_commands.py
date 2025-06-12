import os
from typing import Optional, Union, List

from rich.console import Console
from rich.prompt import Confirm
import typer
from pathlib import Path
import importlib.util
import yaml

from ..orchestration.workflow import workflow_manager
import uvicorn
from devsynth.logging_setup import configure_logging
from ..orchestration.adaptive_workflow import adaptive_workflow_manager
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError
from devsynth.config import get_settings
from .commands.edrr_cycle_cmd import edrr_cycle_cmd

logger = DevSynthLogger(__name__)
console = Console()
config_app = typer.Typer(help="Manage configuration settings")


def _check_services() -> bool:
    """Verify required services are available."""
    settings = get_settings()
    messages: List[str] = []

    # Check ChromaDB availability when vector store is enabled
    if settings.vector_store_enabled and settings.memory_store_type == "chromadb":
        if importlib.util.find_spec("chromadb") is None:
            messages.append(
                "ChromaDB support is enabled but the 'chromadb' package is missing."
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
            console.print(f"[red]{msg}[/red]", highlight=False)
        console.print(
            "[yellow]Use 'devsynth config' or edit your project.yaml to update settings.[/yellow]"
        )
        return False

    return True


def _filter_args(args: dict) -> dict:
    """Return a new dict with None values removed."""
    return {k: v for k, v in args.items() if v is not None}


def init_cmd(
    path: str = ".", name: Optional[str] = None, template: Optional[str] = None
) -> None:
    """Initialize a new project."""
    try:
        args = _filter_args({"path": path, "name": name, "template": template})
        result = workflow_manager.execute_command("init", args)
        if result.get("success"):
            console.print(f"[green]Initialized DevSynth project in {path}[/green]")

            # Prompt for optional feature flags
            feature_flags = {
                "code_generation": False,
                "test_generation": False,
                "documentation_generation": False,
                "wsde_collaboration": False,
                "dialectical_reasoning": False,
                "experimental_features": False,
            }

            console.print("\n[bold]Select optional features to enable:[/bold]")
            for flag in feature_flags:
                feature_flags[flag] = Confirm.ask(
                    f"Enable {flag.replace('_', ' ')}?", default=False
                )

            # Create configuration file under .devsynth/project.yaml
            project_root = Path(path)
            devsynth_dir = project_root / ".devsynth"
            devsynth_dir.mkdir(parents=True, exist_ok=True)
            config_path = devsynth_dir / "project.yaml"

            if config_path.exists():
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
            else:
                template_path = (
                    Path(__file__).resolve().parents[4] / "templates" / "project.yaml"
                )
                with open(template_path, "r") as f:
                    config = yaml.safe_load(f) or {}

            if name:
                config["projectName"] = name

            config.setdefault("features", {}).update(feature_flags)

            with open(config_path, "w") as f:
                yaml.safe_dump(config, f)
        else:
            console.print(f"[red]Error:[/red] {result.get('message')}", highlight=False)
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)


def spec_cmd(requirements_file: str = "requirements.md") -> None:
    """Generate specifications from a requirements file."""
    try:
        if not _check_services():
            return
        args = _filter_args({"requirements_file": requirements_file})
        result = workflow_manager.execute_command("spec", args)
        if result.get("success"):
            console.print(
                f"[green]Specifications generated from {requirements_file}.[/green]"
            )
        else:
            console.print(f"[red]Error:[/red] {result.get('message')}", highlight=False)
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)


def test_cmd(spec_file: str = "specs.md") -> None:
    """Generate tests based on specifications."""
    try:
        if not _check_services():
            return
        args = _filter_args({"spec_file": spec_file})
        result = workflow_manager.execute_command("test", args)
        if result.get("success"):
            console.print(f"[green]Tests generated from {spec_file}.[/green]")
        else:
            console.print(f"[red]Error:[/red] {result.get('message')}", highlight=False)
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)


def code_cmd() -> None:
    """Generate implementation code from tests."""
    try:
        if not _check_services():
            return
        result = workflow_manager.execute_command("code", {})
        if result.get("success"):
            console.print("[green]Code generated successfully.[/green]")
        else:
            console.print(f"[red]Error:[/red] {result.get('message')}", highlight=False)
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)


def run_cmd(target: Optional[str] = None) -> None:
    """Run the generated code or a specific target."""
    try:
        result = workflow_manager.execute_command("run", {"target": target})
        if result["success"]:
            if target:
                console.print(f"[green]Executed target: {target}[/green]")
            else:
                console.print(f"[green]Execution complete.[/green]")
        else:
            console.print(f"[red]Error:[/red] {result['message']}", highlight=False)
    except Exception as err:
        console.print(f"[red]Error:[/red] {err}", highlight=False)


@config_app.callback(invoke_without_command=True)
def config_cmd(
    ctx: typer.Context,
    key: Optional[str] = None,
    value: Optional[str] = None,
    list_models: bool = False,
) -> None:
    """View or set configuration options."""
    if ctx.invoked_subcommand is not None:
        return
    try:
        args = {"key": key, "value": value}
        if list_models:
            args["list_models"] = True
        result = workflow_manager.execute_command("config", args)
        if result.get("success"):
            if key and value:
                console.print(f"[green]Configuration updated: {key} = {value}[/green]")
            elif key:
                console.print(f"[blue]{key}:[/blue] {result.get('value')}")
            else:
                console.print(f"[blue]DevSynth Configuration:[/blue]")
                for k, v in result.get("config", {}).items():
                    console.print(f"  [yellow]{k}:[/yellow] {v}")
        else:
            console.print(f"[red]Error:[/red] {result.get('message')}", highlight=False)
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)


@config_app.command("enable-feature")
def enable_feature_cmd(name: str) -> None:
    """Enable a feature flag in .devsynth/project.yaml."""
    try:
        project_file = Path(".devsynth") / "project.yaml"
        if not project_file.exists():
            console.print("[red]Error:[/red] Project configuration not found", highlight=False)
            return
        with open(project_file, "r") as f:
            data = yaml.safe_load(f) or {}
        features = data.setdefault("features", {})
        features[name] = True
        with open(project_file, "w") as f:
            yaml.safe_dump(data, f)
        console.print(f"[green]Feature '{name}' enabled.[/green]")
    except Exception as err:
        console.print(f"[red]Error:[/red] {err}", highlight=False)


def adaptive_cmd(path: Optional[str] = None) -> None:
    """
    Execute an adaptive workflow based on the current project state.

    This command analyzes the current project state, determines the optimal workflow,
    and suggests appropriate next steps.

    Args:
        path: Path to the project root directory (default: current directory)
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.markdown import Markdown

        console = Console()

        # Show a welcome message for the adaptive command
        console.print(
            Panel(
                "[bold blue]DevSynth Adaptive Workflow[/bold blue]\n\n"
                "This command will analyze your project state, determine the optimal workflow, "
                "and suggest appropriate next steps.",
                title="Adaptive Workflow",
                border_style="blue",
            )
        )

        # Set the project path
        project_path = path or os.getcwd()

        # Execute the adaptive workflow
        result = adaptive_workflow_manager.execute_adaptive_workflow(project_path)

        if result.get("success", False):
            # Display the workflow information
            console.print(f"[green]Workflow:[/green] {result['workflow']}")
            console.print(f"[green]Entry Point:[/green] {result['entry_point']}")

            # Display the suggestions
            console.print("\n[bold]Suggested Next Steps:[/bold]")

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

            console.print(table)

            # Display the message
            console.print(f"\n[green]{result['message']}[/green]")
        else:
            console.print(f"[red]Error:[/red] {result.get('message', 'Unknown error')}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


def analyze_cmd(input_file: Optional[str] = None, interactive: bool = False) -> None:
    """Analyze requirements from a file or interactively."""
    try:
        if not _check_services():
            return
        args = _filter_args({"input": input_file, "interactive": interactive})
        result = workflow_manager.execute_command("analyze", args)
        if result.get("success"):
            console.print("[green]Requirements analysis completed.[/green]")
        else:
            console.print(f"[red]Error:[/red] {result.get('message')}", highlight=False)
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)


def webapp_cmd(framework: str = "flask", name: str = "webapp", path: str = ".") -> None:
    """Generate a web application with the specified framework."""
    try:
        from rich.prompt import Prompt, Confirm
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.table import Table

        # Show a welcome message for the webapp command
        console.print(
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
            console.print(
                f"[yellow]Warning: '{framework}' is not a recognized framework.[/yellow]"
            )
            console.print(
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

            console.print(framework_table)

            framework = Prompt.ask(
                "[blue]Select a framework[/blue]",
                choices=supported_frameworks,
                default="flask",
            )

        # Get project name if not provided
        if name == "webapp":
            name = Prompt.ask("[blue]Project name[/blue]", default="webapp")

        # Sanitize project name
        name = name.replace(" ", "_").lower()

        # Get project path if not provided
        if path == ".":
            path = Prompt.ask("[blue]Project path[/blue]", default=".")

        # Create full project path
        project_path = os.path.join(path, name)

        # Check if directory already exists
        if os.path.exists(project_path):
            if not Confirm.ask(
                f"[yellow]Directory {project_path} already exists. Overwrite?[/yellow]"
            ):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return

            # Remove existing directory
            shutil.rmtree(project_path)

        # Create project directory
        os.makedirs(project_path, exist_ok=True)

        # Show progress during generation
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            console=console,
        ) as progress:
            # Create task for project generation
            task = progress.add_task(
                f"[blue]Generating {framework} project...", total=100
            )

            # Generate Flask project (for now, we'll only implement Flask)
            if framework == "flask":
                # Create app directory
                app_dir = os.path.join(project_path, name)
                os.makedirs(app_dir, exist_ok=True)

                progress.update(
                    task, advance=20, description="Creating Flask application..."
                )

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

                progress.update(
                    task, advance=40, description="Creating application files..."
                )

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
                    task, advance=40, description="Creating configuration files..."
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
                progress.update(task, advance=100)

            # Mark task as complete
            progress.update(task, completed=True)

        console.print(
            f"[green]✓ Web application generated successfully at: {project_path}[/green]"
        )

        # Show next steps based on the framework
        console.print("\n[bold blue]Next Steps:[/bold blue]")

        if framework == "flask":
            console.print("1. Create a virtual environment:")
            console.print(f"   [green]cd {project_path} && python -m venv venv[/green]")
            console.print("2. Activate the virtual environment:")
            console.print(
                f"   [green]source venv/bin/activate  # On Windows: venv\\Scripts\\activate[/green]"
            )
            console.print("3. Install dependencies:")
            console.print(f"   [green]pip install -r requirements.txt[/green]")
            console.print("4. Run the application:")
            console.print(f"   [green]flask run[/green]")
        else:
            console.print(
                f"Support for {framework} will be implemented in a future version."
            )

        console.print("\n[bold blue]Access your application:[/bold blue]")
        console.print(
            "Open your browser and navigate to: [green]http://localhost:5000[/green]"
        )

    except Exception as err:
        console.print(f"[red]✗ Error:[/red] {str(err)}", highlight=False)
        console.print(
            "[red]An unexpected error occurred during web application generation.[/red]"
        )

        # Show detailed error information
        import traceback

        console.print(
            Panel(
                traceback.format_exc(),
                title="Detailed Error Information",
                border_style="red",
            )
        )


def serve_cmd(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the DevSynth API server."""
    try:
        configure_logging()
        uvicorn.run("devsynth.api:app", host=host, port=port, log_level="info")
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)


def dbschema_cmd(
    db_type: str = "sqlite", name: str = "database", path: str = "."
) -> None:
    """Generate a database schema for the specified database type."""
    try:
        from rich.prompt import Prompt, Confirm
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.table import Table

        # Show a welcome message for the dbschema command
        console.print(
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
            console.print(
                f"[yellow]Warning: '{db_type}' is not a recognized database type.[/yellow]"
            )
            console.print(
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

            console.print(db_table)

            db_type = Prompt.ask(
                "[blue]Select a database type[/blue]",
                choices=supported_db_types,
                default="sqlite",
            )

        # Get schema name if not provided
        if name == "database":
            name = Prompt.ask("[blue]Schema name[/blue]", default="database")

        # Sanitize schema name
        name = name.replace(" ", "_").lower()

        # Get schema path if not provided
        if path == ".":
            path = Prompt.ask("[blue]Schema path[/blue]", default=".")

        # Create full schema path
        schema_path = os.path.join(path, f"{name}_schema")

        # Check if directory already exists
        if os.path.exists(schema_path):
            if not Confirm.ask(
                f"[yellow]Directory {schema_path} already exists. Overwrite?[/yellow]"
            ):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return

            # Remove existing directory
            shutil.rmtree(schema_path)

        # Create schema directory
        os.makedirs(schema_path, exist_ok=True)

        # Get entity information
        console.print("\n[bold]Entity Information[/bold]")
        console.print(
            "Let's define the entities (tables/collections) for your database schema."
        )

        entities = []
        while True:
            entity_name = Prompt.ask(
                "[blue]Entity name[/blue] (or press Enter to finish)"
            )
            if not entity_name:
                break

            # Sanitize entity name
            entity_name = entity_name.replace(" ", "_").lower()

            # Get entity fields
            console.print(f"\n[bold]Fields for {entity_name}[/bold]")
            fields = []
            while True:
                field_name = Prompt.ask(
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

                field_type = Prompt.ask(
                    "[blue]Field type[/blue]",
                    choices=field_type_choices,
                    default=field_type_choices[0],
                )

                # Get field constraints
                constraints = []
                if db_type in ["sqlite", "mysql", "postgresql"]:
                    if Confirm.ask(
                        "[blue]Is this field a primary key?[/blue]", default=False
                    ):
                        constraints.append("PRIMARY KEY")
                    if Confirm.ask(
                        "[blue]Is this field required (NOT NULL)?[/blue]", default=False
                    ):
                        constraints.append("NOT NULL")
                    if Confirm.ask(
                        "[blue]Should this field be unique?[/blue]", default=False
                    ):
                        constraints.append("UNIQUE")
                else:  # MongoDB
                    if Confirm.ask(
                        "[blue]Is this field required?[/blue]", default=False
                    ):
                        constraints.append("required: true")
                    if Confirm.ask(
                        "[blue]Should this field be unique?[/blue]", default=False
                    ):
                        constraints.append("unique: true")

                fields.append(
                    {"name": field_name, "type": field_type, "constraints": constraints}
                )

            if fields:
                entities.append({"name": entity_name, "fields": fields})
            else:
                console.print(
                    "[yellow]Warning: Entity has no fields and will be skipped.[/yellow]"
                )

        if not entities:
            console.print(
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            console=console,
        ) as progress:
            # Create task for schema generation
            task = progress.add_task(f"[blue]Generating {db_type} schema...", total=100)

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

                progress.update(task, advance=100)

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

                progress.update(task, advance=100)

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

                progress.update(task, advance=100)

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

                progress.update(task, advance=100)

            # Mark task as complete
            progress.update(task, completed=True)

        console.print(
            f"[green]✓ Database schema generated successfully at: {schema_path}[/green]"
        )

        # Show next steps based on the database type
        console.print("\n[bold blue]Next Steps:[/bold blue]")

        if db_type == "sqlite":
            console.print("1. Use the schema to create your SQLite database:")
            console.print(f"   [green]sqlite3 {name}.db < {schema_file}[/green]")
        elif db_type == "mysql":
            console.print("1. Use the schema to create your MySQL database:")
            console.print(f"   [green]mysql -u username -p < {schema_file}[/green]")
        elif db_type == "postgresql":
            console.print("1. Use the schema to create your PostgreSQL database:")
            console.print(
                f"   [green]psql -U username -d {name} -f {schema_file}[/green]"
            )
        elif db_type == "mongodb":
            console.print("1. Install Mongoose in your Node.js project:")
            console.print(f"   [green]npm install mongoose[/green]")
            console.print("2. Import the schema in your application:")
            console.print(
                f"   [green]const {{ {', '.join([entity['name'].capitalize() for entity in entities])} }} = require('./path/to/{name}_schema.js');[/green]"
            )

    except Exception as err:
        console.print(f"[red]✗ Error:[/red] {str(err)}", highlight=False)
        console.print(
            "[red]An unexpected error occurred during database schema generation.[/red]"
        )

        # Show detailed error information
        import traceback

        console.print(
            Panel(
                traceback.format_exc(),
                title="Detailed Error Information",
                border_style="red",
            )
        )
