"""Sandbox utilities for restricting tool execution."""

from __future__ import annotations

import builtins
import subprocess
from contextlib import ContextDecorator
from functools import wraps
from pathlib import Path
from typing import Any, Callable

# Determine the project root (three levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Sandbox(ContextDecorator):
    """Context manager that restricts file and subprocess access."""

    def __init__(self, *, allow_shell: bool = False) -> None:
        """Initialize the sandbox.

        Args:
            allow_shell: Whether to permit shell command execution.
        """
        self.allow_shell = allow_shell
        self._original_open = builtins.open
        self._original_popen = subprocess.Popen
        self._original_run = subprocess.run

    @staticmethod
    def _in_project(path: Path) -> bool:
        """Return True if the path is within the project root."""
        resolved = path.resolve()
        return PROJECT_ROOT == resolved or PROJECT_ROOT in resolved.parents

    def _safe_open(self, file: str | Path, *args: Any, **kwargs: Any):
        if not self._in_project(Path(file)):
            raise PermissionError("Access outside project directory is not allowed")
        return self._original_open(file, *args, **kwargs)

    def _blocked_popen(self, *args: Any, **kwargs: Any):
        if not self.allow_shell:
            raise PermissionError("Shell commands are not permitted")
        return self._original_popen(*args, **kwargs)

    def _blocked_run(self, *args: Any, **kwargs: Any):
        if not self.allow_shell:
            raise PermissionError("Shell commands are not permitted")
        return self._original_run(*args, **kwargs)

    def __enter__(self):  # pragma: no cover - trivial
        builtins.open = self._safe_open
        subprocess.Popen = self._blocked_popen
        subprocess.run = self._blocked_run
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - trivial
        builtins.open = self._original_open
        subprocess.Popen = self._original_popen
        subprocess.run = self._original_run
        return False


def sandboxed(func: Callable[..., Any], *, allow_shell: bool = False) -> Callable[..., Any]:
    """Return ``func`` wrapped to execute inside a :class:`Sandbox`."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        with Sandbox(allow_shell=allow_shell):
            return func(*args, **kwargs)

    return wrapper
