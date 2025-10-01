import os

import pytest
from pytest_bdd import scenarios

feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "requirements_wizard_logging.feature",
)

# Resource gating if applicable (CLI/UI)

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Load BDD scenarios; module-level pytestmark keeps them in the fast profile.
scenarios(feature_file)
