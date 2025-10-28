"""
CLI commands for requirements management.
"""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devsynth.adapters.requirements.cli_chat import CLIChatAdapter
from devsynth.adapters.requirements.console_notification import (
    ConsoleNotificationAdapter,
)
from devsynth.adapters.requirements.memory_repository import (
    InMemoryChangeRepository,
    InMemoryChatRepository,
    InMemoryDialecticalReasoningRepository,
    InMemoryImpactAssessmentRepository,
    InMemoryRequirementRepository,
)
from devsynth.application.requirements.dialectical_reasoner import (
    DialecticalReasonerService,
)
from devsynth.application.requirements.models import RequirementUpdateDTO
from devsynth.application.requirements.requirement_service import (
    RequirementService,
    determine_edrr_phase,
)
from devsynth.config import get_project_config, save_config
from devsynth.config.settings import ensure_path_exists
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.ports.llm_port import LLMPort

from .config import CLIConfig
from .utils import prompt

CLI_CONFIG = CLIConfig.from_env()


# Create a Typer app for requirements management
requirements_app = typer.Typer(help="Requirements management commands")


@requirements_app.callback()
def main(
    ctx: typer.Context,
    non_interactive: bool = typer.Option(
        CLI_CONFIG.non_interactive,
        "--non-interactive/--interactive",
        help="Run without interactive prompts",
        envvar="DEVSYNTH_NONINTERACTIVE",
    ),
):
    """Configure global options for the requirements commands."""

    ctx.obj = CLIConfig(non_interactive=non_interactive)


# Console for rich output
bridge: UXBridge = CLIUXBridge()
console = Console()

# Global services
requirement_repository = InMemoryRequirementRepository()
change_repository = InMemoryChangeRepository()
dialectical_reasoning_repository = InMemoryDialecticalReasoningRepository()
impact_assessment_repository = InMemoryImpactAssessmentRepository()
chat_repository = InMemoryChatRepository()
notification_service = ConsoleNotificationAdapter(
    logging.getLogger("requirements.notification")
)

# These will be initialized later
requirement_service = None
dialectical_reasoner = None
chat_adapter = None


def initialize_services(llm_service: LLMPort):
    """
    Initialize the services with the provided LLM service.

    Args:
        llm_service: The LLM service to use.
    """
    global requirement_service, dialectical_reasoner, chat_adapter

    # Initialize the dialectical reasoner
    dialectical_reasoner = DialecticalReasonerService(
        requirement_repository=requirement_repository,
        reasoning_repository=dialectical_reasoning_repository,
        impact_repository=impact_assessment_repository,
        chat_repository=chat_repository,
        notification_service=notification_service,
        llm_service=llm_service,
    )

    # Initialize the requirement service
    requirement_service = RequirementService(
        requirement_repository=requirement_repository,
        change_repository=change_repository,
        dialectical_reasoner=dialectical_reasoner,
        notification_service=notification_service,
    )

    # Initialize the chat adapter
    chat_adapter = CLIChatAdapter(
        dialectical_reasoner=dialectical_reasoner,
        bridge=bridge,
    )


@requirements_app.command("list")
def list_requirements():
    """List all requirements."""
    requirements = requirement_repository.get_all_requirements()

    if not requirements:
        bridge.print("[yellow]No requirements found.[/yellow]")
        return

    table = Table(title="Requirements")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Status", style="magenta")
    table.add_column("Priority", style="red")
    table.add_column("Type", style="blue")

    for req in requirements:
        table.add_row(
            str(req.id), req.title, req.status.value, req.priority.value, req.type.value
        )

    bridge.print(table)


@requirements_app.command("show")
def show_requirement(requirement_id: str):
    """
    Show details of a requirement.

    Args:
        requirement_id: The ID of the requirement to show.
    """
    try:
        req_id = uuid.UUID(requirement_id)
    except ValueError:
        bridge.print("[red]Invalid requirement ID.[/red]")
        return

    requirement = requirement_repository.get_requirement(req_id)
    if not requirement:
        bridge.print(f"[red]Requirement with ID {requirement_id} not found.[/red]")
        return

    bridge.print(
        Panel(
            f"[bold cyan]ID:[/bold cyan] {requirement.id}\n"
            f"[bold green]Title:[/bold green] {requirement.title}\n"
            f"[bold]Description:[/bold] {requirement.description}\n"
            f"[bold magenta]Status:[/bold magenta] {requirement.status.value}\n"
            f"[bold red]Priority:[/bold red] {requirement.priority.value}\n"
            f"[bold blue]Type:[/bold blue] {requirement.type.value}\n"
            f"[bold]Created at:[/bold] {requirement.created_at}\n"
            f"[bold]Updated at:[/bold] {requirement.updated_at}\n"
            f"[bold]Created by:[/bold] {requirement.created_by}\n"
            f"[bold]Dependencies:[/bold] {', '.join(str(dep) for dep in requirement.dependencies) if requirement.dependencies else 'None'}\n"
            f"[bold]Tags:[/bold] {', '.join(requirement.tags) if requirement.tags else 'None'}\n"
            f"[bold]Metadata:[/bold] {requirement.metadata if requirement.metadata else 'None'}",
            title=f"Requirement: {requirement.title}",
            expand=False,
        )
    )


@requirements_app.command("create")
def create_requirement(
    title: str | None = typer.Option(
        None,
        prompt=not CLI_CONFIG.non_interactive,
        help="Title of the requirement",
    ),
    description: str | None = typer.Option(
        None,
        prompt=not CLI_CONFIG.non_interactive,
        help="Description of the requirement",
    ),
    status: str = typer.Option(
        RequirementStatus.DRAFT.value, help="Status of the requirement"
    ),
    priority: str = typer.Option(
        RequirementPriority.MEDIUM.value, help="Priority of the requirement"
    ),
    type_: str = typer.Option(
        RequirementType.FUNCTIONAL.value,
        "--type",
        help="Type of the requirement",
    ),
    user_id: str = typer.Option(
        "admin", help="ID of the user creating the requirement"
    ),
):
    """
    Create a new requirement.

    Args:
        title: Title of the requirement.
        description: Description of the requirement.
        status: Status of the requirement.
        priority: Priority of the requirement.
        type_: Type of the requirement.
        user_id: ID of the user creating the requirement.
    """
    title = title or os.environ.get("DEVSYNTH_REQ_TITLE", "Untitled")
    description = description or os.environ.get("DEVSYNTH_REQ_DESCRIPTION", "")

    # Validate status
    try:
        status_enum = RequirementStatus(status)
    except ValueError:
        valid_statuses = ", ".join(s.value for s in RequirementStatus)
        bridge.print(f"[red]Invalid status. Valid values are: {valid_statuses}[/red]")
        return

    # Validate priority
    try:
        priority_enum = RequirementPriority(priority)
    except ValueError:
        valid_priorities = ", ".join(p.value for p in RequirementPriority)
        bridge.print(
            f"[red]Invalid priority. Valid values are: {valid_priorities}[/red]"
        )
        return

    # Validate type
    try:
        type_enum = RequirementType(type_)
    except ValueError:
        valid_types = ", ".join(t.value for t in RequirementType)
        bridge.print(f"[red]Invalid type. Valid values are: {valid_types}[/red]")
        return

    # Create the requirement
    requirement = Requirement(
        title=title,
        description=description,
        status=status_enum,
        priority=priority_enum,
        type=type_enum,
        created_by=user_id,
    )

    # Save the requirement
    saved_requirement = requirement_service.create_requirement(requirement, user_id)

    bridge.print(f"[green]Requirement created with ID: {saved_requirement.id}[/green]")


@requirements_app.command("update")
def update_requirement(
    requirement_id: str = typer.Option(..., help="ID of the requirement to update"),
    title: str | None = typer.Option(None, help="New title of the requirement"),
    description: str | None = typer.Option(
        None, help="New description of the requirement"
    ),
    status: str | None = typer.Option(None, help="New status of the requirement"),
    priority: str | None = typer.Option(
        None, help="New priority of the requirement"
    ),
    type_: str | None = typer.Option(
        None, "--type", help="New type of the requirement"
    ),
    reason: str | None = typer.Option(
        None,
        prompt=not CLI_CONFIG.non_interactive,
        help="Reason for the update",
    ),
    user_id: str = typer.Option(
        "admin", help="ID of the user updating the requirement"
    ),
):
    """
    Update a requirement.

    Args:
        requirement_id: ID of the requirement to update.
        title: New title of the requirement.
        description: New description of the requirement.
        status: New status of the requirement.
        priority: New priority of the requirement.
        type_: New type of the requirement.
        reason: Reason for the update.
        user_id: ID of the user updating the requirement.
    """
    try:
        req_id = uuid.UUID(requirement_id)
    except ValueError:
        bridge.print("[red]Invalid requirement ID.[/red]")
        return

    # Check if the requirement exists
    requirement = requirement_repository.get_requirement(req_id)
    if not requirement:
        bridge.print(f"[red]Requirement with ID {requirement_id} not found.[/red]")
        return

    reason = reason or os.environ.get("DEVSYNTH_REQ_REASON", "update")

    # Prepare updates
    status_enum: RequirementStatus | None = None
    priority_enum: RequirementPriority | None = None
    type_enum: RequirementType | None = None

    if status is not None:
        try:
            status_enum = RequirementStatus(status)
        except ValueError:
            valid_statuses = ", ".join(s.value for s in RequirementStatus)
            bridge.print(
                f"[red]Invalid status. Valid values are: {valid_statuses}[/red]"
            )
            return

    if priority is not None:
        try:
            priority_enum = RequirementPriority(priority)
        except ValueError:
            valid_priorities = ", ".join(p.value for p in RequirementPriority)
            bridge.print(
                f"[red]Invalid priority. Valid values are: {valid_priorities}[/red]"
            )
            return

    if type_ is not None:
        try:
            type_enum = RequirementType(type_)
        except ValueError:
            valid_types = ", ".join(t.value for t in RequirementType)
            bridge.print(f"[red]Invalid type. Valid values are: {valid_types}[/red]")
            return

    if (
        title is None
        and description is None
        and status_enum is None
        and priority_enum is None
        and type_enum is None
    ):
        bridge.print("[yellow]No updates provided.[/yellow]")
        return

    updates_dto = RequirementUpdateDTO(
        title=title,
        description=description,
        status=status_enum,
        priority=priority_enum,
        type=type_enum,
    )

    # Update the requirement
    updated_requirement = requirement_service.update_requirement(
        req_id, updates_dto, user_id, reason
    )

    if updated_requirement:
        bridge.print(f"[green]Requirement with ID {requirement_id} updated.[/green]")
    else:
        bridge.print(
            f"[red]Failed to update requirement with ID {requirement_id}.[/red]"
        )


@requirements_app.command("delete")
def delete_requirement(
    requirement_id: str = typer.Option(..., help="ID of the requirement to delete"),
    reason: str | None = typer.Option(
        None,
        prompt=not CLI_CONFIG.non_interactive,
        help="Reason for the deletion",
    ),
    user_id: str = typer.Option(
        "admin", help="ID of the user deleting the requirement"
    ),
):
    """
    Delete a requirement.

    Args:
        requirement_id: ID of the requirement to delete.
        reason: Reason for the deletion.
        user_id: ID of the user deleting the requirement.
    """
    try:
        req_id = uuid.UUID(requirement_id)
    except ValueError:
        bridge.print("[red]Invalid requirement ID.[/red]")
        return

    # Check if the requirement exists
    requirement = requirement_repository.get_requirement(req_id)
    if not requirement:
        bridge.print(f"[red]Requirement with ID {requirement_id} not found.[/red]")
        return

    reason = reason or os.environ.get("DEVSYNTH_REQ_DEL_REASON", "delete")

    # Delete the requirement
    deleted = requirement_service.delete_requirement(req_id, user_id, reason)

    if deleted:
        bridge.print(f"[green]Requirement with ID {requirement_id} deleted.[/green]")
    else:
        bridge.print(
            f"[red]Failed to delete requirement with ID {requirement_id}.[/red]"
        )


@requirements_app.command("changes")
def list_changes(requirement_id: str):
    """
    List changes for a requirement.

    Args:
        requirement_id: ID of the requirement.
    """
    try:
        req_id = uuid.UUID(requirement_id)
    except ValueError:
        bridge.print("[red]Invalid requirement ID.[/red]")
        return

    # Check if the requirement exists
    requirement = requirement_repository.get_requirement(req_id)
    if not requirement:
        bridge.print(f"[red]Requirement with ID {requirement_id} not found.[/red]")
        return

    # Get changes for the requirement
    changes = change_repository.get_changes_for_requirement(req_id)

    if not changes:
        bridge.print(
            f"[yellow]No changes found for requirement with ID {requirement_id}.[/yellow]"
        )
        return

    table = Table(title=f"Changes for Requirement: {requirement.title}")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Created By", style="blue")
    table.add_column("Created At", style="magenta")
    table.add_column("Reason", style="yellow")
    table.add_column("Approved", style="red")

    for change in changes:
        table.add_row(
            str(change.id),
            change.change_type.value,
            change.created_by,
            str(change.created_at),
            change.reason,
            "Yes" if change.approved else "No",
        )

    bridge.print(table)


@requirements_app.command("approve-change")
def approve_change(
    change_id: str = typer.Option(..., help="ID of the change to approve"),
    user_id: str = typer.Option("admin", help="ID of the user approving the change"),
):
    """
    Approve a requirement change.

    Args:
        change_id: ID of the change to approve.
        user_id: ID of the user approving the change.
    """
    try:
        chg_id = uuid.UUID(change_id)
    except ValueError:
        bridge.print("[red]Invalid change ID.[/red]")
        return

    # Check if the change exists
    change = change_repository.get_change(chg_id)
    if not change:
        bridge.print(f"[red]Change with ID {change_id} not found.[/red]")
        return

    # Approve the change
    approved_change = requirement_service.approve_change(chg_id, user_id)

    if approved_change:
        bridge.print(f"[green]Change with ID {change_id} approved.[/green]")
    else:
        bridge.print(f"[red]Failed to approve change with ID {change_id}.[/red]")


@requirements_app.command("reject-change")
def reject_change(
    change_id: str = typer.Option(..., help="ID of the change to reject"),
    comment: str | None = typer.Option(
        None,
        prompt=not CLI_CONFIG.non_interactive,
        help="Comment explaining the rejection",
    ),
    user_id: str = typer.Option("admin", help="ID of the user rejecting the change"),
):
    """
    Reject a requirement change.

    Args:
        change_id: ID of the change to reject.
        comment: Comment explaining the rejection.
        user_id: ID of the user rejecting the change.
    """
    try:
        chg_id = uuid.UUID(change_id)
    except ValueError:
        bridge.print("[red]Invalid change ID.[/red]")
        return

    # Check if the change exists
    change = change_repository.get_change(chg_id)
    if not change:
        bridge.print(f"[red]Change with ID {change_id} not found.[/red]")
        return

    comment = comment or os.environ.get("DEVSYNTH_CHANGE_COMMENT", "rejected")

    # Reject the change
    rejected_change = requirement_service.reject_change(chg_id, user_id, comment)

    if rejected_change:
        bridge.print(f"[green]Change with ID {change_id} rejected.[/green]")
    else:
        bridge.print(f"[red]Failed to reject change with ID {change_id}.[/red]")


@requirements_app.command("chat")
def start_chat(
    change_id: str | None = typer.Option(None, help="ID of the change to discuss"),
    user_id: str = typer.Option("admin", help="ID of the user starting the chat"),
):
    """
    Start a chat session with the dialectical reasoning agent.

    Args:
        change_id: ID of the change to discuss, if any.
        user_id: ID of the user starting the chat.
    """
    # Convert change_id to UUID if provided
    change_uuid = None
    if change_id:
        try:
            change_uuid = uuid.UUID(change_id)
        except ValueError:
            bridge.print("[red]Invalid change ID.[/red]")
            return

        # Check if the change exists
        change = change_repository.get_change(change_uuid)
        if not change:
            bridge.print(f"[red]Change with ID {change_id} not found.[/red]")
            return

    # Create a chat session
    session = chat_adapter.create_session(user_id, change_uuid)

    bridge.print(f"[green]Chat session created with ID: {session.id}[/green]")
    bridge.print("[bold]Starting chat with the dialectical reasoning agent...[/bold]")

    # Run the interactive session
    chat_adapter.run_interactive_session(session.id, user_id)


@requirements_app.command("sessions")
def list_chat_sessions(user_id: str = typer.Option("admin", help="ID of the user")):
    """
    List chat sessions for a user.

    Args:
        user_id: ID of the user.
    """
    # Get sessions for the user
    sessions = chat_adapter.get_sessions_for_user(user_id)

    if not sessions:
        bridge.print(f"[yellow]No chat sessions found for user {user_id}.[/yellow]")
        return

    table = Table(title=f"Chat Sessions for User: {user_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Created At", style="magenta")
    table.add_column("Updated At", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Change ID", style="yellow")
    table.add_column("Messages", style="red")

    for session in sessions:
        messages = chat_adapter.get_messages_for_session(session.id)
        table.add_row(
            str(session.id),
            str(session.created_at),
            str(session.updated_at),
            session.status,
            str(session.change_id) if session.change_id else "None",
            str(len(messages)),
        )

    bridge.print(table)


@requirements_app.command("continue-chat")
def continue_chat(
    session_id: str = typer.Option(..., help="ID of the chat session to continue"),
    user_id: str = typer.Option("admin", help="ID of the user"),
):
    """
    Continue a chat session with the dialectical reasoning agent.

    Args:
        session_id: ID of the chat session to continue.
        user_id: ID of the user.
    """
    try:
        sess_id = uuid.UUID(session_id)
    except ValueError:
        bridge.print("[red]Invalid session ID.[/red]")
        return

    # Check if the session exists
    session = chat_adapter.get_session(sess_id)
    if not session:
        bridge.print(f"[red]Chat session with ID {session_id} not found.[/red]")
        return

    # Check if the session belongs to the user
    if session.user_id != user_id:
        bridge.print(
            f"[red]Chat session with ID {session_id} does not belong to user {user_id}.[/red]"
        )
        return

    bridge.print(f"[bold]Continuing chat session with ID: {session_id}[/bold]")

    # Run the interactive session
    chat_adapter.run_interactive_session(sess_id, user_id)


@requirements_app.command("evaluate-change")
def evaluate_change(
    change_id: str = typer.Option(..., help="ID of the change to evaluate"),
    user_id: str = typer.Option(
        "admin", help="ID of the user requesting the evaluation"
    ),
):
    """
    Evaluate a requirement change using dialectical reasoning.

    Args:
        change_id: ID of the change to evaluate.
        user_id: ID of the user requesting the evaluation.
    """
    try:
        chg_id = uuid.UUID(change_id)
    except ValueError:
        bridge.print("[red]Invalid change ID.[/red]")
        return

    # Check if the change exists
    change = change_repository.get_change(chg_id)
    if not change:
        bridge.print(f"[red]Change with ID {change_id} not found.[/red]")
        return

    bridge.print(f"[bold]Evaluating change with ID: {change_id}[/bold]")

    # Evaluate the change
    reasoning = dialectical_reasoner.evaluate_change(
        change, edrr_phase=determine_edrr_phase(change)
    )

    bridge.print(
        Panel(
            f"[bold cyan]Thesis:[/bold cyan]\n{reasoning.thesis}\n\n"
            f"[bold red]Antithesis:[/bold red]\n{reasoning.antithesis}\n\n"
            f"[bold green]Arguments:[/bold green]",
            title=f"Dialectical Reasoning for Change: {change_id}",
            expand=False,
        )
    )

    # Display arguments
    for i, arg in enumerate(reasoning.arguments, 1):
        position = arg.get("position", "")
        content = arg.get("content", "")

        color = "cyan" if position.lower() == "thesis" else "red"
        bridge.print(
            f"[bold {color}]Argument {i} ({position}):[/bold {color}]\n{content}\n"
        )

    bridge.print(
        Panel(
            f"[bold yellow]Synthesis:[/bold yellow]\n{reasoning.synthesis}\n\n"
            f"[bold magenta]Conclusion:[/bold magenta]\n{reasoning.conclusion}\n\n"
            f"[bold blue]Recommendation:[/bold blue]\n{reasoning.recommendation}",
            title="Synthesis and Conclusion",
            expand=False,
        )
    )


@requirements_app.command("assess-impact")
def assess_impact(
    change_id: str = typer.Option(..., help="ID of the change to assess"),
    user_id: str = typer.Option(
        "admin", help="ID of the user requesting the assessment"
    ),
):
    """
    Assess the impact of a requirement change.

    Args:
        change_id: ID of the change to assess.
        user_id: ID of the user requesting the assessment.
    """
    try:
        chg_id = uuid.UUID(change_id)
    except ValueError:
        bridge.print("[red]Invalid change ID.[/red]")
        return

    # Check if the change exists
    change = change_repository.get_change(chg_id)
    if not change:
        bridge.print(f"[red]Change with ID {change_id} not found.[/red]")
        return

    bridge.print(f"[bold]Assessing impact of change with ID: {change_id}[/bold]")

    # Assess the impact
    impact = dialectical_reasoner.assess_impact(
        change, edrr_phase=determine_edrr_phase(change)
    )

    # Get the affected requirements
    affected_requirements = []
    for req_id in impact.affected_requirements:
        req = requirement_repository.get_requirement(req_id)
        if req:
            affected_requirements.append(req)

    bridge.print(
        Panel(
            f"[bold red]Risk Level:[/bold red] {impact.risk_level}\n"
            f"[bold yellow]Estimated Effort:[/bold yellow] {impact.estimated_effort}\n\n"
            f"[bold cyan]Affected Requirements:[/bold cyan] {len(impact.affected_requirements)}\n"
            + "\n".join(f"- {req.title}" for req in affected_requirements)
            + "\n\n"
            f"[bold green]Affected Components:[/bold green] {len(impact.affected_components)}\n"
            + "\n".join(f"- {comp}" for comp in impact.affected_components),
            title=f"Impact Assessment for Change: {change_id}",
            expand=False,
        )
    )

    bridge.print(
        Panel(
            f"[bold magenta]Analysis:[/bold magenta]\n{impact.analysis}\n\n"
            f"[bold blue]Recommendations:[/bold blue]\n"
            + "\n".join(f"- {rec}" for rec in impact.recommendations),
            title="Analysis and Recommendations",
            expand=False,
        )
    )


@requirements_app.command("wizard")
def wizard_cmd(
    output_file: str = typer.Option(
        "requirements_wizard.json",
        help="File to store collected requirements",
    ),
    title: str | None = typer.Option(
        None,
        help="Requirement title",
    ),
    description: str | None = typer.Option(
        None,
        help="Requirement description",
    ),
    req_type: str | None = typer.Option(
        None,
        help="Requirement type",
    ),
    priority: str | None = typer.Option(
        None,
        help="Requirement priority",
    ),
    constraints: str | None = typer.Option(
        None,
        help="Constraints (comma separated)",
    ),
    *,
    bridge: UXBridge = CLIUXBridge(),
    config: CLIConfig | None = None,
    ctx: typer.Context | None = None,
) -> None:
    """Run the interactive requirements wizard.

    Users can move backward by typing ``back`` when prompted.
    The collected data is written to ``output_file`` in JSON format.
    """

    if isinstance(title, typer.models.OptionInfo):
        title = None
    if isinstance(description, typer.models.OptionInfo):
        description = None
    if isinstance(req_type, typer.models.OptionInfo):
        req_type = None
    if isinstance(priority, typer.models.OptionInfo):
        priority = None
    if isinstance(constraints, typer.models.OptionInfo):
        constraints = None

    title = title or os.environ.get("DEVSYNTH_REQ_TITLE")
    description = description or os.environ.get("DEVSYNTH_REQ_DESCRIPTION")
    req_type = req_type or os.environ.get("DEVSYNTH_REQ_TYPE")

    project_cfg = get_project_config(Path("."))
    priority = (
        priority
        or os.environ.get("DEVSYNTH_REQ_PRIORITY")
        or project_cfg.priority
        or RequirementPriority.MEDIUM.value
    )
    constraints = (
        constraints
        or os.environ.get("DEVSYNTH_REQ_CONSTRAINTS")
        or project_cfg.constraints
        or ""
    )

    steps = [
        (
            "title",
            "Requirement title",
            None,
            None,
        ),
        (
            "description",
            "Requirement description",
            None,
            None,
        ),
        (
            "type",
            "Requirement type",
            [t.value for t in RequirementType],
            RequirementType.FUNCTIONAL.value,
        ),
        (
            "priority",
            "Requirement priority",
            [p.value for p in RequirementPriority],
            priority,
        ),
        (
            "constraints",
            "Constraints (comma separated, optional)",
            None,
            constraints,
        ),
    ]

    cfg = (
        config
        or (ctx.obj if ctx and getattr(ctx, "obj", None) else None)
        or CLIConfig.from_env()
    )

    # Pre-populate responses with defaults so moving backward retains values.
    responses: dict[str, str] = {key: (default or "") for key, _, _, default in steps}
    if title is not None:
        responses["title"] = title
    if description is not None:
        responses["description"] = description
    if req_type is not None:
        responses["type"] = req_type
    if priority is not None:
        responses["priority"] = priority
    if constraints is not None:
        responses["constraints"] = constraints

    index = 0
    while index < len(steps):
        key, message, choices, default = steps[index]
        default_val = responses.get(key, default)
        if cfg.non_interactive:
            reply = default_val or ""
        else:
            prefix = f"Step {index + 1}/{len(steps)}: "
            reply = prompt(
                prefix + message + " (type 'back' to go back)",
                choices=choices,
                default=default_val,
                bridge=bridge,
            )
        if reply.lower() == "back":
            if index > 0:
                index -= 1
            else:
                bridge.display_result("[yellow]Already at first step.[/yellow]")
            continue
        if key in {"title", "description"} and not reply.strip():
            if cfg.non_interactive:
                bridge.display_result(
                    f"[red]{message} is required.[/red]", message_type="error"
                )
                return
            bridge.display_result(
                "[red]This field is required.[/red]", message_type="error"
            )
            continue
        if choices and reply not in choices:
            bridge.display_result(
                f"[red]Invalid choice. Options: {', '.join(choices)}[/red]",
                message_type="error",
            )
            if cfg.non_interactive:
                return
            continue
        responses[key] = reply
        index += 1

    # Use the last provided priority or fall back to ``MEDIUM``.  Empty strings
    # should not override the default value in the resulting plan or project
    # configuration.
    priority_value = responses.get("priority") or RequirementPriority.MEDIUM.value
    result = {
        "title": responses.get("title", ""),
        "description": responses.get("description", ""),
        "type": responses.get("type", RequirementType.FUNCTIONAL.value),
        "priority": priority_value,
        "constraints": [
            c.strip() for c in responses.get("constraints", "").split(",") if c.strip()
        ],
    }

    path = Path(output_file)
    out_dir = ensure_path_exists(str(path.parent), create=True)
    output_path = Path(out_dir) / path.name
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    cfg = get_project_config(Path("."))
    cfg.priority = priority_value
    cfg.constraints = responses.get("constraints", "")
    save_config(cfg, use_pyproject=False)

    bridge.display_result(f"[green]Requirements saved to {output_path}[/green]")


@requirements_app.command("gather")
def gather_requirements_cmd(
    output_file: str = typer.Option(
        "requirements_plan.yaml", help="File to store collected goals"
    ),
    *,
    bridge: UXBridge = CLIUXBridge(),
) -> None:
    """Gather project goals, constraints and priority."""

    from devsynth.core.workflows import gather_requirements

    gather_requirements(bridge, output_file=output_file)
