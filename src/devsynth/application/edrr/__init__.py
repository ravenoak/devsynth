"""EDRR (Expand, Differentiate, Refine, Retrospect) application module."""

from .coordinator import EDRRCoordinator, EDRRCoordinatorError
from .templates import register_edrr_templates
from .wsde_team_proxy import WSDETeamProxy

__all__ = [
    "EDRRCoordinator",
    "EDRRCoordinatorError",
    "register_edrr_templates",
    "WSDETeamProxy",
]

# Import templates module to make it available
from . import templates  # noqa: F401
