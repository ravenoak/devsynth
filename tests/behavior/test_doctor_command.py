import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_devsynth_doctor_steps import *  # noqa: F401,F403
from .steps.test_doctor_command_steps import *  # noqa: F401,F403

from tests.behavior.feature_paths import feature_path


pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "doctor_command.feature"))
