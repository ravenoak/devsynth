"""Steps for the validate metadata feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

pytest.skip("Placeholder feature not implemented", allow_module_level=True)

scenarios(feature_path(__file__, "general", "validate_metadata.feature"))


@given("the validate_metadata feature context")
def given_context():
    pass


@when("we execute the validate_metadata workflow")
def when_execute():
    pass


@then("the validate_metadata workflow completes")
def then_complete():
    pass
