# Version and metadata
__version__ = "0.1.0-alpha.1"

# Import the DevSynthLogger class first
from devsynth.logging_setup import DevSynthLogger, set_request_context, clear_request_context

# Now make it available for all modules
__all__ = ["DevSynthLogger", "set_request_context", "clear_request_context"]

# Initialize logger for this module
logger = DevSynthLogger(__name__)

# Ensure subpackages can be imported even if tests manipulate ``sys.modules``.
import importlib
import sys
if "devsynth.application" not in sys.modules:
    try:  # pragma: no cover - safe fallback
        importlib.import_module("devsynth.application")
    except Exception:  # pragma: no cover - ignore if unavailable
        pass
if "devsynth.application.memory" not in sys.modules:
    try:  # pragma: no cover - optional subpackage
        importlib.import_module("devsynth.application.memory")
    except Exception:  # pragma: no cover - ignore
        pass
