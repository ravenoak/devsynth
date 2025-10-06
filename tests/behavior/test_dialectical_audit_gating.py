import os

import pytest
from pytest_bdd import scenarios

from .steps.test_dialectical_audit_gating_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "dialectical_audit_gating.feature",
)

scenarios(feature_file)
