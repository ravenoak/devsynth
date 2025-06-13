from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

# Create a logger for this module
logger = DevSynthLogger(__name__)

"""Collaboration module for agent coordination and team-based workflows."""

from .wsde_team_extended import CollaborativeWSDETeam

__all__ = ["CollaborativeWSDETeam"]
