import importlib.util
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import typer
from rich.console import Console

from devsynth.config import config_key_autocomplete as loader_autocomplete
from devsynth.config import get_settings
from devsynth.config.loader import ConfigModel, _find_config_path, save_config
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.core import workflows
from devsynth.core.workflows import (
    filter_args,
    gather_requirements,
    generate_code,
    generate_specs,
    generate_tests,
    init_project,
    inspect_requirements,
    run_pipeline,
)
from devsynth.exceptions import DevSynthError
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger, configure_logging, get_logger

from ..orchestration.refactor_workflow import refactor_workflow_manager
from .commands.doctor_cmd import doctor_cmd as _doctor_impl
from .commands.edrr_cycle_cmd import edrr_cycle_cmd
from .commands.run_tests_cmd import run_tests_cmd
from .errors import handle_error_enhanced

# Optional Dear PyGUI interface support
try:  # pragma: no cover - optional dependency handling
    from devsynth.interface.dpg_ui import run as run_dpg_ui
except Exception:  # pragma: no cover - defensive
    run_dpg_ui = None  # type: ignore

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def _resolve_bridge(b: Optional[UXBridge]) -> UXBridge:
    """Return the provided bridge or fall back to the module default."""
    return b if b is not None else bridge


def _env_flag(name: str) -> Optional[bool]:
    """Return boolean value for ``name`` if set, otherwise ``None``."""
    val = os.environ.get(name)
    if val is None:
        return None
    return val.lower() in {"1", "true", "yes"}


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


def _handle_error(
    bridge: UXBridge, error: Union[Exception, Dict[str, Any], str]
) -> None:
    """Handle errors consistently across all commands.

    Args:
        bridge: The UX bridge to use for displaying messages
        error: The error to handle, can be an Exception, a result dict, or a string
    """
    logger = get_logger("cli_commands")

    # Common error patterns and their solutions
    error_solutions = {
        "file not found": "Make sure the file exists and the path is correct. Use absolute paths if needed.",
        "permission denied": "Check file permissions. You may need to run with elevated privileges or change file permissions.",
        "invalid format": "Verify the file format matches what the command expects (e.g., YAML, JSON, Markdown).",
        "invalid parameter": "Check the command parameters. Use --help to see valid options.",
        "connection error": "Check your internet connection. If using a proxy, verify your proxy settings.",
        "timeout": "The operation timed out. Try again or increase the timeout setting in your configuration.",
        "api key": "Ensure your API key is correctly set in the environment or configuration file.",
        "out of memory": "The operation requires more memory. Try closing other applications or increasing available memory.",
        "configuration": "There may be an issue with your configuration. Run 'devsynth doctor' to diagnose configuration problems.",
    }

    # Documentation links for different error types
    doc_links = {
        "file": "[link=https://devsynth.ai/docs/file-handling]File Handling Documentation[/link]",
        "parameter": "[link=https://devsynth.ai/docs/command-parameters]Command Parameters Documentation[/link]",
        "configuration": "[link=https://devsynth.ai/docs/configuration]Configuration Documentation[/link]",
        "api": "[link=https://devsynth.ai/docs/api-integration]API Integration Documentation[/link]",
        "network": "[link=https://devsynth.ai/docs/network-troubleshooting]Network Troubleshooting[/link]",
        "memory": "[link=https://devsynth.ai/docs/performance]Performance Optimization[/link]",
    }

    if isinstance(error, Exception):
        # Log the error for debugging with full traceback
        logger.error(f"Command error: {str(error)}", exc_info=True)

        # Get the error message
        error_msg = str(error)

        # Create a panel with the error details
        bridge.display_result(
            f"[bold red]Error:[/bold red] {error_msg}", highlight=False
        )

        # Find relevant solutions based on error message
        solutions = []
        relevant_docs = []

        # Check for known error patterns
        for pattern, solution in error_solutions.items():
            if pattern.lower() in error_msg.lower():
                solutions.append(solution)

        # Add documentation links based on error type
        for keyword, link in doc_links.items():
            if keyword.lower() in error_msg.lower():
                relevant_docs.append(link)

        # Display solutions if found
        if solutions:
            bridge.display_result(
                "[bold yellow]Suggested solutions:[/bold yellow]", highlight=False
            )
            for i, solution in enumerate(solutions, 1):
                bridge.display_result(
                    f"  [yellow]{i}.[/yellow] {solution}", highlight=False
                )

        # Display documentation links if found
        if relevant_docs:
            bridge.display_result(
                "[bold cyan]Relevant documentation:[/bold cyan]", highlight=False
            )
            for doc in relevant_docs:
                bridge.display_result(f"  • {doc}", highlight=False)

        # Always provide a general help tip
        bridge.display_result(
            "[dim]Run 'devsynth help' or 'devsynth <command> --help' for more information.[/dim]",
            highlight=False,
        )

    elif isinstance(error, dict):
        # Handle result dict with error message
        message = error.get("message", "Unknown error")
        code = error.get("code", "")
        details = error.get("details", "")

        # Log the error
        logger.error(f"Command error: {message} (Code: {code})")

        # Display a structured error message
        bridge.display_result(
            f"[bold red]Error {code if code else ''}:[/bold red] {message}",
            highlight=False,
        )

        if details:
            bridge.display_result(
                f"[yellow]Details:[/yellow] {details}", highlight=False
            )

        # Find relevant solutions based on error message
        solutions = []
        relevant_docs = []

        # Check for known error patterns
        for pattern, solution in error_solutions.items():
            if pattern.lower() in message.lower() or (
                details and pattern.lower() in details.lower()
            ):
                solutions.append(solution)

        # Add documentation links based on error type
        for keyword, link in doc_links.items():
            if keyword.lower() in message.lower() or (
                details and keyword.lower() in details.lower()
            ):
                relevant_docs.append(link)

        # Display solutions if found
        if solutions:
            bridge.display_result(
                "[bold yellow]Suggested solutions:[/bold yellow]", highlight=False
            )
            for i, solution in enumerate(solutions, 1):
                bridge.display_result(
                    f"  [yellow]{i}.[/yellow] {solution}", highlight=False
                )

        # Display documentation links if found
        if relevant_docs:
            bridge.display_result(
                "[bold cyan]Relevant documentation:[/bold cyan]", highlight=False
            )
            for doc in relevant_docs:
                bridge.display_result(f"  • {doc}", highlight=False)

        # Always provide a general help tip
        bridge.display_result(
            "[dim]Run 'devsynth help' or 'devsynth <command> --help' for more information.[/dim]",
            highlight=False,
        )
    else:
        # Handle string error message
        logger.error(f"Command error: {error}")

        # Display a user-friendly error message
        bridge.display_result(f"[bold red]Error:[/bold red] {error}", highlight=False)

        # Find relevant solutions based on error message
        solutions = []
        relevant_docs = []

        # Check for known error patterns
        for pattern, solution in error_solutions.items():
            if pattern.lower() in str(error).lower():
                solutions.append(solution)

        # Add documentation links based on error type
        for keyword, link in doc_links.items():
            if keyword.lower() in str(error).lower():
                relevant_docs.append(link)

        # Display solutions if found
        if solutions:
            bridge.display_result(
                "[bold yellow]Suggested solutions:[/bold yellow]", highlight=False
            )
            for i, solution in enumerate(solutions, 1):
                bridge.display_result(
                    f"  [yellow]{i}.[/yellow] {solution}", highlight=False
                )

        # Display documentation links if found
        if relevant_docs:
            bridge.display_result(
                "[bold cyan]Relevant documentation:[/bold cyan]", highlight=False
            )
            for doc in relevant_docs:
                bridge.display_result(f"  • {doc}", highlight=False)

        # Always provide a general help tip
        bridge.display_result(
            "[dim]Run 'devsynth help' or 'devsynth <command> --help' for more information.[/dim]",
            highlight=False,
        )


def _validate_file_path(path: str, must_exist: bool = True) -> Optional[str]:
    """Validate a file path.

    Args:
        path: The file path to validate
        must_exist: Whether the file must exist

    Returns:
        An error message if validation fails, None otherwise
    """
    if not path:
        return "File path cannot be empty"

    file_path = Path(path)
    if must_exist and not file_path.exists():
        return f"File '{path}' does not exist"

    return None


def config_key_autocomplete(ctx: typer.Context, incomplete: str):
    """Provide autocompletion for configuration keys."""
    return loader_autocomplete(ctx, incomplete)


def init_cmd(
    wizard: bool = False,
    *,
    root: Optional[str] = None,
    language: Optional[str] = None,
    goals: Optional[str] = None,
    memory_backend: Optional[str] = None,
    offline_mode: Optional[bool] = None,
    features: Optional[Dict[str, bool]] = None,
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Initialize a new project.

    This command sets up a new DevSynth project with the specified configuration.
    It will create a configuration file in the project directory.

    Args:
        wizard: If True, run the interactive setup wizard for a guided setup
        bridge: Optional UX bridge for interaction

    Examples:
        Initialize a project with interactive prompts:
        ```
        devsynth init
        ```

        Initialize a project with the guided setup wizard:
        ```
        devsynth init --wizard
        ```
    """

    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        if wizard:
            from .setup_wizard import SetupWizard

            SetupWizard(bridge).run()
            return

        config = UnifiedConfigLoader.load().config
        if _find_config_path(Path.cwd()) is not None:
            bridge.display_result("[yellow]Project already initialized[/yellow]")
            return

        root = root or os.environ.get("DEVSYNTH_INIT_ROOT")
        if root is None:
            root = bridge.ask_question(
                "Project root directory?", default=str(Path.cwd())
            )

        # Validate root directory
        root_path = Path(root)
        if not root_path.exists():
            if auto_confirm or bridge.confirm_choice(
                f"Directory '{root}' does not exist. Create it?", default=True
            ):
                root_path.mkdir(parents=True, exist_ok=True)
            else:
                bridge.display_result("[yellow]Initialization cancelled[/yellow]")
                return

        language = language or os.environ.get("DEVSYNTH_INIT_LANGUAGE")
        if language is None:
            language = bridge.ask_question("Primary language?", default="python")

        goals = goals or os.environ.get("DEVSYNTH_INIT_GOALS")
        if goals is None:
            goals = bridge.ask_question("Project goals?", default="")

        memory_backend = memory_backend or os.environ.get(
            "DEVSYNTH_INIT_MEMORY_BACKEND"
        )
        if memory_backend is None:
            memory_backend = bridge.ask_question(
                "Select memory backend",
                choices=["memory", "file", "kuzu", "chromadb"],
                default="memory",
            )

        if offline_mode is None:
            env_offline = _env_flag("DEVSYNTH_INIT_OFFLINE_MODE")
            if env_offline is not None:
                offline_mode = env_offline
            else:
                offline_mode = bridge.confirm_choice(
                    "Enable offline mode?", default=False
                )

        # Configure features
        if features is None:
            env_feats = os.environ.get("DEVSYNTH_INIT_FEATURES")
            if env_feats:
                features = {f.strip(): True for f in env_feats.split(";") if f.strip()}
            else:
                features = config.features or {}
        for feat in [
            "wsde_collaboration",
            "dialectical_reasoning",
            "code_generation",
            "test_generation",
            "documentation_generation",
            "experimental_features",
        ]:
            if feat in features:
                features[feat] = bool(features[feat])
            elif auto_confirm:
                features[feat] = True
            else:
                features[feat] = bridge.confirm_choice(
                    f"Enable {feat.replace('_', ' ')}?",
                    default=features.get(feat, False),
                )

        # Confirm and save
        proceed = auto_confirm if auto_confirm is not None else None
        if proceed is None:
            proceed = bridge.confirm_choice(
                "Proceed with initialization?", default=True
            )
        if not proceed:
            bridge.display_result("[yellow]Initialization cancelled[/yellow]")
            return

        config.project_root = root
        config.language = language
        config.goals = goals
        config.memory_store_type = memory_backend
        config.offline_mode = offline_mode
        config.features = features

        try:
            save_config(
                ConfigModel(**config.as_dict()),
                use_pyproject=(Path("pyproject.toml").exists()),
            )
            # Trigger workflow manager so tests can verify initialization logic
            init_project(
                root=root,
                structure=config.structure,
                language=language,
                goals=goals,
                memory_backend=memory_backend,
                offline_mode=offline_mode,
                features=features,
            )
            bridge.display_result(
                "[green]Initialization complete[/green]", highlight=True
            )
        except Exception as save_err:
            console = Console()
            handle_error_enhanced(bridge, save_err, console)
    except Exception as err:  # pragma: no cover - defensive
        console = Console()
        handle_error_enhanced(bridge, err, console)


def spec_cmd(
    requirements_file: str = "requirements.md",
    *,
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Generate specifications from a requirements file.

    This command analyzes a requirements file and generates detailed specifications
    that can be used for implementation.

    Args:
        requirements_file: Path to the requirements file (Markdown format)
        bridge: Optional UX bridge for interaction

    Examples:
        Generate specifications from the default requirements file:
        ```
        devsynth spec
        ```

        Generate specifications from a custom requirements file:
        ```
        devsynth spec --requirements-file custom_requirements.md
        ```
    """
    from rich.console import Console

    from .progress import create_enhanced_progress, run_with_progress

    console = Console()
    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Validate input file
        error = _validate_file_path(requirements_file)
        if error:
            bridge.display_result(f"[yellow]{error}[/yellow]")
            if auto_confirm or bridge.confirm_choice(
                f"Create empty '{requirements_file}' file?", default=False
            ):
                Path(requirements_file).touch()
                bridge.display_result(
                    f"[green]Created empty file: {requirements_file}[/green]"
                )
            else:
                return

        # Define subtasks for the specification generation process
        subtasks = [
            {"name": "Analyzing requirements", "total": 30},
            {"name": "Extracting key concepts", "total": 20},
            {"name": "Generating specifications", "total": 40},
            {"name": "Validating output", "total": 10},
        ]

        # Create a function to run with progress tracking
        def generate_specs_with_progress():
            # Create progress indicator for the main task
            progress = create_enhanced_progress(
                console, "Generating specifications", 100
            )

            try:
                # Add subtasks
                for subtask in subtasks:
                    progress.add_subtask(subtask["name"], subtask["total"])

                # Update progress for first subtask
                progress.update_subtask(
                    "Analyzing requirements",
                    advance=15,
                    description="Parsing requirements file",
                )

                # Generate specifications
                args = filter_args({"requirements_file": requirements_file})

                # Update progress for first subtask completion
                progress.update_subtask("Analyzing requirements", advance=15)
                progress.complete_subtask("Analyzing requirements")

                # Update progress for second subtask
                progress.update_subtask("Extracting key concepts", advance=20)
                progress.complete_subtask("Extracting key concepts")

                # Update progress for third subtask
                progress.update_subtask(
                    "Generating specifications",
                    advance=20,
                    description="Creating specification structure",
                )
                progress.update_subtask(
                    "Generating specifications",
                    advance=20,
                    description="Writing specification details",
                )

                # Call the actual generate_specs function
                result = generate_specs(**args)

                # Update progress for remaining subtasks
                progress.complete_subtask("Generating specifications")
                progress.update_subtask("Validating output", advance=10)
                progress.complete_subtask("Validating output")

                # Update main task progress
                progress.update(advance=100)

                return result
            finally:
                # Ensure progress is completed even if an error occurs
                progress.complete()

        # Run the specification generation with progress tracking
        result = generate_specs_with_progress()

        # Handle result
        if result.get("success"):
            output_file = result.get("output_file", "specs.md")

            # Create a summary table of what was generated
            from rich.table import Table

            summary_table = Table(title="Specification Generation Summary")
            summary_table.add_column("Item", style="cyan")
            summary_table.add_column("Value", style="green")

            summary_table.add_row("Input File", requirements_file)
            summary_table.add_row("Output File", output_file)
            if "stats" in result:
                stats = result["stats"]
                for key, value in stats.items():
                    summary_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(summary_table)

            bridge.display_result(
                f"[green]Specifications successfully generated from {requirements_file}.[/green]",
                highlight=True,
            )

            # Show next steps
            bridge.display_result("\n[bold]Next Steps:[/bold]")
            bridge.display_result(
                f"1. Review the generated specifications in {output_file}"
            )
            bridge.display_result("2. Generate tests: devsynth test")
            bridge.display_result("3. Generate code: devsynth code")
        else:
            handle_error_enhanced(bridge, result, console)
    except Exception as err:  # pragma: no cover - defensive
        handle_error_enhanced(bridge, err, console)


def test_cmd(
    spec_file: str = "specs.md",
    *,
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Generate tests based on specifications.

    This command analyzes a specifications file and generates test cases
    that can be used to validate the implementation.

    Args:
        spec_file: Path to the specifications file (Markdown format)
        bridge: Optional UX bridge for interaction

    Examples:
        Generate tests from the default specifications file:
        ```
        devsynth test
        ```

        Generate tests from a custom specifications file:
        ```
        devsynth test --spec-file custom_specs.md
        ```
    """
    from rich.console import Console
    from rich.table import Table

    from .progress import create_enhanced_progress

    console = Console()
    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Validate input file
        error = _validate_file_path(spec_file)
        if error:
            bridge.display_result(f"[yellow]{error}[/yellow]")
            if auto_confirm or bridge.confirm_choice(
                f"Run 'devsynth spec' to generate {spec_file}?", default=True
            ):
                spec_cmd(bridge=bridge, auto_confirm=auto_confirm)
            else:
                return

        # Define subtasks for the test generation process
        subtasks = [
            {"name": "Analyzing specifications", "total": 25},
            {"name": "Identifying test cases", "total": 25},
            {"name": "Generating unit tests", "total": 20},
            {"name": "Generating integration tests", "total": 15},
            {"name": "Generating behavior tests", "total": 15},
        ]

        # Create a function to run with progress tracking
        def generate_tests_with_progress():
            # Create progress indicator for the main task
            progress = create_enhanced_progress(console, "Generating tests", 100)

            try:
                # Add subtasks
                for subtask in subtasks:
                    progress.add_subtask(subtask["name"], subtask["total"])

                # Update progress for first subtask
                progress.update_subtask(
                    "Analyzing specifications",
                    advance=15,
                    description="Parsing specification file",
                )

                # Generate tests
                args = filter_args({"spec_file": spec_file})

                # Update progress for first subtask completion
                progress.update_subtask("Analyzing specifications", advance=10)
                progress.complete_subtask("Analyzing specifications")

                # Update progress for second subtask
                progress.update_subtask(
                    "Identifying test cases",
                    advance=15,
                    description="Extracting testable requirements",
                )
                progress.update_subtask(
                    "Identifying test cases",
                    advance=10,
                    description="Defining test boundaries",
                )
                progress.complete_subtask("Identifying test cases")

                # Update progress for remaining subtasks
                progress.update_subtask("Generating unit tests", advance=20)
                progress.complete_subtask("Generating unit tests")

                progress.update_subtask("Generating integration tests", advance=15)
                progress.complete_subtask("Generating integration tests")

                progress.update_subtask("Generating behavior tests", advance=15)
                progress.complete_subtask("Generating behavior tests")

                # Call the actual generate_tests function
                result = generate_tests(**args)

                # Update main task progress
                progress.update(advance=100)

                return result
            finally:
                # Ensure progress is completed even if an error occurs
                progress.complete()

        # Run the test generation with progress tracking
        result = generate_tests_with_progress()

        # Handle result
        if result.get("success"):
            output_dir = result.get("output_dir", "tests")

            # Create a summary table of what was generated
            summary_table = Table(title="Test Generation Summary")
            summary_table.add_column("Test Type", style="cyan")
            summary_table.add_column("Location", style="blue")

            # Add rows for each test type
            test_types = {
                "Unit Tests": f"{output_dir}/unit",
                "Integration Tests": f"{output_dir}/integration",
                "Behavior Tests": f"{output_dir}/behavior",
            }

            for test_type, location in test_types.items():
                summary_table.add_row(test_type, location)

            console.print(summary_table)

            bridge.display_result(
                f"[green]Tests successfully generated from {spec_file}.[/green]",
                highlight=True,
            )

            # Show next steps
            bridge.display_result("\n[bold]Next Steps:[/bold]")
            bridge.display_result("1. Review the generated tests")
            bridge.display_result("2. Generate code: devsynth code")
            bridge.display_result("3. Run tests: devsynth run-pipeline")
        else:
            handle_error_enhanced(bridge, result, console)
    except Exception as err:  # pragma: no cover - defensive
        handle_error_enhanced(bridge, err, console)


def code_cmd(
    *, auto_confirm: Optional[bool] = None, bridge: Optional[UXBridge] = None
) -> None:
    """Generate implementation code from tests.

    This command analyzes the test files and generates implementation code
    that satisfies the test requirements.

    Args:
        bridge: Optional UX bridge for interaction

    Examples:
        Generate implementation code:
        ```
        devsynth code
        ```
    """
    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Check if tests directory exists
        tests_dir = Path("tests")
        if not tests_dir.exists() or not any(tests_dir.iterdir()):
            bridge.display_result(
                "[yellow]No tests found in 'tests' directory.[/yellow]"
            )
            if auto_confirm or bridge.confirm_choice(
                "Run 'devsynth test' to generate tests?", default=True
            ):
                test_cmd(bridge=bridge, auto_confirm=auto_confirm)
            else:
                return

        # Generate code
        bridge.display_result(
            "[blue]Generating implementation code from tests...[/blue]"
        )
        result = generate_code()

        # Handle result
        if result.get("success"):
            output_dir = result.get("output_dir", "src")
            bridge.display_result("[green]Code generated successfully.[/green]")
            bridge.display_result(f"[blue]Code saved to directory: {output_dir}[/blue]")
        else:
            console = Console()
            handle_error_enhanced(bridge, result, console)
    except Exception as err:  # pragma: no cover - defensive
        console = Console()
        handle_error_enhanced(bridge, err, console)


def run_pipeline_cmd(
    target: Optional[str] = None,
    report: Optional[Dict[str, Any]] = None,
    *,
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Run the generated code or a specific target.

    This command executes the generated code or a specific target, such as unit tests.
    It can also persist a report with the results.

    Args:
        target: Execution target (e.g. "unit-tests", "integration-tests", "all")
        report: Optional report data that should be persisted with pipeline results
        bridge: Optional UX bridge for interaction

    Examples:
        Run the default pipeline:
        ```
        devsynth run-pipeline
        ```

        Run a specific target:
        ```
        devsynth run-pipeline --target unit-tests
        ```
    """
    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Validate target if provided
        valid_targets = ["unit-tests", "integration-tests", "behavior-tests", "all"]
        if target and target not in valid_targets:
            bridge.display_result(
                f"[yellow]Warning: '{target}' is not a standard target. Valid targets are: {', '.join(valid_targets)}[/yellow]"
            )
            if not (
                auto_confirm
                or bridge.confirm_choice(
                    f"Continue with target '{target}'?", default=True
                )
            ):
                return

        # Execute command
        bridge.display_result(
            f"[blue]Running {'target: ' + target if target else 'default pipeline'}...[/blue]"
        )
        result = workflows.execute_command(
            "run-pipeline", {"target": target, "report": report}
        )

        # Handle result
        if result.get("success"):
            if target:
                bridge.display_result(
                    f"[green]Successfully executed target: {target}[/green]"
                )
            else:
                bridge.display_result(f"[green]Pipeline execution complete.[/green]")

            # Display additional result information if available
            if "output" in result:
                bridge.display_result(f"[blue]Output:[/blue]\n{result['output']}")
        else:
            console = Console()
            handle_error_enhanced(bridge, result, console)
    except Exception as err:  # pragma: no cover - defensive
        console = Console()
        handle_error_enhanced(bridge, err, console)


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

    This command allows you to view or modify DevSynth configuration settings.
    Without arguments, it displays all configuration settings.
    With a key, it displays the value for that key.
    With a key and value, it updates the configuration.

    Args:
        key: Configuration key to view or set
        value: Value to set for the specified key
        list_models: List available LLM models
        ctx: Typer context
        bridge: Optional UX bridge for interaction

    Examples:
        View all configuration settings:
        ```
        devsynth config
        ```

        View a specific configuration setting:
        ```
        devsynth config --key model
        ```

        Update a configuration setting:
        ```
        devsynth config --key model --value gpt-4
        ```

        List available LLM models:
        ```
        devsynth config --list-models
        ```
    """
    bridge = _resolve_bridge(bridge)

    # Handle Typer's OptionInfo objects
    if isinstance(key, typer.models.OptionInfo):
        key = None
    if isinstance(value, typer.models.OptionInfo):
        value = None

    # Skip if a subcommand is being invoked
    if ctx is not None and ctx.invoked_subcommand is not None:
        return

    try:
        # Load configuration
        config = UnifiedConfigLoader.load().config

        # Prepare arguments
        args = {"key": key, "value": value}
        if list_models:
            args["list_models"] = True

        # Execute command
        result = workflows.execute_command("config", args)

        # Handle result
        if result.get("success"):
            if key and value:
                # Update configuration
                try:
                    setattr(config, key, value)
                    save_config(
                        ConfigModel(**config.as_dict()),
                        use_pyproject=(Path("pyproject.toml").exists()),
                    )
                    bridge.display_result(
                        f"[green]Configuration updated: {key} = {value}[/green]"
                    )
                except Exception as save_err:
                    console = Console()
                    handle_error_enhanced(bridge, save_err, console)
            elif key:
                # Display specific configuration value
                bridge.display_result(f"[blue]{key}:[/blue] {result.get('value')}")
            elif list_models:
                # Display available models
                bridge.display_result(f"[blue]Available LLM Models:[/blue]")
                for model in result.get("models", []):
                    bridge.display_result(f"  [yellow]{model}[/yellow]")
            else:
                # Display all configuration settings
                bridge.display_result(f"[blue]DevSynth Configuration:[/blue]")
                for k, v in result.get("config", {}).items():
                    bridge.display_result(f"  [yellow]{k}:[/yellow] {v}")
        else:
            console = Console()
            handle_error_enhanced(bridge, result, console)
    except Exception as err:  # pragma: no cover - defensive
        console = Console()
        handle_error_enhanced(bridge, err, console)


@config_app.command("enable-feature")
def enable_feature_cmd(name: str, *, bridge: Optional[UXBridge] = None) -> None:
    """Enable a feature flag in the project configuration.

    Example:
        `devsynth config enable-feature code_generation`
    """
    bridge = _resolve_bridge(bridge)
    try:
        config = UnifiedConfigLoader.load().config
        features = config.features or {}
        features[name] = True
        config.features = features
        save_config(
            ConfigModel(**config.as_dict()),
            use_pyproject=(Path("pyproject.toml").exists()),
        )

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
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.table import Table

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
        result = refactor_workflow_manager.execute_refactor_workflow(project_path)

        if result.get("success", False):
            # Display the workflow information
            bridge.display_result(f"[green]Workflow:[/green] {result['workflow']}")
            bridge.display_result(
                f"[green]Entry Point:[/green] {result['entry_point']}"
            )

            # Display the suggestions
            bridge.display_result("\n[bold]Suggested Next Steps:[/bold]")

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
            bridge.display_result(f"\n[green]{result['message']}[/green]")
        else:
            bridge.display_result(
                f"[red]Error:[/red] {result.get('message', 'Unknown error')}"
            )
    except Exception as e:
        bridge.display_result(f"[red]Error:[/red] {str(e)}")


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
    force: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Generate a web application with the specified framework.

    Example:
        `devsynth webapp --framework flask --name myapp --path ./apps`
    """
    try:
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
            raise ValueError(
                f"Unsupported framework '{framework}'. Supported: {', '.join(supported_frameworks)}"
            )

        # Sanitize project name
        name = name.replace(" ", "_").lower()

        # Create full project path
        project_path = os.path.join(path, name)

        # Check if directory already exists
        if os.path.exists(project_path):
            if not force:
                bridge.display_result(
                    f"[yellow]Directory {project_path} already exists. Use --force to overwrite.[/yellow]"
                )
                return
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

        bridge.display_result(
            f"[green]✓ Web application generated successfully at: {project_path}[/green]"
        )

        # Show next steps based on the framework
        bridge.display_result("\n[bold blue]Next Steps:[/bold blue]")

        if framework == "flask":
            bridge.display_result("1. Create a virtual environment:")
            bridge.display_result(
                f"   [green]cd {project_path} && python -m venv venv[/green]"
            )
            bridge.display_result("2. Activate the virtual environment:")
            bridge.display_result(
                f"   [green]source venv/bin/activate  # On Windows: venv\\Scripts\\activate[/green]"
            )
            bridge.display_result("3. Install dependencies:")
            bridge.display_result(f"   [green]pip install -r requirements.txt[/green]")
            bridge.display_result("4. Run the application:")
            bridge.display_result(f"   [green]flask run[/green]")
        else:
            bridge.display_result(
                f"Support for {framework} will be implemented in a future version."
            )

        bridge.display_result("\n[bold blue]Access your application:[/bold blue]")
        bridge.display_result(
            "Open your browser and navigate to: [green]http://localhost:5000[/green]"
        )

    except Exception as err:
        bridge.display_result(f"[red]✗ Error:[/red] {str(err)}", highlight=False)
        bridge.display_result(
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
        import uvicorn

        uvicorn.run("devsynth.api:app", host=host, port=port, log_level="info")
    except ImportError:  # pragma: no cover - optional dependency
        bridge.display_result(
            "[red]Serve command requires the 'uvicorn' package. Install it with 'pip install uvicorn' or use the dev extras.[/red]",
            highlight=False,
        )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


def dbschema_cmd(
    db_type: str = "sqlite",
    name: str = "database",
    path: str = ".",
    force: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Generate a database schema for the specified database type."""
    try:
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.table import Table

        bridge.print(
            Panel(
                f"[bold blue]DevSynth Database Schema Generator[/bold blue]\n\n"
                f"This command will generate a database schema for {db_type}.",
                title="Database Schema Generator",
                border_style="blue",
            )
        )

        db_type = db_type.lower()
        supported_db_types = ["sqlite", "mysql", "postgresql", "mongodb"]
        if db_type not in supported_db_types:
            raise ValueError(
                f"Unsupported database type '{db_type}'. Supported: {', '.join(supported_db_types)}"
            )

        name = name.replace(" ", "_").lower()
        schema_path = os.path.join(path, f"{name}_schema")

        if os.path.exists(schema_path):
            if not force:
                bridge.display_result(
                    f"[yellow]Directory {schema_path} already exists. Use --force to overwrite.[/yellow]"
                )
                return
            shutil.rmtree(schema_path)

        os.makedirs(schema_path, exist_ok=True)

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
                        {"name": "title", "type": "text", "constraints": ["NOT NULL"]},
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
        else:
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

        with bridge.create_progress(
            f"Generating {db_type} schema...", total=100
        ) as progress:
            if db_type == "sqlite":
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
                schema_file = os.path.join(schema_path, f"{name}_schema.sql")
                with open(schema_file, "w") as f:
                    f.write(f"-- PostgreSQL schema for {name}\n\n")
                    f.write(f"CREATE SCHEMA IF NOT EXISTS {name};\n\n")
                    for entity in entities:
                        f.write(f"CREATE TABLE {name}.{entity['name']} (\n")
                        field_definitions = []
                        for field in entity["fields"]:
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
            else:
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
                            if field["name"] == "_id":
                                continue
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
            progress.complete()

        bridge.display_result(
            f"[green]\u2713 Database schema generated successfully at: {schema_path}[/green]"
        )

        bridge.display_result("\n[bold blue]Next Steps:[/bold blue]")
        if db_type == "sqlite":
            bridge.display_result("1. Use the schema to create your SQLite database:")
            bridge.display_result(
                f"   [green]sqlite3 {name}.db < {schema_file}[/green]"
            )
        elif db_type == "mysql":
            bridge.display_result("1. Use the schema to create your MySQL database:")
            bridge.display_result(
                f"   [green]mysql -u username -p < {schema_file}[/green]"
            )
        elif db_type == "postgresql":
            bridge.display_result(
                "1. Use the schema to create your PostgreSQL database:"
            )
            bridge.display_result(
                f"   [green]psql -U username -d {name} -f {schema_file}[/green]"
            )
        elif db_type == "mongodb":
            bridge.display_result("1. Install Mongoose in your Node.js project:")
            bridge.display_result(f"   [green]npm install mongoose[/green]")
            bridge.display_result("2. Import the schema in your application:")
            bridge.display_result(
                f"   [green]const {{ {', '.join([entity['name'].capitalize() for entity in entities])} }} = require('./path/to/{name}_schema.js');[/green]"
            )

    except Exception as err:
        bridge.display_result(f"[red]\u2717 Error:[/red] {str(err)}", highlight=False)
        bridge.display_result(
            "[red]An unexpected error occurred during database schema generation.[/red]"
        )

        import traceback

        bridge.print(
            Panel(
                traceback.format_exc(),
                title="Detailed Error Information",
                border_style="red",
            )
        )


def doctor_cmd(
    config_dir: str = "config",
    quick: bool = typer.Option(False, "--quick", help="Run quick tests"),
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Validate environment configuration files."""

    _doctor_impl(config_dir=config_dir, quick=quick, bridge=_resolve_bridge(bridge))


def check_cmd(config_dir: str = "config", quick: bool = False) -> None:
    """Alias for :func:`doctor_cmd`.

    Example:
        `devsynth check`
    """
    doctor_cmd(config_dir=config_dir, quick=quick)


def webui_cmd(*, bridge: UXBridge = bridge) -> None:
    """Launch the Streamlit WebUI."""
    try:
        from devsynth.interface.webui import run

        run()
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}")


def dpg_cmd(*, bridge: UXBridge = bridge) -> None:
    """Launch the Dear PyGUI interface."""
    try:
        if run_dpg_ui is None:
            raise ImportError("Dear PyGUI interface is unavailable")
        run_dpg_ui()
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}")
