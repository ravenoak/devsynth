import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.alignment_metrics_steps import *  # noqa: F401,F403

pytestmark = pytest.mark.requires_resource("cli")

scenarios("features/alignment_metrics_command.feature")
