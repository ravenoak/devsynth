"""EDRR (Expand, Differentiate, Refine, Retrospect) application module."""

from .coordinator import EDRRCoordinator
from .templates import register_edrr_templates
from .wsde_team_proxy import WSDETeamProxy

__all__ = [
    "EDRRCoordinator",
    "register_edrr_templates",
    "WSDETeamProxy",
]

# Import templates module to make it available
from . import templates
