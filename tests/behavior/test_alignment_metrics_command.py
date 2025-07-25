import os
import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.alignment_metrics_steps import *  # noqa: F401,F403

pytestmark = pytest.mark.requires_resource("cli")

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "general", "alignment_metrics_command.feature")

# Load the scenarios from the feature file
scenarios(feature_file)
