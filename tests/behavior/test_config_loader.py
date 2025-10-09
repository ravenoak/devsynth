import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

# Import step definitions
from .steps.test_config_loader_steps import *

pytestmark = [pytest.mark.fast]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "config_loader.feature"))
