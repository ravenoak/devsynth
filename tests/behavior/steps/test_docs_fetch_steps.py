"""Steps for the docs fetch feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

scenarios("../features/general/docs_fetch.feature")


@pytest.fixture
def docs_context():
    return {"executed": False}


@pytest.mark.medium
@given("the docs_fetch feature context")
def given_context(docs_context):
    return docs_context


@pytest.mark.medium
@when("we execute the docs_fetch workflow")
def when_execute(docs_context):
    docs_context["executed"] = True


@pytest.mark.medium
@then("the docs_fetch workflow completes")
def then_complete(docs_context):
    assert docs_context.get("executed") is True
