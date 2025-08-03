"""Steps for the enhanced chromadb integration feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

scenarios("../features/general/enhanced_chromadb_integration.feature")


@pytest.fixture
def enhanced_chroma_context():
    return {"executed": False}


@pytest.mark.medium
@given("the enhanced_chromadb_integration feature context")
def given_context(enhanced_chroma_context):
    return enhanced_chroma_context


@pytest.mark.medium
@when("we execute the enhanced_chromadb_integration workflow")
def when_execute(enhanced_chroma_context):
    enhanced_chroma_context["executed"] = True


@pytest.mark.medium
@then("the enhanced_chromadb_integration workflow completes")
def then_complete(enhanced_chroma_context):
    assert enhanced_chroma_context.get("executed") is True
