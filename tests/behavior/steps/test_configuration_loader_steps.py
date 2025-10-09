from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.config.unified_loader import UnifiedConfig, UnifiedConfigLoader
from devsynth.exceptions import ConfigurationError
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "configuration_loader.feature"))


@dataclass
class LoaderContext:
    """Shared state for configuration loader scenarios."""

    root: Path
    result: UnifiedConfig | None = None
    error: ConfigurationError | None = None


@pytest.fixture
def loader_context(tmp_path: Path) -> LoaderContext:
    """Provide an isolated project root for each scenario."""

    return LoaderContext(root=tmp_path)


@given("a temporary project root")
def given_temporary_project_root(loader_context: LoaderContext) -> None:
    assert loader_context.root.exists(), "Temporary project root should exist"


@given("a pyproject file without a DevSynth section")
def given_pyproject_without_section(loader_context: LoaderContext) -> None:
    (loader_context.root / "pyproject.toml").write_text("[project]\nname = 'demo'\n")


@given(parsers.parse('a YAML configuration with language "{language}"'))
def given_yaml_configuration(loader_context: LoaderContext, language: str) -> None:
    cfg_dir = loader_context.root / ".devsynth"
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "project.yaml").write_text(f"language: {language}\n")


@given("a malformed pyproject configuration")
def given_malformed_pyproject(loader_context: LoaderContext) -> None:
    (loader_context.root / "pyproject.toml").write_text(
        "[tool.devsynth\nlanguage = 'python'\n"
    )


@when("I load the unified configuration")
def when_load_configuration(loader_context: LoaderContext) -> None:
    loader_context.error = None
    loader_context.result = UnifiedConfigLoader.load(loader_context.root)


@when("I attempt to load the unified configuration")
def when_attempt_load(loader_context: LoaderContext) -> None:
    loader_context.error = None
    try:
        loader_context.result = UnifiedConfigLoader.load(loader_context.root)
    except ConfigurationError as exc:
        loader_context.error = exc
        loader_context.result = None


@then("the loader should report it uses YAML")
def then_loader_uses_yaml(loader_context: LoaderContext) -> None:
    assert loader_context.result is not None, "Expected configuration to load"
    assert loader_context.result.use_pyproject is False
    assert (
        loader_context.result.path == loader_context.root / ".devsynth" / "project.yaml"
    )


@then(parsers.parse('the loaded language should be "{language}"'))
def then_language_matches(loader_context: LoaderContext, language: str) -> None:
    assert loader_context.result is not None, "Configuration result is required"
    assert loader_context.result.config.language == language


@then(parsers.parse('a configuration error should be reported for "{filename}"'))
def then_configuration_error(loader_context: LoaderContext, filename: str) -> None:
    assert (
        loader_context.error is not None
    ), "Expected configuration error to be captured"
    assert isinstance(loader_context.error, ConfigurationError)
    expected_path = loader_context.root / filename
    assert loader_context.error.details["config_key"] == str(expected_path)
