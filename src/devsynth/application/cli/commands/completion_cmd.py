"""Shell completion command for DevSynth CLI.

This module provides a command to generate or install shell completion scripts
for the DevSynth CLI.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.enhanced_error_handler import improved_error_handler
from devsynth.interface.progress_utils import run_with_progress
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def get_completion_script_path(shell: str) -> Path:
    """Get the path to the completion script for the specified shell.

    Args:
        shell: The shell to get the completion script for (bash, zsh, fish)

    Returns:
        The path to the completion script
    """
    # Get the path to the devsynth package
    devsynth_path = Path(__file__).parent.parent.parent.parent.parent

    # Get the path to the completion script
    script_name = f"devsynth-completion.{shell}"
    script_path = devsynth_path / "scripts" / "completions" / script_name

    return script_path


def get_shell_config_path(shell: str) -> Path:
    """Get the path to the shell configuration file.

    Args:
        shell: The shell to get the configuration file for (bash, zsh, fish)

    Returns:
        The path to the shell configuration file
    """
    home = Path.home()

    if shell == "bash":
        # Check for .bashrc or .bash_profile
        if (home / ".bashrc").exists():
            return home / ".bashrc"
        elif (home / ".bash_profile").exists():
            return home / ".bash_profile"
        else:
            return home / ".bashrc"  # Default to .bashrc
    elif shell == "zsh":
        return home / ".zshrc"
    elif shell == "fish":
        return home / ".config" / "fish" / "config.fish"
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def get_completion_install_path(shell: str) -> Path:
    """Get the path where the completion script should be installed.

    Args:
        shell: The shell to get the installation path for (bash, zsh, fish)

    Returns:
        The path where the completion script should be installed
    """
    home = Path.home()

    if shell == "bash":
        # Check for common bash completion directories
        if os.path.exists("/etc/bash_completion.d"):
            return Path("/etc/bash_completion.d") / "devsynth"
        elif os.path.exists(f"{home}/.local/share/bash-completion/completions"):
            return Path(f"{home}/.local/share/bash-completion/completions") / "devsynth"
        else:
            # Try to get the bash-completion directory from Homebrew
            try:
                result = subprocess.run(
                    ["brew", "--prefix"], capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    brew_prefix = result.stdout.strip()
                    return Path(f"{brew_prefix}/etc/bash_completion.d") / "devsynth"
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

            # Default to user's home directory
            return home / ".bash_completion.d" / "devsynth"
    elif shell == "zsh":
        # Check for common zsh completion directories
        if os.path.exists(f"{home}/.zsh/completions"):
            return Path(f"{home}/.zsh/completions") / "_devsynth"
        else:
            # Create the directory if it doesn't exist
            zsh_completions_dir = home / ".zsh" / "completions"
            zsh_completions_dir.mkdir(parents=True, exist_ok=True)
            return zsh_completions_dir / "_devsynth"
    elif shell == "fish":
        # Check for common fish completion directories
        fish_completions_dir = home / ".config" / "fish" / "completions"
        fish_completions_dir.mkdir(parents=True, exist_ok=True)
        return fish_completions_dir / "devsynth.fish"
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def detect_shell() -> str:
    """Detect the current shell.

    Returns:
        The detected shell (bash, zsh, fish) or None if the shell couldn't be detected
    """
    # Check the SHELL environment variable
    shell_path = os.environ.get("SHELL", "")
    shell_name = os.path.basename(shell_path)

    if "bash" in shell_name:
        return "bash"
    elif "zsh" in shell_name:
        return "zsh"
    elif "fish" in shell_name:
        return "fish"
    else:
        # Try to detect the shell from the parent process
        try:
            import psutil

            parent = psutil.Process(os.getppid())
            parent_name = parent.name()

            if "bash" in parent_name:
                return "bash"
            elif "zsh" in parent_name:
                return "zsh"
            elif "fish" in parent_name:
                return "fish"
        except (ImportError, psutil.Error):
            pass

    # Default to bash if we couldn't detect the shell
    return "bash"


def generate_completion_script(shell: str, output_path: Optional[str] = None) -> str:
    """Generate a shell completion script for the specified shell.

    Args:
        shell: The shell to generate the completion script for (bash, zsh, fish)
        output_path: Optional path to write the completion script to

    Returns:
        The path to the generated completion script
    """
    # Get the path to the completion script
    script_path = get_completion_script_path(shell)

    if not script_path.exists():
        raise FileNotFoundError(f"Completion script not found: {script_path}")

    # If output_path is provided, copy the script to that location
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(script_path, output_path)
        return str(output_path)

    return str(script_path)


def install_completion_script(shell: str) -> str:
    """Install the shell completion script for the specified shell.

    Args:
        shell: The shell to install the completion script for (bash, zsh, fish)

    Returns:
        The path to the installed completion script
    """
    # Get the path to the completion script
    script_path = get_completion_script_path(shell)

    if not script_path.exists():
        raise FileNotFoundError(f"Completion script not found: {script_path}")

    # Get the path where the completion script should be installed
    install_path = get_completion_install_path(shell)

    # Create the parent directory if it doesn't exist
    install_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy the script to the installation path
    shutil.copy2(script_path, install_path)

    # Get the shell configuration file
    config_path = get_shell_config_path(shell)

    # Add the necessary configuration to the shell configuration file
    with open(config_path, "r") as f:
        config_content = f.read()

    if shell == "bash":
        # Check if the completion script is already sourced
        if f"source {install_path}" not in config_content:
            with open(config_path, "a") as f:
                f.write(f"\n# DevSynth shell completion\nsource {install_path}\n")
    elif shell == "zsh":
        # Check if the completions directory is already in fpath
        if f"fpath=({install_path.parent}" not in config_content:
            with open(config_path, "a") as f:
                f.write(
                    f"\n# DevSynth shell completion\nfpath=({install_path.parent} $fpath)\nautoload -U compinit\ncompinit\n"
                )
    elif shell == "fish":
        # Fish automatically loads completions from ~/.config/fish/completions
        pass

    return str(install_path)


def completion_cmd(
    shell: Optional[str] = None,
    install: bool = False,
    output: Optional[str] = None,
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Generate or install shell completion scripts for the DevSynth CLI.

    This command generates or installs shell completion scripts for the DevSynth CLI,
    making it easier to use the CLI by providing tab completion for commands and options.

    Examples:
        Generate a completion script for the current shell:
        `devsynth completion`

        Generate a completion script for a specific shell:
        `devsynth completion --shell bash`

        Install the completion script for the current shell:
        `devsynth completion --install`

        Generate a completion script and save it to a specific location:
        `devsynth completion --output /path/to/completion.sh`

    Args:
        shell: The shell to generate the completion script for (bash, zsh, fish)
        install: Whether to install the completion script
        output: Path to write the completion script to
        bridge: UX bridge for output. If not provided, the default CLI bridge will be used.
    """
    # Use the provided bridge or the global default bridge
    ux_bridge = bridge if bridge is not None else globals()["bridge"]

    try:
        # If shell is not provided, detect the current shell
        if not shell:
            shell = detect_shell()
            ux_bridge.display_result(f"Detected shell: {shell}", message_type="info")

        # Validate the shell
        if shell not in ["bash", "zsh", "fish"]:
            ux_bridge.display_result(
                f"Unsupported shell: {shell}. Supported shells are: bash, zsh, fish",
                message_type="error",
            )
            return

        if install:
            # Install the completion script
            try:
                install_path = run_with_progress(
                    "Installing completion script",
                    lambda: install_completion_script(shell),
                    ux_bridge,
                    total=1,
                )
                ux_bridge.display_result(
                    f"Shell completion script installed to: {install_path}",
                    message_type="success",
                )

                # Provide instructions for activating the completion
                if shell == "bash":
                    ux_bridge.display_result(
                        "To activate the completion, restart your shell or run:\n"
                        f"source {install_path}",
                        message_type="info",
                    )
                elif shell == "zsh":
                    ux_bridge.display_result(
                        "To activate the completion, restart your shell or run:\n"
                        "autoload -U compinit\n"
                        "compinit",
                        message_type="info",
                    )
                elif shell == "fish":
                    ux_bridge.display_result(
                        "Completion script installed. Fish will automatically load it.",
                        message_type="info",
                    )
            except (FileNotFoundError, PermissionError, OSError) as e:
                # Use the improved error handler for better error messages
                improved_error_handler.format_error(e)
                ux_bridge.display_result(
                    f"Failed to install completion script: {str(e)}",
                    message_type="error",
                )
        else:
            # Generate the completion script
            try:
                script_path = run_with_progress(
                    "Generating completion script",
                    lambda: generate_completion_script(shell, output),
                    ux_bridge,
                    total=1,
                )

                if output:
                    ux_bridge.display_result(
                        f"Shell completion script generated at: {script_path}",
                        message_type="success",
                    )
                else:
                    # Display the script content
                    with open(script_path, "r") as f:
                        script_content = f.read()

                    ux_bridge.display_result(
                        f"Shell completion script for {shell}:\n\n{script_content}",
                        message_type="info",
                    )

                # Provide instructions for using the completion script
                if shell == "bash":
                    ux_bridge.display_result(
                        "To use this completion script, add the following to your ~/.bashrc or ~/.bash_profile:\n"
                        f"source {script_path}",
                        message_type="info",
                    )
                elif shell == "zsh":
                    ux_bridge.display_result(
                        "To use this completion script, add the following to your ~/.zshrc:\n"
                        f"fpath=({os.path.dirname(script_path)} $fpath)\n"
                        "autoload -U compinit\n"
                        "compinit",
                        message_type="info",
                    )
                elif shell == "fish":
                    ux_bridge.display_result(
                        "To use this completion script, copy it to ~/.config/fish/completions/devsynth.fish",
                        message_type="info",
                    )
            except (FileNotFoundError, PermissionError, OSError) as e:
                # Use the improved error handler for better error messages
                improved_error_handler.format_error(e)
                ux_bridge.display_result(
                    f"Failed to generate completion script: {str(e)}",
                    message_type="error",
                )
    except Exception as e:
        # Use the improved error handler for better error messages
        improved_error_handler.format_error(e)
        ux_bridge.display_result(f"An error occurred: {str(e)}", message_type="error")
