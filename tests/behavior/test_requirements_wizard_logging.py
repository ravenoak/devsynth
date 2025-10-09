import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

feature_file = feature_path(__file__, "general", "requirements_wizard_logging.feature")

# Resource gating if applicable (CLI/UI)

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Load BDD scenarios; module-level pytestmark keeps them in the fast profile.
scenarios(feature_file)
