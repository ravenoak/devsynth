import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

# Import step definitions to register them
from .steps.test_cli_webui_parity_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

feature_file = feature_path(__file__, "general", "cli_ui_parity.feature")

scenarios(feature_file)
