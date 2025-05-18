# Version and metadata
__version__ = "0.1.0"

# Import the DevSynthLogger class first
from devsynth.logging_setup import DevSynthLogger

# Now make it available for all modules
__all__ = ["DevSynthLogger"]

# Initialize logger for this module
logger = DevSynthLogger(__name__)

