"""
Behavior tests for Code Analysis feature.
"""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path
from .steps.test_code_analysis_steps import *

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "code_analysis.feature"))
