"""DevSynth Test Package.

This package ensures the test suite can import ``devsynth`` from the
working tree.  If the package isn't already installed in editable mode,
it installs it before tests are collected.  This mirrors the behaviour
of CI workflows which call ``pip install -e '.[dev]'``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _ensure_editable_install() -> None:
    """Install ``devsynth`` in editable mode if it's not available."""

    try:  # pragma: no cover - minimal safety check
        import devsynth  # noqa: F401
        return
    except Exception:
        pass

    root = Path(__file__).resolve().parents[1]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(root)])


_ensure_editable_install()
