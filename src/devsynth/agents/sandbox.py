"""Sandbox utilities for restricting tool execution."""

from __future__ import annotations

import builtins
import subprocess
from collections.abc import Callable
from contextlib import ContextDecorator
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, ParamSpec, TypeVar, cast

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
        self._original_open: Callable[..., Any] = cast(
            Callable[..., Any], builtins.open
        )
        self._original_popen: Callable[..., subprocess.Popen[Any]] = cast(
            Callable[..., subprocess.Popen[Any]], subprocess.Popen
        )
        self._original_run: Callable[..., subprocess.CompletedProcess[Any]] = cast(
            Callable[..., subprocess.CompletedProcess[Any]], subprocess.run
        )

    @staticmethod
    def _in_project(path: Path) -> bool:
        """Return True if the path is within the project root."""
        resolved = path.resolve()
        return PROJECT_ROOT == resolved or PROJECT_ROOT in resolved.parents

    def _safe_open(self, file: str | Path, *args: Any, **kwargs: Any) -> Any:
        if not self._in_project(Path(file)):
            raise PermissionError("Access outside project directory is not allowed")
        return self._original_open(file, *args, **kwargs)

    def _blocked_popen(self, *args: Any, **kwargs: Any) -> subprocess.Popen[Any]:
        if not self.allow_shell:
            raise PermissionError("Shell commands are not permitted")
        return self._original_popen(*args, **kwargs)

    def _blocked_run(
        self, *args: Any, **kwargs: Any
    ) -> subprocess.CompletedProcess[Any]:
        if not self.allow_shell:
            raise PermissionError("Shell commands are not permitted")
        return self._original_run(*args, **kwargs)

    def __enter__(self) -> Sandbox:  # pragma: no cover - trivial
        builtins.open = cast(Any, self._safe_open)
        setattr(subprocess, "Popen", cast(Any, self._blocked_popen))
        setattr(subprocess, "run", cast(Any, self._blocked_run))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:  # pragma: no cover - trivial
        builtins.open = cast(Any, self._original_open)
        setattr(subprocess, "Popen", cast(Any, self._original_popen))
        setattr(subprocess, "run", cast(Any, self._original_run))
        return False


P = ParamSpec("P")
T = TypeVar("T")


def sandboxed(func: Callable[P, T], *, allow_shell: bool = False) -> Callable[P, T]:
    """Return ``func`` wrapped to execute inside a :class:`Sandbox`."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        with Sandbox(allow_shell=allow_shell):
            result = func(*args, **kwargs)
        return result

    return wrapper
