"""WebUI wrapper for the interactive setup wizard."""

from __future__ import annotations

from typing import Optional

from devsynth.interface.ux_bridge import UXBridge
from devsynth.interface.webui_bridge import WebUIBridge

try:  # pragma: no cover - optional dependency
    from devsynth.application.cli.setup_wizard import SetupWizard
except Exception:  # pragma: no cover - setup wizard is optional
    SetupWizard = None  # type: ignore[assignment]


class WebUISetupWizard:
    """Expose the CLI :class:`SetupWizard` through a WebUI bridge."""

    def __init__(self, bridge: UXBridge | None = None) -> None:
        self.bridge = bridge or WebUIBridge()

    def run(self) -> None:
        """Launch the guided setup wizard."""
        if SetupWizard is None:  # pragma: no cover - error path
            raise RuntimeError(
                "The SetupWizard dependency is missing; ensure CLI components are installed."
            )
        SetupWizard(self.bridge).run()


__all__ = ["WebUISetupWizard"]
