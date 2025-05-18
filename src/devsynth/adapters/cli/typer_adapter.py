
import sys
import argparse
from rich.console import Console
from typing import Optional, List
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

# Create a logger for this module
logger = DevSynthLogger(__name__)

from devsynth.application.cli import (
    init_cmd, spec_cmd, test_cmd, code_cmd,
    run_cmd, config_cmd, analyze_cmd, webapp_cmd,
    dbschema_cmd, adaptive_cmd, analyze_code_cmd
)
from devsynth.application.cli.apispec import apispec_cmd
from devsynth.application.cli.requirements_commands import requirements_app

console = Console()

def show_help():
    """Display help information."""
    console.print(f"[bold]DevSynth CLI[/bold] - Iterative 'expand, differentiate, refine' automation")
    console.print(f"\nCommands:")
    console.print(f"  init         Initialize a new DevSynth project")
    console.print(f"  analyze      Analyze requirements from a file or interactively")
    console.print(f"  analyze-code Analyze a codebase to understand its architecture and quality")
    console.print(f"  spec         Generate specifications from requirements")
    console.print(f"  test         Generate tests from specifications")
    console.print(f"  code         Generate code from tests")
    console.print(f"  run          Execute the generated code")
    console.print(f"  config       Configure DevSynth settings")
    console.print(f"  webapp       Generate a web application")
    console.print(f"  dbschema     Generate a database schema")
    console.print(f"  apispec      Generate an API specification")
    console.print(f"  requirements Manage requirements with dialectical reasoning")
    console.print(f"  help         Display this help message")
    console.print(f"\nRun 'devsynth [COMMAND] --help' for more information on a command.")

def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="DevSynth CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new DevSynth project")
    init_parser.add_argument("--path", default=".", help="Path to initialize the project")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze requirements from a file or interactively")
    analyze_parser.add_argument("--input", help="Path to requirements file to analyze")
    analyze_parser.add_argument("--interactive", action="store_true", help="Start an interactive session for requirement gathering")

    # analyze-code command
    analyze_code_parser = subparsers.add_parser("analyze-code", help="Analyze a codebase to understand its architecture and quality")
    analyze_code_parser.add_argument("--path", help="Path to the codebase to analyze (default: current directory)")

    # spec command
    spec_parser = subparsers.add_parser("spec", help="Generate specifications from requirements")
    spec_parser.add_argument("--requirements-file", default="requirements.md", help="Path to requirements file")

    # test command
    test_parser = subparsers.add_parser("test", help="Generate tests from specifications")
    test_parser.add_argument("--spec-file", default="specs.md", help="Path to specifications file")

    # code command
    subparsers.add_parser("code", help="Generate implementation code from tests")

    # run command
    run_parser = subparsers.add_parser("run", help="Execute the generated code")
    run_parser.add_argument("--target", help="Specific target to run")

    # config command
    config_parser = subparsers.add_parser("config", help="Configure DevSynth settings")
    config_parser.add_argument("--key", help="Configuration key to set or view")
    config_parser.add_argument("--value", help="Value to set for the configuration key")
    config_parser.add_argument("--list-models", action="store_true", help="List available LM Studio models")

    # webapp command
    webapp_parser = subparsers.add_parser("webapp", help="Generate a web application")
    webapp_parser.add_argument("--framework", default="flask", help="Web framework to use (flask, fastapi, django, express)")
    webapp_parser.add_argument("--name", default="webapp", help="Name of the web application")
    webapp_parser.add_argument("--path", default=".", help="Path to create the web application")

    # dbschema command
    dbschema_parser = subparsers.add_parser("dbschema", help="Generate a database schema")
    dbschema_parser.add_argument("--db-type", default="sqlite", help="Database type (sqlite, mysql, postgresql, mongodb)")
    dbschema_parser.add_argument("--name", default="database", help="Name of the database schema")
    dbschema_parser.add_argument("--path", default=".", help="Path to create the database schema")

    # apispec command
    apispec_parser = subparsers.add_parser("apispec", help="Generate an API specification")
    apispec_parser.add_argument("--api-type", default="rest", help="API type (rest, graphql, grpc)")
    apispec_parser.add_argument("--format", dest="format_type", default="openapi", help="API specification format (openapi, raml, graphql, etc.)")
    apispec_parser.add_argument("--name", default="api", help="Name of the API")
    apispec_parser.add_argument("--path", default=".", help="Path to create the API specification")

    # requirements command
    requirements_parser = subparsers.add_parser("requirements", help="Manage requirements with dialectical reasoning")
    requirements_parser.add_argument("--action", help="Action to perform (list, show, create, update, delete, changes, approve-change, reject-change, chat, sessions, continue-chat, evaluate-change, assess-impact)")
    requirements_parser.add_argument("--id", help="ID of the requirement, change, or session")
    requirements_parser.add_argument("--user", default="admin", help="ID of the user")
    requirements_parser.add_argument("--reason", help="Reason for the action")
    requirements_parser.add_argument("--comment", help="Comment for the action")
    requirements_parser.add_argument("--title", help="Title of the requirement")
    requirements_parser.add_argument("--description", help="Description of the requirement")
    requirements_parser.add_argument("--status", help="Status of the requirement")
    requirements_parser.add_argument("--priority", help="Priority of the requirement")
    requirements_parser.add_argument("--type", help="Type of the requirement")

    # help command
    subparsers.add_parser("help", help="Display help information")

    return parser.parse_args(args)

def run_cli():
    """Entry point for the CLI application."""
    if len(sys.argv) == 1 or sys.argv[1] == "help":
        show_help()
        return

    try:
        args = parse_args(sys.argv[1:])

        if args.command == "init":
            init_cmd(args.path)
        elif args.command == "analyze":
            analyze_cmd(args.input, args.interactive)
        elif args.command == "analyze-code":
            analyze_code_cmd(args.path)
        elif args.command == "spec":
            spec_cmd(args.requirements_file)
        elif args.command == "test":
            test_cmd(args.spec_file)
        elif args.command == "code":
            code_cmd()
        elif args.command == "run":
            run_cmd(args.target)
        elif args.command == "config":
            config_cmd(args.key, args.value, args.list_models)
        elif args.command == "webapp":
            webapp_cmd(args.framework, args.name, args.path)
        elif args.command == "dbschema":
            dbschema_cmd(args.db_type, args.name, args.path)
        elif args.command == "apispec":
            apispec_cmd(args.api_type, args.format_type, args.name, args.path)
        elif args.command == "requirements":
            # Import the LLM service for the dialectical reasoner
            from devsynth.adapters.llm.lmstudio_provider import LMStudioProvider
            from devsynth.application.cli.requirements_commands import initialize_services
            
            # Initialize the LLM service
            llm_service = LMStudioProvider()
            
            # Initialize the requirements services
            initialize_services(llm_service)
            
            # Run the requirements command
            if args.action == "list":
                from devsynth.application.cli.requirements_commands import list_requirements
                list_requirements()
            elif args.action == "show":
                from devsynth.application.cli.requirements_commands import show_requirement
                show_requirement(args.id)
            elif args.action == "create":
                from devsynth.application.cli.requirements_commands import create_requirement
                create_requirement(args.title, args.description, args.status, args.priority, args.type, args.user)
            elif args.action == "update":
                from devsynth.application.cli.requirements_commands import update_requirement
                update_requirement(args.id, args.title, args.description, args.status, args.priority, args.type, args.reason, args.user)
            elif args.action == "delete":
                from devsynth.application.cli.requirements_commands import delete_requirement
                delete_requirement(args.id, args.reason, args.user)
            elif args.action == "changes":
                from devsynth.application.cli.requirements_commands import list_changes
                list_changes(args.id)
            elif args.action == "approve-change":
                from devsynth.application.cli.requirements_commands import approve_change
                approve_change(args.id, args.user)
            elif args.action == "reject-change":
                from devsynth.application.cli.requirements_commands import reject_change
                reject_change(args.id, args.comment, args.user)
            elif args.action == "chat":
                from devsynth.application.cli.requirements_commands import start_chat
                start_chat(args.id, args.user)
            elif args.action == "sessions":
                from devsynth.application.cli.requirements_commands import list_chat_sessions
                list_chat_sessions(args.user)
            elif args.action == "continue-chat":
                from devsynth.application.cli.requirements_commands import continue_chat
                continue_chat(args.id, args.user)
            elif args.action == "evaluate-change":
                from devsynth.application.cli.requirements_commands import evaluate_change
                evaluate_change(args.id, args.user)
            elif args.action == "assess-impact":
                from devsynth.application.cli.requirements_commands import assess_impact
                assess_impact(args.id, args.user)
            else:
                console.print("[yellow]Please specify an action for the requirements command.[/yellow]")
                console.print("Available actions: list, show, create, update, delete, changes, approve-change, reject-change, chat, sessions, continue-chat, evaluate-change, assess-impact")
        else:
            show_help()
    except argparse.ArgumentError:
        # Handle invalid command
        show_help()
    except SystemExit:
        # Catch SystemExit from argparse and show help instead
        show_help()
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
