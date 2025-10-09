import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.test_webui_onboarding_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

# Load scenarios from the feature file using the pytest-bdd base directory
scenarios(feature_path(__file__, "general", "webui_onboarding_flow.feature"))
