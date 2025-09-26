import pytest
from pytest_bdd import scenarios

from .steps.test_dialectical_reasoning_impact_memory_persistence_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

scenarios("dialectical_reasoning/impact_assessment_memory_persistence.feature")
