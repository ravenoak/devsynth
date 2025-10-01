"""BDD scenarios covering the Streamlit WebUI bridge."""

from pathlib import Path

import pytest
from pytest_bdd import scenarios

from .steps.webui_bridge_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.gui, pytest.mark.medium]

feature_file = Path(__file__).with_name("features") / "webui_bridge.feature"

scenarios(feature_file)
