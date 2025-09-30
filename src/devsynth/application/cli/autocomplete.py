"""Autocomplete utilities and shell-completion helpers for the DevSynth CLI."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import typer
from click.core import Command
from click.shell_completion import ShellComplete, get_completion_class
from typer.main import get_command as get_typer_command

from devsynth.application.cli.models import TyperAutocomplete

# List of all available commands
COMMANDS: list[str] = [
    "init",
    "spec",
    "test",
    "code",
    "run-pipeline",
    "config",
    "gather",
    "inspect",
    "refactor",
    "webapp",
    "serve",
    "dbschema",
    "check",
    "doctor",
    "edrr-cycle",
    "webui",
    "completion",
]

# Command descriptions for help text
COMMAND_DESCRIPTIONS: dict[str, str] = {
    "init": "Initialize a new project",
    "spec": "Generate specifications from requirements",
    "test": "Generate tests from specifications",
    "code": "Generate code from tests",
    "run-pipeline": "Run the generated code or a specific target",
    "config": "View or set configuration options",
    "gather": "Interactively gather project goals, constraints and priority",
    "inspect": "Inspect requirements from a file or interactively",
    "refactor": "Execute a refactor workflow based on the current project state",
    "webapp": "Generate a web application with the specified framework",
    "serve": "Run the DevSynth API server",
    "dbschema": "Generate a database schema for the specified database type",
    "check": "Alias for doctor command",
    "doctor": "Run diagnostics on the current environment",
    "edrr-cycle": "Run an EDRR cycle",
    "webui": "Launch the Streamlit WebUI",
    "completion": "Generate or install shell completion scripts",
}

# Command examples for help text
COMMAND_EXAMPLES: dict[str, list[str]] = {
    "init": [
        "devsynth init",
        "devsynth init --wizard",
    ],
    "spec": [
        "devsynth spec",
        "devsynth spec --requirements-file custom_requirements.md",
    ],
    "test": [
        "devsynth test",
        "devsynth test --spec-file custom_specs.md",
    ],
    "code": [
        "devsynth code",
    ],
    "run-pipeline": [
        "devsynth run-pipeline",
        "devsynth run-pipeline --target unit-tests",
    ],
    "config": [
        "devsynth config",
        "devsynth config --key model --value gpt-4",
        "devsynth config --list-models",
    ],
    "gather": [
        "devsynth gather",
        "devsynth gather --output-file custom_requirements.yaml",
    ],
    "inspect": [
        "devsynth inspect --input requirements.txt",
        "devsynth inspect --interactive",
    ],
    "refactor": [
        "devsynth refactor",
        "devsynth refactor --path ./my-project",
    ],
    "webapp": [
        "devsynth webapp",
        "devsynth webapp --framework flask --name myapp --path ./apps",
    ],
    "serve": [
        "devsynth serve",
        "devsynth serve --host 127.0.0.1 --port 8080",
    ],
    "dbschema": [
        "devsynth dbschema",
        "devsynth dbschema --db-type sqlite --name blog --path ./schema",
    ],
    "doctor": [
        "devsynth doctor",
        "devsynth doctor --config-dir custom_config",
    ],
    "check": [
        "devsynth check",
        "devsynth check --quick",
    ],
    "edrr-cycle": [
        "devsynth edrr-cycle",
        "devsynth edrr-cycle --manifest manifest.yaml --auto",
    ],
    "webui": [
        "devsynth webui",
    ],
    "completion": [
        "devsynth completion --install",
        "devsynth completion --shell zsh --output devsynth.zsh",
    ],
}


def get_completions(incomplete: str) -> list[str]:
    """Get command completion suggestions based on the incomplete input.

    Args:
        incomplete: The incomplete command string

    Returns:
        A list of command suggestions that match the incomplete string
    """
    return [cmd for cmd in COMMANDS if cmd.startswith(incomplete)]


def complete_command(incomplete: str) -> str:
    """Complete a command based on the incomplete input.

    Args:
        incomplete: The incomplete command string

    Returns:
        The completed command if there's a unique match, otherwise the incomplete string
    """
    matches = get_completions(incomplete)
    if len(matches) == 1:
        return matches[0]
    return incomplete


def command_autocomplete(ctx: typer.Context, incomplete: str) -> list[str]:
    """Provide autocompletion for DevSynth commands.

    This function is used by Typer to provide command autocompletion.

    Args:
        ctx: The Typer context
        incomplete: The incomplete command string

    Returns:
        A list of command suggestions that match the incomplete string
    """
    return get_completions(incomplete)


def file_path_autocomplete(ctx: typer.Context, incomplete: str) -> list[str]:
    """Provide autocompletion for file paths.

    Args:
        ctx: The Typer context
        incomplete: The incomplete file path

    Returns:
        A list of file path suggestions that match the incomplete string
    """
    # Get the current directory
    current_dir = Path.cwd()

    # If incomplete is empty, return all files and directories in the current directory
    if not incomplete:
        return [str(p) for p in current_dir.iterdir()]

    # If incomplete contains a path separator, get the parent directory
    if "/" in incomplete or "\\" in incomplete:
        parent_dir = Path(incomplete).parent
        if not parent_dir.is_absolute():
            parent_dir = current_dir / parent_dir

        # Get the incomplete filename
        incomplete_name = Path(incomplete).name

        # Return all files and directories in the parent directory that match the incomplete name
        return [
            str(p) for p in parent_dir.iterdir() if p.name.startswith(incomplete_name)
        ]

    # Return all files and directories in the current directory that match the incomplete name
    return [str(p) for p in current_dir.iterdir() if p.name.startswith(incomplete)]


def get_command_help(command: str) -> str:
    """Get detailed help text for a command.

    Args:
        command: The command name

    Returns:
        Detailed help text for the command, including description and examples
    """
    description = COMMAND_DESCRIPTIONS.get(command, "No description available")
    examples = COMMAND_EXAMPLES.get(command, [])

    help_text = f"Command: {command}\n\n"
    help_text += f"Description:\n  {description}\n\n"

    if examples:
        help_text += "Examples:\n"
        for example in examples:
            help_text += f"  {example}\n"

    return help_text


def get_all_commands_help() -> str:
    """Get help text for all available commands.

    Returns:
        Help text for all available commands
    """
    help_text = "Available Commands:\n\n"

    for command in sorted(COMMANDS):
        description = COMMAND_DESCRIPTIONS.get(command, "No description available")
        help_text += f"{command:15} {description}\n"

    help_text += (
        "\nUse 'devsynth <command> --help' for more information about a command."
    )

    return help_text


def _load_click_command() -> Command:
    """Return the Click command generated by the Typer application."""

    from devsynth.adapters.cli.typer_adapter import build_app

    app = build_app()
    return get_typer_command(app)


def _build_shell_complete(shell: str, command: Command) -> ShellComplete:
    """Instantiate the Click ``ShellComplete`` helper for ``shell``."""

    completion_cls = get_completion_class(shell)
    ctx_args: MutableMapping[str, Any] = {}
    return completion_cls(command, ctx_args, "devsynth", "_DEVSYNTH_COMPLETE")


def generate_completion_script(
    shell: str = "bash", install: bool = False, path: Path | None = None
) -> str:
    """Generate a shell completion script for the DevSynth CLI."""

    command = _load_click_command()
    completion = _build_shell_complete(shell, command)
    script = completion.source()

    if install:
        target = path or Path.home() / f".devsynth-completion.{shell}"
        target.write_text(script)
        return str(target)

    return script


_COMMAND_AUTOCOMPLETE: TyperAutocomplete = command_autocomplete
_FILE_PATH_AUTOCOMPLETE: TyperAutocomplete = file_path_autocomplete


__all__ = [
    "COMMANDS",
    "COMMAND_DESCRIPTIONS",
    "COMMAND_EXAMPLES",
    "get_completions",
    "complete_command",
    "command_autocomplete",
    "file_path_autocomplete",
    "get_command_help",
    "get_all_commands_help",
    "generate_completion_script",
]
