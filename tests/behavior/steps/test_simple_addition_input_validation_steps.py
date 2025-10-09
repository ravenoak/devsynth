"""BDD steps for simple addition input validation."""

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.simple_addition import add
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "simple_addition_input_validation.feature"))


@pytest.fixture
def context():
    """Context object for storing test data."""

    class Context:
        def __init__(self):
            self.a = None
            self.b = None
            self.exception = None

    return Context()


@given("I have non-numeric inputs")
def have_non_numeric_inputs(context):
    context.a = "1"
    context.b = "2"


@when("I try to add them")
def try_to_add(context):
    try:
        add(context.a, context.b)
    except Exception as exc:  # pragma: no cover - capturing unexpected exceptions
        context.exception = exc


@then("a TypeError is raised")
def type_error_is_raised(context):
    assert isinstance(context.exception, TypeError)
