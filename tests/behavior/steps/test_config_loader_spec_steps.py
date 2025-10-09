import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.config.loader import (
    ConfigModel,
    config_key_autocomplete,
    load_config,
    save_config,
)
from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

scenarios(feature_path(__file__, "general", "config_loader_spec.feature"))


@pytest.fixture
def context(tmp_path):
    class Context:
        pass

    ctx = Context()
    ctx.project_dir = tmp_path
    return ctx


@given("an empty project directory")
def empty_project_dir(context):
    return context.project_dir


@when("I load the configuration")
def load_configuration(context):
    context.config = load_config(context.project_dir)


@then("the default configuration is returned")
def default_configuration_returned(context):
    assert isinstance(context.config, ConfigModel)
    assert context.config.language == "python"


@when("I save the configuration as project YAML")
def save_configuration(context):
    context.saved_path = save_config(
        context.config, use_pyproject=False, path=context.project_dir
    )


@then("a project configuration file is created")
def config_file_created(context):
    assert context.saved_path.exists()


@when('I autocomplete the config key with prefix "pro"')
def autocomplete(context):
    context.suggestions = config_key_autocomplete(None, "pro")


@then('"project_root" should be suggested')
def check_suggestion(context):
    assert "project_root" in context.suggestions
