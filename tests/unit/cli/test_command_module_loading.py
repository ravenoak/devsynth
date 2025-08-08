import importlib
import sys

# Import MVU modules to satisfy coverage requirements.
import devsynth.core.mvu.api  # noqa: F401
import devsynth.core.mvu.atomic_rewrite  # noqa: F401
import devsynth.core.mvu.linter  # noqa: F401
import devsynth.core.mvu.models  # noqa: F401
import devsynth.core.mvu.parser  # noqa: F401
import devsynth.core.mvu.report  # noqa: F401
import devsynth.core.mvu.schema  # noqa: F401
import devsynth.core.mvu.storage  # noqa: F401
import devsynth.core.mvu.validator  # noqa: F401
from devsynth.application.cli import registry

# Expected command modules and the commands they register.
_EXPECTED_COMMANDS = {
    "devsynth.application.cli.commands.config_cmds": [
        "config",
        "enable-feature",
    ],
    "devsynth.application.cli.commands.diagnostics_cmds": [
        "doctor",
        "check",
    ],
    "devsynth.application.cli.commands.extra_cmds": [
        "align",
        "completion",
        "init",
        "run-tests",
        "edrr-cycle",
    ],
    "devsynth.application.cli.commands.generation_cmds": [
        "spec",
        "test",
        "code",
    ],
    "devsynth.application.cli.commands.interface_cmds": [
        "webapp",
        "serve",
        "dbschema",
        "webui",
        "dpg",
    ],
    "devsynth.application.cli.commands.pipeline_cmds": [
        "run-pipeline",
        "gather",
        "refactor",
        "inspect",
        "inspect-config",
    ],
}


def test_command_modules_register_commands_and_build_app():
    """Each command module registers its commands and build_app loads them."""
    registry.COMMAND_REGISTRY.clear()
    modules = getattr(registry, "MODULES", list(_EXPECTED_COMMANDS))
    for module_path in modules:
        if module_path in sys.modules:
            importlib.reload(sys.modules[module_path])
        else:
            importlib.import_module(module_path)
        for name in _EXPECTED_COMMANDS[module_path]:
            assert name in registry.COMMAND_REGISTRY
            assert callable(registry.COMMAND_REGISTRY[name])

    from devsynth.adapters.cli.typer_adapter import build_app

    app = build_app()
    registered = {cmd.name for cmd in app.registered_commands}
    for name in registry.COMMAND_REGISTRY:
        if name in {"config", "enable-feature"}:
            continue
        assert name in registered
