import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app

runner = CliRunner()


@pytest.mark.fast
def test_atomic_rewrite_help_shows_command():
    app = build_app()
    result = runner.invoke(app, ["atomic-rewrite", "--help"])
    assert result.exit_code == 0
    # Typer help should include the command name
    assert "atomic-rewrite" in result.output


@pytest.mark.fast
def test_atomic_rewrite_disabled_exits_with_guidance(monkeypatch):
    app = build_app()
    # Ensure flag is reported disabled
    import devsynth.core.feature_flags as ff

    monkeypatch.setattr(ff, "is_enabled", lambda name: False)

    result = runner.invoke(app, ["atomic-rewrite", "--dry-run"])
    assert result.exit_code == 2
    assert "Enable with" in result.output


@pytest.mark.fast
def test_atomic_rewrite_enabled_dry_run_succeeds(monkeypatch, tmp_path):
    app = build_app()

    # Enable the feature flag via monkeypatch
    import devsynth.core.feature_flags as ff

    monkeypatch.setattr(ff, "is_enabled", lambda name: name == "atomic_rewrite")

    # Create a temporary git repo structure minimally; we will monkeypatch rewrite to avoid real git
    from devsynth.core.mvu import atomic_rewrite as ar

    class DummyRepo:
        def __init__(self, wd):
            self.working_dir = str(wd)

    monkeypatch.setattr(
        ar, "rewrite_history", lambda p, b, dry_run=False: DummyRepo(tmp_path)
    )

    result = runner.invoke(
        app, ["atomic-rewrite", "--path", str(tmp_path), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "dry run" in result.output.lower()
