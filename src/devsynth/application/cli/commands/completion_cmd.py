"""Shell completion command."""

from __future__ import annotations

from pathlib import Path

import typer
from typer import completion as typer_completion

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


def completion_cmd(
    shell: str | None = None,
    install: bool = False,
    path: Path | None = None,
    *,
    bridge: CLIUXBridge | None = None,
) -> None:
    """Generate or install shell completion scripts."""

    bridge = bridge or CLIUXBridge()
    progress = bridge.create_progress("Generating completion script", total=2)

    try:
        shell_name = shell or "bash"

        # Validate the shell
        if shell_name not in ["bash", "zsh", "fish"]:
            bridge.display_result(
                f"Unsupported shell: {shell_name}. Supported shells are: bash, zsh, fish",
                message_type="error",
            )
            raise typer.Exit(1)

        prog_name = "devsynth"
        complete_var = f"_{prog_name}_COMPLETE".replace("-", "_").upper()
        script = typer_completion.get_completion_script(
            prog_name=prog_name,
            complete_var=complete_var,
            shell=shell_name,  # nosec B604: shell arg specifies completion target
        )
        progress.update(status="script generated", advance=1)

        if install:
            if path is None:
                _, target_path = typer_completion.install(
                    shell=shell_name,
                    prog_name=prog_name,
                    complete_var=complete_var,  # nosec B604: shell arg specifies completion target
                )
            else:
                target_path = path
                target_path.write_text(script)
            bridge.show_completion(str(target_path))
        else:
            bridge.show_completion(script)

        progress.update(status="done", advance=1)
        progress.complete()
    except (FileNotFoundError, PermissionError, OSError) as e:
        progress.complete()
        bridge.display_result(
            f"Failed to generate completion script: {str(e)}",
            message_type="error",
        )
        raise typer.Exit(1)
    except Exception as e:
        progress.complete()
        bridge.display_result(f"An error occurred: {str(e)}", message_type="error")
        raise typer.Exit(1)
