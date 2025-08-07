from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

"""Collaboration module for agent coordination and team-based workflows."""

__all__ = ["CollaborativeWSDETeam"]


def __getattr__(name: str):  # pragma: no cover - simple lazy import
    if name == "CollaborativeWSDETeam":
        from .collaborative_wsde_team import CollaborativeWSDETeam

        return CollaborativeWSDETeam
    raise AttributeError(name)
