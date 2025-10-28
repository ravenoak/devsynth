"""CLI command to generate MVU traceability reports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer

from devsynth.core.mvu.report import generate_report

if TYPE_CHECKING:  # pragma: no cover - type checking import
    from devsynth.interface.ux_bridge import UXBridge
else:  # pragma: no cover - fallback for optional dependency

    class UXBridge:  # pragma: no cover
        """Runtime stub used when :class:`UXBridge` isn't installed."""

        pass


def mvu_report_cmd(
    since: str | None = typer.Option(
        None,
        "--since",
        help="Git revision to start scanning from (e.g. origin/main).",
    ),
    fmt: str = typer.Option(
        "markdown",
        "--format",
        help="Output format: markdown or html.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Destination file. Prints to stdout when omitted.",
    ),
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Generate a traceability matrix from MVU metadata in git history."""

    content = generate_report(since, fmt)
    if output is not None:
        output.write_text(content, encoding="utf-8")
    else:
        print(content)
