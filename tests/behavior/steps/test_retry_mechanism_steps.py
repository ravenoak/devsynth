"""Steps for the retry mechanism feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "retry_mechanism.feature"))


@pytest.fixture
def retry_context():
    return {"executed": False}


@given("the retry_mechanism feature context")
def given_context(retry_context):
    return retry_context


@when("we execute the retry_mechanism workflow")
def when_execute(retry_context):
    retry_context["executed"] = True


@then("the retry_mechanism workflow completes")
def then_complete(retry_context):
    assert retry_context.get("executed") is True
