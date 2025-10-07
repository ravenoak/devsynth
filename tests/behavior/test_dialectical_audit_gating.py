import pytest
from pytest_bdd import scenarios

from .steps.test_dialectical_audit_gating_steps import *  # noqa: F401,F403

from tests.behavior.feature_paths import feature_path


pytestmark = [pytest.mark.fast]

feature_file = feature_path(__file__, "general", "dialectical_audit_gating.feature")

scenarios(feature_file)
