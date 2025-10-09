#!/usr/bin/env python3
"""Verify Poetry post-install invariants for DevSynth."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class VerificationError(RuntimeError):
    """Raised when verification or repair steps fail."""


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_TYPER_VERSION = "0.17.4"


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def emit_process_output(
    proc: subprocess.CompletedProcess[str],
    *,
    label: str,
) -> None:
    if proc.stdout:
        sys.stderr.write(f"[{label}] stdout:\n{proc.stdout}")
        if not proc.stdout.endswith("\n"):
            sys.stderr.write("\n")
    if proc.stderr:
        sys.stderr.write(f"[{label}] stderr:\n{proc.stderr}")
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")


def ensure_poetry_env() -> Path:
    proc = run_command(["poetry", "env", "info", "--path"])
    if proc.returncode != 0:
        sys.stderr.write(
            "[post-install] 'poetry env info --path' failed with exit code"
            f" {proc.returncode}.\n"
        )
        if proc.stdout:
            sys.stderr.write(proc.stdout)
            if not proc.stdout.endswith("\n"):
                sys.stderr.write("\n")
        if proc.stderr:
            sys.stderr.write(proc.stderr)
            if not proc.stderr.endswith("\n"):
                sys.stderr.write("\n")
        raise SystemExit(proc.returncode or 1)

    path_str = proc.stdout.strip()
    if not path_str:
        sys.stderr.write("[post-install] poetry did not return a virtualenv path.\n")
        raise SystemExit(1)

    return Path(path_str)


def run_cli_help() -> subprocess.CompletedProcess[str]:
    return run_command(["poetry", "run", "devsynth", "--help"])


def run_module_help() -> subprocess.CompletedProcess[str]:
    return run_command(["poetry", "run", "python", "-m", "devsynth", "--help"])


def repair_devsynth_install() -> list[tuple[str, subprocess.CompletedProcess[str]]]:
    steps: list[tuple[str, subprocess.CompletedProcess[str]]] = []
    steps.append(
        (
            "devsynth-repair",
            run_command(["poetry", "run", "pip", "install", "--force-reinstall", "."]),
        )
    )
    if steps[-1][1].returncode == 0:
        steps.append(
            (
                "typer-repair",
                run_command(
                    [
                        "poetry",
                        "run",
                        "pip",
                        "install",
                        "--force-reinstall",
                        f"typer=={CLI_TYPER_VERSION}",
                    ]
                ),
            )
        )
    return steps


def ensure_devsynth_cli(venv_path: Path) -> None:
    devsynth_executable = venv_path / "bin" / "devsynth"

    def executable_exists() -> bool:
        return devsynth_executable.is_file()

    cli_proc: subprocess.CompletedProcess[str] | None = None
    module_proc: subprocess.CompletedProcess[str] | None = None

    if executable_exists():
        cli_proc = run_cli_help()
        if cli_proc.returncode == 0:
            return

    reasons: list[str] = []
    if not executable_exists():
        reasons.append(f"devsynth executable not found at {devsynth_executable}")
    elif cli_proc and cli_proc.returncode != 0:
        reasons.append(
            "'poetry run devsynth --help' exited with code " f"{cli_proc.returncode}"
        )

    if cli_proc and cli_proc.returncode != 0:
        emit_process_output(cli_proc, label="devsynth-cli-help")

    module_proc = run_module_help()
    if module_proc.returncode != 0:
        reasons.append(
            "'poetry run python -m devsynth --help' exited with code "
            f"{module_proc.returncode}"
        )
        emit_process_output(module_proc, label="devsynth-module-help")

    if not reasons:
        reasons.append("unknown verification failure")

    sys.stderr.write(
        "[post-install] CLI verification failed; attempting repair: "
        + "; ".join(reasons)
        + "\n"
    )

    repair_steps = repair_devsynth_install()
    for label, proc in repair_steps:
        if proc.returncode != 0:
            emit_process_output(proc, label=label)
            raise VerificationError(
                f"[post-install] Repair attempt '{label}' failed with exit code {proc.returncode}"
            )

    # Re-verify after repair
    if not executable_exists():
        raise VerificationError(
            f"[post-install] devsynth executable still missing at {devsynth_executable} after repair"
        )

    cli_proc = run_cli_help()
    if cli_proc.returncode != 0:
        emit_process_output(cli_proc, label="devsynth-cli-help-after-repair")
        module_proc = run_module_help()
        if module_proc.returncode != 0:
            emit_process_output(module_proc, label="devsynth-module-help-after-repair")
        raise VerificationError(
            "[post-install] 'poetry run devsynth --help' still failing after repair"
        )

    module_proc = run_module_help()
    if module_proc.returncode != 0:
        emit_process_output(module_proc, label="devsynth-module-help-after-repair")
        raise VerificationError(
            "[post-install] 'python -m devsynth --help' failing after repair"
        )


def main() -> int:
    venv_path = ensure_poetry_env()
    print(f"[post-install] poetry virtualenv: {venv_path}")
    try:
        ensure_devsynth_cli(venv_path)
    except VerificationError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    print("[post-install] devsynth CLI is available via 'poetry run devsynth --help'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
