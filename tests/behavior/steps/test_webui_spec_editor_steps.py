import pytest
from pytest_bdd import scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import webui_context

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "webui_spec_editor.feature"))


@when("I edit a specification file")
def edit_spec_file(tmp_path, webui_context):
    spec_path = tmp_path / "specs.md"
    spec_path.write_text("old spec")
    webui_context["st"].sidebar.radio.return_value = "Requirements"
    webui_context["st"].text_input.return_value = str(spec_path)
    webui_context["st"].text_area.return_value = "new spec"
    # Click the "Save Spec" button in the first column
    col1, _ = webui_context["st"].columns.return_value
    col1.button.side_effect = [True]
    webui_context["ui"].run()
    webui_context["spec_path"] = spec_path


@then("the spec command should be executed")
def check_spec(webui_context):
    assert webui_context["cli"].spec_cmd.called


@then("the specification should be displayed")
def spec_displayed(webui_context):
    assert webui_context["st"].markdown.called
    assert webui_context["spec_path"].read_text() == "new spec"
