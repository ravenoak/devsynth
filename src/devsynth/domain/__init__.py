"""Domain layer containing core business logic and models.

This package defines the core domain entities, interfaces, and business rules
for DevSynth including WSDE models, requirements, agents, and workflows.
"""

from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Note: Domain models are imported from submodules to avoid circular dependencies
# and heavy imports. Import specific domain classes as needed from their
# respective submodules (models/, interfaces/, wsde/).
