import subprocess
from pathlib import Path

import pytest
from pytest_bdd import given, then, when

pytestmark = pytest.mark.fast


@pytest.fixture
def context():
    return {}


@pytest.fixture
def release_file(tmp_path):
    path = Path("docs/release/0.1.0-alpha.1.md")
    original = path.read_text()
    yield path
    path.write_text(original)


@given('the release status is "{status}"')
def set_release_status(release_file, status):
    text = release_file.read_text().splitlines()
    for i, line in enumerate(text):
        if line.startswith("status:"):
            text[i] = f"status: {status}"
            break
    release_file.write_text("\n".join(text))


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


@then("the release verification should pass")
def release_should_pass(context):
    assert context["result"].returncode == 0
