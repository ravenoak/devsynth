import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.test_setup_wizard_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "setup_wizard.feature"))
