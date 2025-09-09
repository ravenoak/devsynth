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
pytestmark = [pytest.mark.requires_resource("cli")]

# Load BDD scenarios; per-function speed markers are applied centrally in tests/behavior/conftest.py
scenarios(feature_file)
