"""Steps for the exceptions framework feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.exceptions import DevSynthError
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "exceptions_framework.feature"))


@given("a component that raises a DevSynthError", target_fixture="component")
def given_component():
    def _component():
        raise DevSynthError("boom")

    return _component


@when("I handle errors", target_fixture="handle")
def when_handle(component):
    try:
        component()
    except DevSynthError as err:
        return err
    raise AssertionError("DevSynthError not raised")


@then("I can catch the base class")
def caught(handle):
    assert isinstance(handle, DevSynthError)
