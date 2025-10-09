"""BDD steps for the ``generate-docs`` command."""

import importlib
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Register the CLI installed step so feature backgrounds load correctly
from .cli_commands_steps import (  # noqa: F401
    check_workflow_success,
    devsynth_cli_installed,
    run_command,
    valid_devsynth_project,
)

pytestmark = [pytest.mark.fast]


@pytest.fixture
def docs_context(monkeypatch):
    """Provide a patched ``generate_docs_cmd`` for testing."""
    import devsynth.application.cli.commands.generate_docs_cmd as docs_module

    mock_cmd = MagicMock()
    monkeypatch.setattr(docs_module, "generate_docs_cmd", mock_cmd)
    importlib.reload(docs_module)
    return {"cmd": mock_cmd}


scenarios(feature_path(__file__, "general", "generate_docs.feature"))


@given("the generate_docs feature context")
def given_context(docs_context):
    """Return the patched context."""
    return docs_context


@when("we execute the generate_docs workflow")
def when_execute(docs_context):
    """Invoke the ``generate_docs`` command."""
    from devsynth.application.cli.commands.generate_docs_cmd import generate_docs_cmd

    generate_docs_cmd(path=".")
    docs_context["cmd"] = generate_docs_cmd


@then("the generate_docs workflow completes")
def then_complete(docs_context):
    """Ensure the command was called."""
    docs_context["cmd"].assert_called_once()
