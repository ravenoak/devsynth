"""Steps for the feature markers feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth import feature_markers
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "feature_markers.feature"))


@given("a documented feature", target_fixture="documented_feature")
def given_documented_feature():
    return (
        feature_markers.FeatureMarker.DIALECTICAL_REASONING_PERSISTS_RESULTS_TO_MEMORY
    )


@when("I search the marker module", target_fixture="search_module")
def when_search_module(documented_feature):
    return feature_markers.get_marker(documented_feature)


@then("I find a corresponding marker function")
def found(search_module):
    assert callable(search_module)
