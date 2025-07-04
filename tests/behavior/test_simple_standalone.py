"""
A standalone test script to verify that pytest-bdd works without any dependencies.
"""

import os
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Define a simple feature string
FEATURE = """
Feature: Simple Addition
  As a user
  I want to add two numbers
  So that I can get their sum

  Scenario: Add two numbers
    Given I have the numbers 1 and 2
    When I add them together
    Then the result should be 3
"""

# Write the feature to a temporary file
feature_file = os.path.join(os.path.dirname(__file__), "simple_addition.feature")
with open(feature_file, "w") as f:
    f.write(FEATURE)

# Load the scenarios from the feature file
scenarios(feature_file)

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