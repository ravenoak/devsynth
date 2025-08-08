"""WebUI wrapper for the interactive setup wizard."""

from __future__ import annotations

from typing import Optional

from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.interface.ux_bridge import UXBridge
from devsynth.interface.webui_bridge import WebUIBridge


class WebUISetupWizard:
    """Expose the CLI :class:`SetupWizard` through a WebUI bridge."""

    def __init__(self, bridge: Optional[UXBridge] = None) -> None:
        self.bridge = bridge or WebUIBridge()

    def run(self) -> None:
        """Launch the guided setup wizard."""
        SetupWizard(self.bridge).run()


__all__ = ["WebUISetupWizard"]
