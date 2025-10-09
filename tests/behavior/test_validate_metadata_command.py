import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_validate_metadata_command_steps import *  # noqa: F401,F403

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "validate_metadata_command.feature"))
