"""BDD tests for the retry mechanism."""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.test_retry_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

feature_file = feature_path(__file__, "general", "retry_mechanism.feature")

# Load all scenarios from the feature file
scenarios(feature_file)


# The test functions below are no longer needed as scenarios() will automatically
# generate test functions for each scenario in the feature file.
# The naming convention will be test_<scenario_name_with_underscores>
# For example: test_successful_retry_after_transient_errors

# For documentation purposes, we keep the docstrings of what each scenario tests
"""
Scenarios in retry_mechanism.feature:

1. Successful retry after transient errors
   Test successful retry after transient errors.
   ReqID: N/A

2. Failure after maximum retries
   Test failure after maximum retries.
   ReqID: N/A

3. Exponential backoff with jitter
   Test exponential backoff with jitter.
   ReqID: N/A

4. Callback function is called on each retry
   Test callback invocation on each retry.
   ReqID: N/A

5. Only specified exceptions trigger retries
   Test selective retry based on exception types.
   ReqID: N/A

6. Deterministic backoff without jitter
   Test deterministic exponential backoff when jitter is disabled.
   ReqID: N/A
"""
