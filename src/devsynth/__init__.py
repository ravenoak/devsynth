# Version and metadata
__version__ = "0.1.0"

# Import the DevSynthLogger class first
from devsynth.logging_setup import DevSynthLogger, set_request_context, clear_request_context

# Now make it available for all modules
__all__ = ["DevSynthLogger", "set_request_context", "clear_request_context"]

# Initialize logger for this module
logger = DevSynthLogger(__name__)
