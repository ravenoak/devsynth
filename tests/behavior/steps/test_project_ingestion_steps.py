"""Steps for the project ingestion feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

pytest.skip("Placeholder feature not implemented", allow_module_level=True)

scenarios(feature_path(__file__, "general", "project_ingestion.feature"))


@given("the project_ingestion feature context")
def given_context():
    pass


@when("we execute the project_ingestion workflow")
def when_execute():
    pass


@then("the project_ingestion workflow completes")
def then_complete():
    pass
