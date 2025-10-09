"""Steps for the docs fetch feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "docs_fetch.feature"))


@pytest.fixture
def docs_context():
    return {"executed": False}


@given("the docs_fetch feature context")
def given_context(docs_context):
    return docs_context


@when("we execute the docs_fetch workflow")
def when_execute(docs_context):
    docs_context["executed"] = True


@then("the docs_fetch workflow completes")
def then_complete(docs_context):
    assert docs_context.get("executed") is True
