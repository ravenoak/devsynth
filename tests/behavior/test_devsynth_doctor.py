import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *
from .steps.test_devsynth_doctor_steps import *

from tests.behavior.feature_paths import feature_path


pytestmark = [pytest.mark.fast]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "devsynth_doctor.feature"))
