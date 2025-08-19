import subprocess

import pytest
from pytest_bdd import then, when


@pytest.fixture
def context():
    return {}


@when("I verify the release state")
def verify_release_state(context):
    result = subprocess.run(
        [
            "python",
            "scripts/verify_release_state.py",
        ],
        capture_output=True,
        text=True,
    )
    context["result"] = result


@then("the release verification should fail")
def release_should_fail(context):
    assert context["result"].returncode != 0
