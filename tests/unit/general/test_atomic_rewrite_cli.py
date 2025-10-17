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
    from devsynth.application.cli.commands import atomic_rewrite_cmd

    monkeypatch.setattr(atomic_rewrite_cmd, "is_enabled", lambda name: name == "atomic_rewrite")

    # Mock the git import to avoid needing a real git repository
    import devsynth.core.mvu.atomic_rewrite as ar
    import importlib

    class DummyRepo:
        def __init__(self, wd):
            self.working_dir = str(wd)

    def mock_rewrite_history(target_path, branch_name, dry_run=False):
        return DummyRepo(target_path)

    # Mock the importlib.import_module call for 'git'
    original_import = importlib.import_module

    def mock_import(name):
        if name == "git":
            # Create a mock git module with a Repo class
            import types
            git_mock = types.ModuleType("git")
            git_mock.Repo = lambda path: DummyRepo(path)
            return git_mock
        return original_import(name)

    monkeypatch.setattr("importlib.import_module", mock_import)
    monkeypatch.setattr(ar, "rewrite_history", mock_rewrite_history)

    result = runner.invoke(
        app, ["atomic-rewrite", "--path", str(tmp_path), "--dry-run"]
    )
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    print(f"Exception: {result.exception}")
    assert result.exit_code == 0
    assert "dry run" in result.output.lower()
