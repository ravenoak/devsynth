import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.test_webui_commands_steps import *  # noqa: F401,F403
from .steps.webui_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "webui_commands.feature"))
