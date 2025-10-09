"""Lightweight helpers for invoking Typer applications in tests."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from typer import Typer
from typer.testing import CliRunner


def _coerce_args(args: Iterable[str] | None) -> list[str]:
    if args is None:
        return []
    if isinstance(args, Sequence):
        return list(args)
    return list(args)


def invoke(
    app: Typer,
    args: Iterable[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Any:
    """Invoke a Typer application using :class:`CliRunner`.

    Args:
        app: Typer application to invoke.
        args: Iterable of command-line arguments to pass.
        env: Optional environment mapping supplied to ``CliRunner``.

    Returns:
        The ``Result`` object returned by ``CliRunner.invoke``.
    """

    runner = CliRunner()
    return runner.invoke(app, _coerce_args(args), env=env)


__all__ = ["invoke"]
