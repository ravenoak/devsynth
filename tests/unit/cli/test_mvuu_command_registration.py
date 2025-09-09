import pytest

from devsynth.adapters.cli.typer_adapter import build_app


@pytest.mark.fast
def test_mvuu_dashboard_command_registered():
    """The mvuu-dashboard command should be registered in the CLI.

    ReqID: CLI-CMD-REGISTER-MVUU
    """
    app = build_app()
    command_names = {cmd.name for cmd in app.registered_commands}
    assert "mvuu-dashboard" in command_names
