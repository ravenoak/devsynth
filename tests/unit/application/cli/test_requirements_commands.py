import json
from unittest.mock import MagicMock

import pytest
import yaml
from rich.table import Table

from devsynth.application.cli import requirements_commands as rc
from devsynth.application.cli.config import CLIConfig
from devsynth.domain.models.requirement import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):

    def __init__(self, answers):
        self.answers = list(answers)

    def ask_question(self, *_a, **_k):
        return self.answers.pop(0)

    def confirm_choice(self, *_a, **_k):
        return True

    def display_result(self, *_a, **_k):
        pass


@pytest.mark.fast
def test_wizard_cmd_back_navigation_succeeds(tmp_path, monkeypatch):
    """Users should be able to revise answers using 'back'."""
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    answers = [
        "Old title",
        "back",
        "New title",
        "Description",
        "functional",
        "medium",
        "",
    ]
    bridge = DummyBridge(answers)
    output = tmp_path / "req.json"
    rc.wizard_cmd(
        output_file=str(output), bridge=bridge, config=CLIConfig(non_interactive=False)
    )
    data = json.load(open(output))
    assert data["title"] == "New title"
    assert data["priority"] == "medium"


@pytest.mark.fast
def test_gather_requirements_cmd_yaml_succeeds(tmp_path, monkeypatch):
    """gather_requirements_cmd should write YAML output."""

    class Bridge(DummyBridge):

        def prompt(self, *a, **k):
            return self.ask_question()

        def confirm(self, *a, **k):
            return True

    answers = ["goal1", "constraint1", "high"]
    bridge = Bridge(answers)
    output = tmp_path / "requirements_plan.yaml"
    monkeypatch.chdir(tmp_path)
    rc.gather_requirements_cmd(output_file=str(output), bridge=bridge)
    assert output.exists()
    data = yaml.safe_load(open(output))
    assert data["priority"] == "high"


@pytest.mark.fast
def test_initialize_services_configures_singletons(monkeypatch):
    """initialize_services should wire repositories into CLI singletons."""

    reasoner_instance = MagicMock(name="dialectical_reasoner")
    requirement_service_instance = MagicMock(name="requirement_service")
    chat_adapter_instance = MagicMock(name="chat_adapter")
    llm_service = MagicMock(name="llm_service")

    monkeypatch.setattr(rc, "dialectical_reasoner", None, raising=False)
    monkeypatch.setattr(rc, "requirement_service", None, raising=False)
    monkeypatch.setattr(rc, "chat_adapter", None, raising=False)
    monkeypatch.setattr(
        rc,
        "DialecticalReasonerService",
        MagicMock(return_value=reasoner_instance),
    )
    monkeypatch.setattr(
        rc,
        "RequirementService",
        MagicMock(return_value=requirement_service_instance),
    )
    monkeypatch.setattr(
        rc, "CLIChatAdapter", MagicMock(return_value=chat_adapter_instance)
    )

    rc.initialize_services(llm_service)

    rc.DialecticalReasonerService.assert_called_once_with(
        requirement_repository=rc.requirement_repository,
        reasoning_repository=rc.dialectical_reasoning_repository,
        impact_repository=rc.impact_assessment_repository,
        chat_repository=rc.chat_repository,
        notification_service=rc.notification_service,
        llm_service=llm_service,
    )
    rc.RequirementService.assert_called_once_with(
        requirement_repository=rc.requirement_repository,
        change_repository=rc.change_repository,
        dialectical_reasoner=reasoner_instance,
        notification_service=rc.notification_service,
    )
    rc.CLIChatAdapter.assert_called_once_with(
        dialectical_reasoner=reasoner_instance,
        bridge=rc.bridge,
    )

    assert rc.dialectical_reasoner is reasoner_instance
    assert rc.requirement_service is requirement_service_instance
    assert rc.chat_adapter is chat_adapter_instance


@pytest.mark.fast
def test_list_requirements_handles_empty_repository(monkeypatch):
    """list_requirements should inform users when no data exists."""

    repo = MagicMock()
    repo.get_all_requirements.return_value = []
    bridge = MagicMock()
    monkeypatch.setattr(rc, "requirement_repository", repo, raising=False)
    monkeypatch.setattr(rc, "bridge", bridge, raising=False)

    rc.list_requirements()

    repo.get_all_requirements.assert_called_once_with()
    bridge.print.assert_called_once_with("[yellow]No requirements found.[/yellow]")


@pytest.mark.fast
def test_list_requirements_renders_rich_table(monkeypatch):
    """list_requirements should display requirement summaries in a table."""

    requirement = Requirement(
        title="Improve docs",
        description="Document CLI",
        status=RequirementStatus.APPROVED,
        priority=RequirementPriority.HIGH,
        type=RequirementType.BUSINESS,
    )
    repo = MagicMock()
    repo.get_all_requirements.return_value = [requirement]
    bridge = MagicMock()
    monkeypatch.setattr(rc, "requirement_repository", repo, raising=False)
    monkeypatch.setattr(rc, "bridge", bridge, raising=False)

    rc.list_requirements()

    repo.get_all_requirements.assert_called_once_with()
    bridge.print.assert_called_once()
    (table,) = bridge.print.call_args.args
    assert isinstance(table, Table)
    assert len(table.rows) == 1
    column_values = {column.header: list(column._cells) for column in table.columns}
    assert column_values["ID"][0] == str(requirement.id)
    assert column_values["Title"][0] == requirement.title
    assert column_values["Status"][0] == requirement.status.value
    assert column_values["Priority"][0] == requirement.priority.value
    assert column_values["Type"][0] == requirement.type.value


@pytest.mark.fast
def test_create_requirement_invokes_service(monkeypatch):
    """create_requirement should validate options and persist via service."""

    bridge = MagicMock()
    saved_requirement = Requirement(title="Traceability")
    requirement_service = MagicMock()
    requirement_service.create_requirement.return_value = saved_requirement

    monkeypatch.setattr(rc, "bridge", bridge, raising=False)
    monkeypatch.setattr(rc, "requirement_service", requirement_service, raising=False)

    rc.create_requirement(
        title="Traceability",
        description="Link specs to tests",
        status=RequirementStatus.APPROVED.value,
        priority=RequirementPriority.HIGH.value,
        type_=RequirementType.BUSINESS.value,
        user_id="analyst",
    )

    requirement_service.create_requirement.assert_called_once()
    requirement_arg, user_arg = requirement_service.create_requirement.call_args[0]
    assert isinstance(requirement_arg, Requirement)
    assert requirement_arg.title == "Traceability"
    assert requirement_arg.description == "Link specs to tests"
    assert requirement_arg.status is RequirementStatus.APPROVED
    assert requirement_arg.priority is RequirementPriority.HIGH
    assert requirement_arg.type is RequirementType.BUSINESS
    assert user_arg == "analyst"
    bridge.print.assert_called_with(
        f"[green]Requirement created with ID: {saved_requirement.id}[/green]"
    )
