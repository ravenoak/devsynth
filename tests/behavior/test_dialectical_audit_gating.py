import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.test_dialectical_audit_gating_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

feature_file = feature_path(__file__, "general", "dialectical_audit_gating.feature")

scenarios(feature_file)
