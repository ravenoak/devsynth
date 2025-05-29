"""
Project Utilities

This module provides utility functions for working with DevSynth projects.
"""
from devsynth.config.settings import is_devsynth_managed_project

# Re-export the function for easier imports
__all__ = ['is_devsynth_managed_project']