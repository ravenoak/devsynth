import os

from pytest_bdd import scenarios

# Import step definitions to register them
from .steps.test_cli_webui_parity_steps import *  # noqa: F401,F403

feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "cli_ui_parity.feature",
)

scenarios(feature_file)
