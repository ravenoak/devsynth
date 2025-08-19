import json
import os
import subprocess
from pathlib import Path

import pytest
from pytest_bdd import given, then, when


@pytest.fixture
def context():
    return {}


@given("the dialectical audit log contains unresolved questions")
def dialectical_log_with_questions():
    root = Path(os.environ["ORIGINAL_CWD"])
    log_path = root / "dialectical_audit.log"
    original = log_path.read_text()
    data = {"questions": ["Unresolved question"], "resolved": []}
    log_path.write_text(json.dumps(data))
    yield
    log_path.write_text(original)


@when("I verify the release state")
def verify_release_state(context):
    result = subprocess.run(
        ["python", "scripts/verify_release_state.py"],
        capture_output=True,
        text=True,
        cwd=os.environ["ORIGINAL_CWD"],
    )
    context["result"] = result


@then("the release verification should fail")
def release_should_fail(context):
    assert context["result"].returncode != 0
