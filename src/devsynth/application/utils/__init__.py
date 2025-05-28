"""
Utility modules for the DevSynth application.
"""

from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError
from devsynth.application.utils.project_utils import is_devsynth_managed_project

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Export the is_devsynth_managed_project function
__all__ = ['is_devsynth_managed_project']
