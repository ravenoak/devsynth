"""DevSynth Test Package.

Ensure the ``devsynth`` package can be imported from the working tree
without performing an editable ``pip install``.  CI installs the package
normally, so local test runs should succeed if the sources are present or
the package has been installed via Poetry.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType


def _ensure_dev_synth_importable() -> None:
    """Ensure ``devsynth`` can be imported from ``src`` or is installed."""

    root = Path(__file__).resolve().parents[1]
    src = root / "src"

    # Always place the ``src`` directory on ``sys.path`` so imports work
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

    try:  # pragma: no cover - quick check
        import devsynth  # noqa: F401

        # Load optional subpackages explicitly to mirror historic behaviour
        try:  # pragma: no cover - best effort
            devsynth.initialize_subpackages()
        except AttributeError:
            pass
        return
    except Exception:
        pass

    raise RuntimeError(
        "DevSynth is not installed and could not be imported from the 'src'\n"
        "directory. Install the package with 'poetry install --with dev,docs --all-extras'"
    )


_ensure_dev_synth_importable()

# Apply lightweight mocks for optional heavy dependencies (e.g. SymPy) so
# test collection does not spend time importing them.
try:  # pragma: no cover - best effort
    from .lightweight_imports import apply_lightweight_imports

    apply_lightweight_imports()
except Exception:
    pass

# Disable optional backends by default so tests don't try to import heavy
# dependencies unless explicitly enabled.
# os.environ.setdefault("ENABLE_CHROMADB", "0")

# Provide lightweight stubs for optional network libraries used by plugins
if "openai" not in sys.modules:
    _openai = ModuleType("openai")
    _openai.OpenAI = object
    _openai.AsyncOpenAI = object
    _openai.types = ModuleType("openai.types")
    _openai.types.chat = ModuleType("openai.types.chat")
    _openai.types.chat.ChatCompletion = object
    _openai.types.chat.ChatCompletionChunk = object
    sys.modules["openai.types"] = _openai.types
    sys.modules["openai.types.chat"] = _openai.types.chat
    sys.modules["openai"] = _openai
if "httpx" not in sys.modules:
    _httpx = ModuleType("httpx")
    _httpx.URL = object
    _httpx.Proxy = object
    _httpx.Timeout = object
    _httpx.Response = object
    _httpx.BaseTransport = object
    _httpx.AsyncBaseTransport = object
    sys.modules["httpx"] = _httpx
