"""DevSynth Test Package.

Ensure the ``devsynth`` package can be imported from the working tree
without performing an editable ``pip install``.  CI installs the package
normally, so local test runs should succeed if the sources are present or
the package has been installed via Poetry.
"""

from __future__ import annotations

import sys
from pathlib import Path
import os

def _ensure_dev_synth_importable() -> None:
    """Ensure ``devsynth`` can be imported from ``src`` or is installed."""

    root = Path(__file__).resolve().parents[1]
    src = root / "src"

    # Always place the ``src`` directory on ``sys.path`` so imports work
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

    try:  # pragma: no cover - quick check
        import devsynth  # noqa: F401
        return
    except Exception:
        pass

    raise RuntimeError(
        "DevSynth is not installed and could not be imported from the 'src'\n"
        "directory. Install the package with 'poetry install --with dev,docs --all-extras'"
    )


_ensure_dev_synth_importable()

# Disable optional backends by default so tests don't try to import
# heavy dependencies unless explicitly enabled.
os.environ.setdefault("ENABLE_CHROMADB", "0")
