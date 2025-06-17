"""WebUI placeholder for DevSynth."""

from typing import Optional, Sequence
from .ux_bridge import UXBridge


class WebUI(UXBridge):
    """TODO: Phase 2 implementation of graphical interface."""

    def prompt(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        raise NotImplementedError("TODO: implement WebUI prompt")

    def confirm(self, message: str, *, default: bool = False) -> bool:
        raise NotImplementedError("TODO: implement WebUI confirm")

    def print(self, message: str, *, highlight: bool = False) -> None:
        raise NotImplementedError("TODO: implement WebUI print")
