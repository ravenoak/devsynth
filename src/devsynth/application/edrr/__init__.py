"""EDRR (Expand, Differentiate, Refine, Retrospect) application module."""

from .coordinator import EDRRCoordinator
from .templates import register_edrr_templates

__all__ = [
    "EDRRCoordinator",
    "register_edrr_templates",
]

# Import templates module to make it available
from . import templates
