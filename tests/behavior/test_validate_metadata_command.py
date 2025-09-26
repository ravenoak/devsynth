import os

import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_validate_metadata_command_steps import *  # noqa: F401,F403

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Get the absolute path to the feature file
feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "validate_metadata_command.feature",
)

# Load the scenarios from the feature file
scenarios(feature_file)
