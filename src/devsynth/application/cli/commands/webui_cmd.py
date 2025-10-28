"""[experimental] Launch the Streamlit WebUI.

This command depends on optional extras and may not be available in all environments.
"""

from __future__ import annotations

from typing import Optional, cast
from collections.abc import Callable

from devsynth.exceptions import DevSynthError
from devsynth.interface.ux_bridge import UXBridge

from ..utils import _resolve_bridge

RunWebUICallback = Callable[[], None]


def _load_webui_runner() -> RunWebUICallback:
    """Return the Streamlit runner while keeping the import lazy."""

    import importlib.util
    import sys
    from pathlib import Path

    # Load the webui.py module directly
    webui_path = Path(__file__).parent.parent.parent.parent / "interface" / "webui.py"
    spec = importlib.util.spec_from_file_location(
        "devsynth.interface.webui_module", webui_path
    )
    if spec and spec.loader:
        webui_module = importlib.util.module_from_spec(spec)
        sys.modules["devsynth.interface.webui_module"] = webui_module
        spec.loader.exec_module(webui_module)
        run = webui_module.run
    else:
        raise ImportError("Could not load webui module")

    return cast(RunWebUICallback, run)


def webui_cmd(*, bridge: UXBridge | None = None) -> None:
    """Launch the Streamlit WebUI.

    Notes:
        - This command requires the optional web UI dependencies. To install:
          `poetry install --with dev --extras webui` or equivalent.
        - Implemented with a lazy import so that the main CLI remains importable
          in minimal environments (no Streamlit installed), per project guidelines.
    """
    bridge = _resolve_bridge(bridge)
    try:
        # Lazy import to avoid importing Streamlit unless the command is invoked.
        run = _load_webui_runner()

        run()
    except (
        ModuleNotFoundError,
        DevSynthError,
    ) as err:  # pragma: no cover - optional dep missing
        bridge.display_result(
            "[yellow]WebUI dependencies are not installed.[/yellow]\n"
            "Install optional extras and retry, e.g.:\n"
            "  poetry install --with dev --extras webui\n"
            f"Details: {err}"
        )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}")


__all__ = ["webui_cmd"]
