import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .mvu_command_execution_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "command_execution.feature"))
