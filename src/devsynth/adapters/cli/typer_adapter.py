import importlib
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from typing_extensions import Literal

import click
import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from typer import completion as typer_completion

# Ensure CLI commands are registered before using the registry
import devsynth.application.cli
from devsynth.application.cli.registry import COMMAND_REGISTRY

# Trigger command registration by accessing a command that will call __getattr__
_ = devsynth.application.cli.run_tests_cmd
# config_app will be imported just before use
from devsynth.core.config_loader import load_config
from devsynth.interface.cli import COLORBLIND_THEME, DEVSYNTH_THEME, CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge, sanitize_output
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import register_dashboard_hook

if os.environ.get("DEVSYNTH_CLI_MINIMAL") == "1":  # pragma: no cover - env shim
    requirements_app = typer.Typer(
        help="Requirements commands disabled in minimal mode"
    )
    vcs_app = typer.Typer(help="VCS commands disabled in minimal mode")
    mvu_app = typer.Typer(help="MVUU commands disabled in minimal mode")
else:
    from devsynth.application.cli.mvu_commands import mvu_app
    from devsynth.application.cli.requirements_commands import requirements_app
    from devsynth.application.cli.vcs_commands import vcs_app


@dataclass(slots=True)
class CLIThemeOptions:
    """Shared theme configuration propagated from Typer callbacks."""

    colorblind_mode: bool = False
    overrides: Dict[str, str] = field(default_factory=dict)


def _ensure_ctx_state(ctx: typer.Context) -> Dict[str, Any]:
    if ctx.obj is None:
        ctx.obj = {}
    return ctx.obj


def _set_theme_options(ctx: typer.Context, theme: CLIThemeOptions) -> None:
    state = _ensure_ctx_state(ctx)
    state["theme"] = theme


def _get_theme_options(ctx: typer.Context | None) -> CLIThemeOptions:
    if ctx is None or ctx.obj is None:
        return CLIThemeOptions()
    theme = ctx.obj.get("theme")  # type: ignore[assignment]
    if isinstance(theme, CLIThemeOptions):
        return theme
    return CLIThemeOptions()


def _create_textual_bridge(
    theme: CLIThemeOptions,
    *,
    require_textual: bool,
) -> UXBridge:
    try:
        from devsynth.interface import TextualUXBridge, TEXTUAL_AVAILABLE
    except Exception as exc:  # pragma: no cover - degraded optional import
        raise typer.BadParameter("Textual bridge is unavailable.") from exc

    if require_textual and not TEXTUAL_AVAILABLE:
        raise typer.BadParameter(
            "Install the 'textual' extra to launch the DevSynth TUI."
        )

    bridge = TextualUXBridge(
        require_textual=require_textual,
        colorblind_mode=theme.colorblind_mode,
        theme_overrides=theme.overrides,
    )
    configure = getattr(bridge, "configure_theme", None)
    if callable(configure):
        configure(
            colorblind_mode=theme.colorblind_mode,
            theme_overrides=theme.overrides,
        )
    return bridge


def _run_bridge_event_loop(bridge: UXBridge) -> None:
    run_loop = getattr(bridge, "run_event_loop", None)
    if callable(run_loop):
        try:
            run_loop()
        except RuntimeError as exc:  # pragma: no cover - user feedback path
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc


def init_cmd(
    ctx: typer.Context,
    wizard: bool = False,
    *,
    tui: bool = typer.Option(
        False,
        "--tui/--no-tui",
        help="Launch the setup wizard with the Textual interface.",
    ),
    bridge: UXBridge | None = None,
) -> None:
    """Dispatch the init command, optionally routing through the Textual TUI."""

    theme = _get_theme_options(ctx)

    if tui:
        active_bridge = bridge or _create_textual_bridge(theme, require_textual=True)
        COMMAND_REGISTRY["init"](wizard=True, bridge=active_bridge)
        _run_bridge_event_loop(active_bridge)
        return

    COMMAND_REGISTRY["init"](wizard=wizard, bridge=bridge)


def spec_cmd(
    requirements_file: str = "requirements.md", *, bridge: UXBridge | None = None
) -> None:
    from devsynth.application.cli import cli_commands
    from devsynth.application.cli.commands import spec_cmd as _spec_module

    _spec_module.generate_specs = cli_commands.generate_specs
    COMMAND_REGISTRY["spec"](requirements_file=requirements_file, bridge=bridge)


def test_cmd(spec_file: str = "specs.md", *, bridge: UXBridge | None = None) -> None:
    COMMAND_REGISTRY["test"](spec_file=spec_file, bridge=bridge)


def code_cmd(*, bridge: UXBridge | None = None) -> None:
    COMMAND_REGISTRY["code"](bridge=bridge)


def run_pipeline_cmd(
    *,
    target: str | None = None,
    report: str | None = None,
    bridge: UXBridge | None = None,
) -> None:
    COMMAND_REGISTRY["run-pipeline"](target=target, report=report, bridge=bridge)


def inspect_config_cmd(
    path: str | None = None, update: bool = False, prune: bool = False
) -> None:
    COMMAND_REGISTRY["inspect-config"](path=path, update=update, prune=prune)


def _patch_typer_types() -> None:
    """Allow Typer to handle custom parameter annotations used in the CLI."""

    orig = typer.main.get_click_type

    def patched_get_click_type(
        annotation: Any, parameter_info: typer.models.ParameterInfo
    ) -> click.types.ParamType:
        if annotation in {UXBridge, typer.models.Context, Any}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if origin in {UXBridge, typer.models.Context, Any}:
            return click.STRING
        try:
            return orig(annotation=annotation, parameter_info=parameter_info)
        except RuntimeError:
            return click.STRING

    typer.main.get_click_type = patched_get_click_type

    orig_get_click_param = typer.main.get_click_param

    def _is_optional_union(annotation: Any) -> Tuple[bool, Tuple[Any, ...]]:
        try:
            origin = typer.main.get_origin(annotation)
        except Exception:  # pragma: no cover - defensive
            return False, ()
        if origin is None:
            return False, ()
        if not typer.main.is_union(origin):
            return False, ()
        try:
            args = tuple(typer.main.get_args(annotation))
        except Exception:  # pragma: no cover - defensive
            return False, ()
        non_none = tuple(arg for arg in args if arg is not typer.main.NoneType)
        return True, non_none

    def patched_get_click_param(
        param: typer.models.ParamMeta,
    ) -> tuple[click.Parameter, Any]:
        original_annotation = getattr(param, "annotation", typer.main.ParamMeta.empty)
        should_restore = False
        if original_annotation is not typer.main.ParamMeta.empty:
            is_union, non_none_args = _is_optional_union(original_annotation)
            if is_union and len(non_none_args) > 1:
                logger.info(
                    "Typer union fallback for parameter '%s' with annotation %r",
                    getattr(param, "name", "<unknown>"),
                    original_annotation,
                )
                param.annotation = non_none_args[0]
                should_restore = True
        try:
            logger.debug(
                "Building click parameter '%s' with annotation %r and default %r",
                getattr(param, "name", "<unknown>"),
                getattr(param, "annotation", None),
                getattr(param, "default", None),
            )
            return orig_get_click_param(param)
        except Exception as exc:  # pragma: no cover - diagnostic aid
            logger.error(
                "Failed to build click parameter '%s' with annotation %r: %s",
                getattr(param, "name", "<unknown>"),
                getattr(param, "annotation", None),
                exc,
            )
            raise
        finally:
            if should_restore:
                param.annotation = original_annotation

    typer.main.get_click_param = patched_get_click_param


logger = DevSynthLogger(__name__)


class EnhancedHelpFormatter(click.HelpFormatter):
    """Custom help formatter that provides enhanced Rich-based output."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.console = Console(theme=DEVSYNTH_THEME)

    def write_usage(self, prog: str, args: str = "", prefix: str = "Usage: ") -> None:
        """Write the usage line with enhanced formatting."""
        usage_text = f"{prefix}{prog} {args}"

        # Use Rich to format the usage text
        panel = Panel(usage_text, title="Command Usage", border_style="cyan")
        self.console.print(panel)

    def write_heading(self, heading: str) -> None:
        """Write a heading with enhanced formatting."""
        # Use Rich to format the heading
        self.console.print(f"\n[bold blue]{heading}[/bold blue]")

    def write_paragraph(self) -> None:
        """Write a paragraph separator."""
        self.console.print("")

    def write_text(self, text: str) -> None:
        """Write text with enhanced formatting."""
        # Use Rich to format the text
        if text.startswith("  "):
            # Indented text (usually option descriptions)
            self.console.print(text)
        else:
            # Regular text
            self.console.print(text)

    def write_dl(
        self,
        rows: Iterable[tuple[str, str]],
        col_max: int = 30,
        col_spacing: int = 2,
    ) -> None:
        """Write a definition list with enhanced formatting."""
        # Create a Rich table for the definition list
        table = Table(box=ROUNDED, show_header=False, expand=True)
        table.add_column("Option", style="cyan", width=col_max)
        table.add_column("Description", style="white")

        for option, description in rows:
            table.add_row(option, description)

        self.console.print(table)


class CommandHelp:
    """Container for enhanced command help information."""

    def __init__(
        self,
        summary: str,
        description: str | None = None,
        examples: list[dict[str, str]] | None = None,
        notes: list[str] | None = None,
        options: dict[str, str] | None = None,
    ) -> None:
        """Initialize the command help."""

        self.summary = summary
        self.description = description or ""
        self.examples = examples or []
        self.notes = notes or []
        self.options = options or {}

    @staticmethod
    def _sanitize(value: str) -> str:
        return sanitize_output(value) if value else ""

    def format(self) -> str:
        """Format the help text for Typer integration."""

        parts = [self._sanitize(self.summary)]

        if self.description:
            parts.extend(["", self._sanitize(self.description)])

        if self.examples:
            parts.append("")
            parts.append("Examples:")
            for example in self.examples:
                command = self._sanitize(example.get("command", ""))
                parts.append(f"  $ {command}")
                description = example.get("description")
                if description:
                    parts.append(f"      {self._sanitize(description)}")

        if self.notes:
            parts.append("")
            parts.append("Notes:")
            for note in self.notes:
                parts.append(f"  • {self._sanitize(note)}")

        if self.options:
            parts.append("")
            parts.append("Options:")
            for option, description in self.options.items():
                parts.append(
                    f"  {self._sanitize(option)}: {self._sanitize(description)}"
                )

        return "\n".join(parts)

    def as_markdown(self) -> Markdown:
        """Return the help content as Markdown."""

        lines = [f"# {self._sanitize(self.summary)}"]

        if self.description:
            lines.extend(["", self._sanitize(self.description)])

        if self.examples:
            lines.extend(["", "## Examples"])
            for example in self.examples:
                command = self._sanitize(example.get("command", ""))
                description = self._sanitize(example.get("description", ""))
                lines.append(f"- `{command}`")
                if description:
                    lines.append(f"  - {description}")

        if self.notes:
            lines.extend(["", "## Notes"])
            for note in self.notes:
                lines.append(f"- {self._sanitize(note)}")

        if self.options:
            lines.extend(["", "## Options"])
            for option, description in self.options.items():
                lines.append(
                    f"- `{self._sanitize(option)}`: {self._sanitize(description)}"
                )

        return Markdown("\n".join(lines))

    def as_panel(self, title: str = "DevSynth CLI") -> Panel:
        """Create a panel suitable for Rich console output."""

        return Panel(self.as_markdown(), title=title, border_style="cyan")

    def as_notes_panel(self) -> Panel | None:
        """Create a supplemental notes panel when notes are available."""

        if not self.notes:
            return None

        notes_table = Table.grid(padding=(0, 1))
        notes_table.add_column()
        for note in self.notes:
            notes_table.add_row(Text(f"• {self._sanitize(note)}", style="note"))

        return Panel(notes_table, title="Notes", border_style="magenta")


MAIN_COMMAND_HELP = CommandHelp(
    summary="DevSynth CLI - automate iterative 'Expand, Differentiate, Refine, Retrace' workflows.",
    description=(
        "DevSynth is a tool for automating software development workflows using "
        "the EDRR (Expand, Differentiate, Refine, Retrace) methodology. It helps "
        "you generate specifications from requirements, tests from specifications, "
        "and code from tests, all while maintaining traceability and alignment."
    ),
    examples=[
        {
            "command": "devsynth init",
            "description": "Initialize a new project in the current directory",
        },
        {
            "command": "devsynth spec --requirements-file requirements.md",
            "description": "Generate specifications from requirements",
        },
        {
            "command": "devsynth test --spec-file specs.md",
            "description": "Generate tests from specifications",
        },
        {"command": "devsynth code", "description": "Generate code from tests"},
        {
            "command": "devsynth tui",
            "description": "Launch the Textual TUI for guided wizards",
        },
        {
            "command": "devsynth run-pipeline --target unit-tests",
            "description": "Execute the generated code",
        },
    ],
    notes=[
        "Only the embedded ChromaDB backend is currently supported.",
        "Use 'devsynth <command> --help' for more information on a specific command.",
        "Configuration can be managed with 'devsynth config' commands.",
        "Shell completion is available via '--install-completion' or the 'completion' command.",
        "Long-running commands display progress indicators for better feedback.",
        "Dashboard metric hooks can be registered with '--dashboard-hook module:function'.",
        "Enable the colorblind-friendly palette with '--colorblind' or the DEVSYNTH_CLI_COLORBLIND environment variable.",
    ],
)


def build_app() -> typer.Typer:
    """Create a Typer application with all commands registered."""
    _patch_typer_types()

    app = typer.Typer(
        help=MAIN_COMMAND_HELP.format(),
        context_settings={"help_option_names": ["--help", "-h"]},
    )

    for name, cmd in COMMAND_REGISTRY.items():
        if name in {"config", "enable-feature"}:
            continue
        override = globals().get(f"{name.replace('-', '_')}_cmd", cmd)
        app.command(name)(override)

    app.add_typer(requirements_app, name="requirements")
    app.add_typer(mvu_app, name="mvu")
    app.add_typer(vcs_app, name="vcs", help="Git / VCS utilities")

    # Import config_app just before use to ensure lazy loading
    from devsynth.application.cli import config_app

    app.add_typer(config_app, name="config", help="Manage configuration settings")

    @app.command(
        "completion",
        help="Show or install shell completion scripts (see scripts/completions).",
    )
    def completion(
        shell: str | None = typer.Option(None, "--shell", help="Shell type"),
        install: bool = typer.Option(
            False, "--install", help="Install completion script"
        ),
        path: Path | None = typer.Option(None, "--path", help="Installation path"),
    ) -> None:
        completion_cmd(
            shell=shell, install=install, path=path
        )  # nosec B604: shell arg selects completion target

    @app.command(
        "tui",
        help="Launch the Textual interface for DevSynth wizards.",
    )
    def tui_command(
        ctx: typer.Context,
        wizard: str = typer.Option(
            "init",
            "--wizard",
            "-w",
            help="Wizard to launch (init or requirements).",
            show_default=True,
        ),
        requirements_output: Path = typer.Option(
            Path("requirements_wizard.json"),
            "--requirements-output",
            help="Output file when running the requirements wizard.",
        ),
    ) -> None:
        """Start the Textual UI with the configured theme settings."""

        theme = _get_theme_options(ctx)
        bridge = _create_textual_bridge(theme, require_textual=True)
        wizard_name = wizard.strip().lower()

        if wizard_name == "init":
            COMMAND_REGISTRY["init"](wizard=True, bridge=bridge)
        elif wizard_name in {"requirements", "requirement"}:
            from devsynth.application.cli.config import CLIConfig
            from devsynth.application.requirements.wizard import requirements_wizard

            requirements_wizard(
                bridge,
                output_file=str(requirements_output),
                config=CLIConfig(non_interactive=False),
            )
        else:
            raise typer.BadParameter(
                "Wizard must be 'init' or 'requirements'."
            )

        _run_bridge_event_loop(bridge)

    @app.callback(invoke_without_command=True)
    def main(
        ctx: typer.Context,
        dashboard_hook: str | None = typer.Option(
            None,
            "--dashboard-hook",
            help="Python path to function receiving dashboard metric events",
        ),
        version: bool = typer.Option(  # global eager flag
            False,
            "--version",
            help="Show DevSynth version and exit",
            is_eager=True,
            callback=None,
        ),
        debug: bool = typer.Option(
            False,
            "--debug",
            help="Enable debug logging (equivalent to --log-level DEBUG)",
            is_eager=True,
        ),
        log_level: str | None = typer.Option(
            None,
            "--log-level",
            help="Set log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
            is_eager=True,
        ),
        colorblind: bool = typer.Option(
            False,
            "--colorblind/--no-colorblind",
            help="Use the colorblind-friendly theme across CLI and TUI output.",
            envvar="DEVSYNTH_CLI_COLORBLIND",
        ),
    ) -> None:
        # Handle --version eagerly
        # Configure logging as early as possible using flags/env
        import logging as _logging
        import os

        from devsynth.logging_setup import configure_logging

        # If DEVSYNTH_DEBUG is set and log_level not provided, treat as debug
        env_debug = os.environ.get("DEVSYNTH_DEBUG", "").lower() in {"1", "true", "yes"}
        chosen_level = None
        if log_level:
            chosen_level = log_level.strip().upper()
        elif debug or env_debug:
            chosen_level = "DEBUG"
        else:
            # fall back to env DEVSYNTH_LOG_LEVEL or default inside configure_logging
            chosen_level = os.environ.get("DEVSYNTH_LOG_LEVEL")

        if chosen_level:
            # Persist to env for child processes and consistency
            os.environ["DEVSYNTH_LOG_LEVEL"] = chosen_level
            try:
                configure_logging(
                    log_level=getattr(_logging, chosen_level, _logging.INFO)
                )
            except Exception:
                # Do not crash CLI due to logging issues
                pass

        # Handle --version eagerly after logging configured
        if version:
            try:
                from devsynth import __version__
            except Exception:  # pragma: no cover - defensive fallback
                __version__ = "unknown"
            typer.echo(__version__)
            raise typer.Exit(0)

        if dashboard_hook:
            try:
                module_name, func_name = dashboard_hook.split(":", 1)
                hook = getattr(importlib.import_module(module_name), func_name)
                register_dashboard_hook(hook)
            except Exception:
                typer.echo(
                    f"Failed to load dashboard hook '{dashboard_hook}'", err=True
                )

        theme = CLIThemeOptions(colorblind_mode=colorblind)
        _set_theme_options(ctx, theme)
        os.environ["DEVSYNTH_CLI_COLORBLIND"] = "1" if colorblind else "0"

        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit()

    # Enable Typer's built-in completion if available
    if hasattr(app, "add_completion"):
        app.add_completion()
    else:  # pragma: no cover - compatibility for older Typer versions
        method = getattr(app, "_add_completion", None)
        if callable(method):
            try:
                method()
            except Exception:
                pass
    return app


# Provide a default app instance for convenience
app = build_app()


def _warn_if_features_disabled() -> None:
    """Emit a notice when all feature flags are disabled."""
    try:
        cfg = load_config()
        features = cfg.features or {}
        if features and not any(features.values()):
            typer.echo(
                "All optional features are disabled. Enable with 'devsynth config enable-feature <name>'."
            )
    except Exception:
        # Don't fail the CLI if the config can't be read
        logger.debug("Failed to read feature flags for warning message")


def _extract_commands(typer_obj: Any) -> list[Any]:
    """Return registered commands from a Typer instance."""

    if typer_obj is None:
        return []

    for attr in ("registered_commands", "commands"):
        commands = getattr(typer_obj, attr, None)
        if commands:
            return list(commands)
    return []


def _command_name(command: Any) -> str:
    """Return the command name as a safe string."""

    value = getattr(command, "name", "") or ""
    return str(value)


def _get_command_groups(app: Any) -> list[SimpleNamespace]:
    """Collect metadata about registered command groups."""

    groups: list[SimpleNamespace] = []
    registered_groups = getattr(app, "registered_groups", None)
    if registered_groups:
        for group in registered_groups:
            typer_instance = getattr(group, "typer_instance", None)
            help_text = getattr(group, "help", "") or getattr(
                getattr(typer_instance, "info", None), "help", ""
            )
            groups.append(
                SimpleNamespace(
                    name=str(getattr(group, "name", "") or ""),
                    help=help_text,
                    commands=_extract_commands(typer_instance),
                )
            )
    elif hasattr(app, "registered_typers"):
        for typer_instance, name in getattr(app, "registered_typers"):
            help_text = getattr(getattr(typer_instance, "info", None), "help", "")
            groups.append(
                SimpleNamespace(
                    name=str(name or ""),
                    help=help_text,
                    commands=_extract_commands(typer_instance),
                )
            )

    return groups


def _format_command_entry(name: str, description: str | None) -> Text:
    """Return a styled Rich Text entry for a command."""

    safe_name = sanitize_output(str(name or ""))
    label = Text(safe_name, style="command")
    if description:
        label.append(" – ", style="dim")
        label.append(sanitize_output(str(description)), style="info")
    return label


def _format_group_label(name: str, description: str | None) -> Text:
    """Return a styled label for a command group."""

    label = Text(sanitize_output(name), style="section")
    if description:
        label.append(" – ", style="dim")
        label.append(sanitize_output(description), style="info")
    return label


def _build_command_tree(app: Any, filter_set: set[str] | None) -> Tree:
    """Create a Rich tree describing available commands."""

    tree = Tree(Text("Commands", style="heading"), guide_style="dim")
    commands = getattr(app, "registered_commands", []) or []
    for command in sorted(commands, key=lambda c: _command_name(c).lower()):
        tree.add(
            _format_command_entry(
                _command_name(command), getattr(command, "help", "")
            )
        )

    for group in _get_command_groups(app):
        group_name = str(group.name or "")
        if filter_set and group_name.lower() not in filter_set:
            continue
        branch = tree.add(_format_group_label(group_name, group.help))
        for sub_command in sorted(
            group.commands, key=lambda c: _command_name(c).lower()
        ):
            branch.add(
                _format_command_entry(
                    _command_name(sub_command), getattr(sub_command, "help", "")
                )
            )

    return tree


def _build_command_table(app: Any, filter_set: set[str] | None) -> Table:
    """Create a Rich table of commands and descriptions."""

    table = Table(
        title="Available Commands",
        box=ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Command", style="command")
    table.add_column("Description", style="info")

    for command in sorted(
        getattr(app, "registered_commands", []), key=lambda c: _command_name(c).lower()
    ):
        table.add_row(
            Text(sanitize_output(_command_name(command)), style="command"),
            Text(
                sanitize_output(str(getattr(command, "help", "") or "")),
                style="info",
            ),
        )

    for group in _get_command_groups(app):
        group_name = str(group.name or "")
        if filter_set and group_name.lower() not in filter_set:
            continue
        label = Text(sanitize_output(group_name), style="section")
        description = Text(
            sanitize_output(str(group.help or "")), style="info"
        )
        table.add_row(label, description)

    return table


def show_help(
    render_mode: Literal["layout", "tree", "table"] = "layout",
    *,
    group_filter: Sequence[str] | None = None,
) -> None:
    """Display the CLI help message with enhanced formatting."""

    colorblind_env = os.environ.get("DEVSYNTH_CLI_COLORBLIND", "0").lower()
    colorblind_mode = colorblind_env in {"1", "true", "yes"}
    theme = COLORBLIND_THEME if colorblind_mode else DEVSYNTH_THEME
    console = Console(theme=theme)

    if render_mode not in {"layout", "tree", "table"}:
        raise ValueError(f"Unsupported help render mode: {render_mode}")

    app = build_app()
    filter_set = {name.lower() for name in group_filter} if group_filter else None

    overview_panel = MAIN_COMMAND_HELP.as_panel(title="DevSynth CLI")
    commands_renderable = (
        _build_command_tree(app, filter_set)
        if render_mode in {"layout", "tree"}
        else _build_command_table(app, filter_set)
    )
    notes_panel = MAIN_COMMAND_HELP.as_notes_panel()
    footer = Text(
        "Use 'devsynth [COMMAND] --help' for more information on a command.",
        style="info",
    )

    if render_mode == "layout":
        layout = Layout(name="root")
        layout.split(
            Layout(overview_panel, name="overview", size=15),
            Layout(name="body"),
        )
        if notes_panel:
            layout["body"].split_row(
                Layout(commands_renderable, name="commands", ratio=3),
                Layout(notes_panel, name="notes", ratio=2),
            )
        else:
            layout["body"].update(commands_renderable)
        console.print(layout)
    else:
        console.print(overview_panel)
        console.print(commands_renderable)
        if notes_panel:
            console.print(notes_panel)

    console.print(footer)

    logger.info("Commands:")
    logger.info("Run 'devsynth [COMMAND] --help' for more information on a command.")


def _format_cli_error(message: str, *, kind: str) -> str:
    """Normalize CLI error messages for actionable, concise output.

    Args:
        message: Raw error text
        kind: One of {"usage", "runtime"}
    """
    prefix = "Usage error" if kind == "usage" else "Error"
    sanitized = sanitize_output(str(message))
    # Keep messages concise; add a single actionable hint.
    hint = (
        "Run 'devsynth --help' for usage."
        if kind == "usage"
        else "Re-run with --help for usage or check logs."
    )
    return f"{prefix}: {sanitized}\n{hint}"


def parse_args(args: list[str]) -> None:
    """Parse command line arguments and execute the CLI.

    Exit codes:
    - 0: Success
    - 1: Runtime or unexpected error
    - 2: Usage or argument error
    """
    _warn_if_features_disabled()
    try:
        build_app()(args)
    except (click.UsageError, click.BadParameter) as e:
        typer.echo(_format_cli_error(str(e), kind="usage"), err=True)
        raise typer.Exit(2)
    except SystemExit:
        # Let explicit exits propagate (e.g., --help)
        raise
    except Exception as e:  # pragma: no cover - generic safety net
        typer.echo(_format_cli_error(str(e), kind="runtime"), err=True)
        raise typer.Exit(1)


def run_cli() -> None:
    """Entry point for the Typer application.

    Exit codes:
    - 0: Success
    - 1: Runtime or unexpected error
    - 2: Usage or argument error
    """
    _warn_if_features_disabled()
    try:
        build_app()()
    except (click.UsageError, click.BadParameter) as e:
        typer.echo(_format_cli_error(str(e), kind="usage"), err=True)
        raise typer.Exit(2)
    except SystemExit:
        # Let explicit exits propagate (e.g., --help)
        raise
    except Exception as e:  # pragma: no cover - generic safety net
        typer.echo(_format_cli_error(str(e), kind="runtime"), err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    run_cli()
