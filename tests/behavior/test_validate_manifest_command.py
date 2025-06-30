import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.validate_manifest_command_steps import *  # noqa: F401,F403
from .steps.edrr_cycle_steps import *  # noqa: F401,F403

pytestmark = pytest.mark.requires_resource("cli")

scenarios("features/validate_manifest_command.feature")
