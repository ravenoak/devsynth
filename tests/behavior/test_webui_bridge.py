"""BDD scenarios covering the Streamlit WebUI bridge."""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.webui_bridge_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.gui, pytest.mark.medium]

scenarios(feature_path(__file__, "general", "webui_bridge.feature"))
