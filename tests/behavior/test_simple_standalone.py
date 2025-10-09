"""Standalone test to verify pytest-bdd integration."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Load scenarios from the static feature file
scenarios(feature_path(__file__, "general", "simple_addition.feature"))


@pytest.fixture
def context():
    """Create a simple context object for the test."""

    class Context:
        def __init__(self):
            self.numbers = []
            self.result = None

    return Context()


@given(parsers.parse("I have the numbers {num1:d} and {num2:d}"))
def have_numbers(context, num1, num2):
    """Store the numbers for later addition."""
    context.numbers = [num1, num2]


@when("I add them together")
def add_numbers(context):
    """Add the numbers together."""
    context.result = sum(context.numbers)


@then(parsers.parse("the result should be {expected:d}"))
def check_result(context, expected):
    """Verify the addition result."""
    assert context.result == expected
