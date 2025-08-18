import pytest
from pytest_bdd import scenarios

from .test_mvu_commands_steps import *  # noqa: F401,F403

pytestmark = pytest.mark.fast

scenarios("../features/mvu/command_execution.feature")
