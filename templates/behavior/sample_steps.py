"""Sample step definitions for behavior tests in DevSynth projects."""

import pytest
from pytest_bdd import given, when, then, scenarios

scenarios("sample.feature")


@pytest.fixture
def context():
    """Simple object for sharing state between steps."""
    return type("Context", (), {})()


@given("I have numbers 2 and 3")
def set_numbers(context):
    """Store example numbers on the context."""
    context.a = 2
    context.b = 3


@when("I add them")
def add_numbers(context):
    """Perform addition on stored numbers."""
    context.result = context.a + context.b


@then("the result should be 5")
def check_result(context):
    """Verify the addition result."""
    assert context.result == 5
