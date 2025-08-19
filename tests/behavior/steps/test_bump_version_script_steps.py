import subprocess

import pytest
from pytest_bdd import given, then, when

from scripts import bump_version


@pytest.fixture
def context():
    return {}


@given("a sample __init__ file")
def sample_init(tmp_path, context):
    init_path = tmp_path / "__init__.py"
    init_path.write_text('__version__ = "0.1.0-alpha.1"\n')
    context["init_path"] = init_path


@when('I bump the version to "0.1.0-alpha.2.dev0"')
def run_bump(monkeypatch, context):
    calls = []

    def fake_run(cmd, check=True):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    bump_version.bump_version("0.1.0-alpha.2.dev0", init_path=context["init_path"])
    context["calls"] = calls


@then('the __init__ version should be "0.1.0-alpha.2.dev0"')
def assert_version(context):
    assert (
        context["init_path"].read_text().strip() == '__version__ = "0.1.0-alpha.2.dev0"'
    )
    assert ["poetry", "version", "0.1.0-alpha.2.dev0"] in context["calls"]
