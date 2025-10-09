"""Steps exercising the Agent API endpoints."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient


def _module_stub(name: str, **attributes: object) -> ModuleType:
    """Return a ModuleType populated with the provided attributes."""

    module = ModuleType(name)
    for attribute, value in attributes.items():
        setattr(module, attribute, value)
    return module


scenarios(feature_path(__file__, "general", "agent_api_interactions.feature"))


@pytest.fixture
def api_context(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Start the API with CLI commands mocked."""

    cli_stub = _module_stub("devsynth.application.cli")

    def init_cmd(path=".", project_root=None, language=None, goals=None, *, bridge):
        bridge.display_result("init")

    def gather_cmd(output_file="requirements_plan.yaml", *, bridge):
        g = bridge.ask_question("g")
        c = bridge.ask_question("c")
        p = bridge.ask_question("p")
        bridge.display_result(f"{g},{c},{p}")

    def run_pipeline_cmd(target=None, *, bridge):
        bridge.display_result(f"run:{target}")

    def spec_cmd(requirements_file="requirements.md", *, bridge):
        bridge.display_result(f"spec:{requirements_file}")

    def cli_test_cmd(spec_file="specs.md", output_dir=None, *, bridge):
        bridge.display_result(f"test:{spec_file}")

    def code_cmd(output_dir=None, *, bridge):
        bridge.display_result("code")

    cli_stub.init_cmd = MagicMock(side_effect=init_cmd)
    cli_stub.gather_cmd = MagicMock(side_effect=gather_cmd)
    cli_stub.run_pipeline_cmd = MagicMock(side_effect=run_pipeline_cmd)
    cli_stub.spec_cmd = MagicMock(side_effect=spec_cmd)
    cli_stub.test_cmd = MagicMock(side_effect=cli_test_cmd)
    cli_stub.code_cmd = MagicMock(side_effect=code_cmd)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    doctor_stub = _module_stub("devsynth.application.cli.commands.doctor_cmd")

    def doctor_cmd(path=".", fix: bool = False, *, bridge):
        bridge.display_result(f"doctor:{path}:{fix}")

    doctor_stub.doctor_cmd = MagicMock(side_effect=doctor_cmd)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_stub
    )

    edrr_stub = _module_stub("devsynth.application.cli.commands.edrr_cycle_cmd")

    def edrr_cycle_cmd(prompt, context=None, max_iterations: int = 3, *, bridge):
        bridge.display_result(f"edrr:{prompt}")

    edrr_stub.edrr_cycle_cmd = MagicMock(side_effect=edrr_cycle_cmd)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_stub
    )

    import devsynth.interface.agentapi as agentapi

    importlib.reload(agentapi)
    client = TestClient(agentapi.app)
    return {
        "client": client,
        "cli": cli_stub,
        "doctor_cmd": doctor_stub.doctor_cmd,
        "edrr_cycle_cmd": edrr_stub.edrr_cycle_cmd,
        "last_request": {},
    }


@given("the Agent API server is running")
def api_running(api_context):
    """Return the API context."""
    return api_context


@when("I POST to /init")
def post_init(api_context):
    api_context["client"].post("/init", json={"path": "proj"})


@when("I POST to /gather")
def post_gather(api_context):
    api_context["client"].post(
        "/gather",
        json={"goals": "g1", "constraints": "c1", "priority": "high"},
    )


@when("I POST to /synthesize")
def post_synthesize(api_context):
    api_context["client"].post("/synthesize", json={"target": "unit"})


@when(parsers.parse('I POST to /spec with requirements file "{requirements_file}"'))
def post_spec(api_context, requirements_file):
    response = api_context["client"].post(
        "/spec", json={"requirements_file": requirements_file}
    )
    api_context["last_request"]["requirements_file"] = requirements_file
    api_context["last_response"] = response


@when(parsers.parse('I POST to /test with spec file "{spec_file}"'))
def post_test(api_context, spec_file):
    response = api_context["client"].post("/test", json={"spec_file": spec_file})
    api_context["last_request"]["spec_file"] = spec_file
    api_context["last_response"] = response


@when("I POST to /code")
def post_code(api_context):
    response = api_context["client"].post("/code", json={})
    api_context["last_response"] = response


@when(parsers.parse('I POST to /doctor with path "{path}" and fix "{fix}"'))
def post_doctor(api_context, path, fix):
    fix_bool = fix.lower() == "true"
    response = api_context["client"].post(
        "/doctor", json={"path": path, "fix": fix_bool}
    )
    api_context["last_request"]["path"] = path
    api_context["last_request"]["fix"] = fix
    api_context["last_response"] = response


@when(parsers.parse('I POST to /edrr-cycle with prompt "{prompt}"'))
def post_edrr_cycle(api_context, prompt):
    response = api_context["client"].post("/edrr-cycle", json={"prompt": prompt})
    api_context["last_request"]["prompt"] = prompt
    api_context["last_response"] = response


@when("I GET /status")
def get_status(api_context):
    api_context["status"] = api_context["client"].get("/status")


@then("the CLI init command should be called")
def cli_init_called(api_context):
    assert api_context["cli"].init_cmd.called


@then("the CLI gather command should be called")
def cli_gather_called(api_context):
    assert api_context["cli"].gather_cmd.called


@then("the CLI run_pipeline command should be called")
def cli_run_pipeline_called(api_context):
    assert api_context["cli"].run_pipeline_cmd.called


@then("the CLI spec command should be called")
def cli_spec_called(api_context):
    assert api_context["cli"].spec_cmd.called


@then("the CLI test command should be called")
def cli_test_called(api_context):
    assert api_context["cli"].test_cmd.called


@then("the CLI code command should be called")
def cli_code_called(api_context):
    assert api_context["cli"].code_cmd.called


@then("the CLI doctor command should be called")
def cli_doctor_called(api_context):
    assert api_context["doctor_cmd"].called


@then("the CLI edrr_cycle command should be called")
def cli_edrr_cycle_called(api_context):
    assert api_context["edrr_cycle_cmd"].called


@then(parsers.parse('the requirements file should be "{requirements_file}"'))
def check_requirements_file(api_context, requirements_file):
    assert api_context["last_request"]["requirements_file"] == requirements_file


@then(parsers.parse('the spec file should be "{spec_file}"'))
def check_spec_file(api_context, spec_file):
    assert api_context["last_request"]["spec_file"] == spec_file


@then(parsers.parse('the path should be "{path}"'))
def check_path(api_context, path):
    assert api_context["last_request"]["path"] == path


@then(parsers.parse('the fix parameter should be "{fix}"'))
def check_fix(api_context, fix):
    assert api_context["last_request"]["fix"] == fix


@then(parsers.parse('the prompt should be "{prompt}"'))
def check_prompt(api_context, prompt):
    assert api_context["last_request"]["prompt"] == prompt


@then('the status message should be "run:unit"')
def status_run_unit(api_context):
    assert api_context["status"].json() == {"messages": ["run:unit"]}
