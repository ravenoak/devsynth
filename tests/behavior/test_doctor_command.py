import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.doctor_command_steps import *  # noqa: F401,F403
from .steps.devsynth_doctor_steps import *  # noqa: F401,F403

pytestmark = pytest.mark.requires_resource("cli")

scenarios("features/doctor_command.feature")
