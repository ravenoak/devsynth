"""
Step definitions for the simple addition feature.
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load the scenarios from the feature file
scenarios('../features/examples/simple_addition.feature')

@pytest.fixture
def context():
    """Create a context for the test."""
    class Context:
        def __init__(self):
            self.numbers = []
            self.result = None
    return Context()

@given(parsers.parse("I have the numbers {num1:d} and {num2:d}"))
def have_numbers(context, num1, num2):
    """Store the numbers in the context."""
    context.numbers = [num1, num2]

@when("I add them together")
def add_numbers(context):
    """Add the numbers together."""
    context.result = sum(context.numbers)

@then(parsers.parse("the result should be {expected:d}"))
def check_result(context, expected):
    """Check that the result matches the expected value."""
    assert context.result == expected