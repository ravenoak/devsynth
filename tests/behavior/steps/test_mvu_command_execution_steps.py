import pytest
from pytest_bdd import scenarios

from .mvu_command_execution_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

scenarios("../features/mvu/command_execution.feature")
