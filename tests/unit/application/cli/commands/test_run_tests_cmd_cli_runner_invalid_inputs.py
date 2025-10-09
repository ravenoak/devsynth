from __future__ import annotations

import importlib.util
import json
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import typer
from typer import Typer
from typer.models import OptionInfo
from typer.testing import CliRunner

from devsynth.testing import run_tests as run_tests_module


@pytest.fixture(autouse=True)
def _cli_dependency_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install lightweight stubs for optional CLI dependencies."""

    provider_env_module = ModuleType("devsynth.config.provider_env")

    class _ProviderEnv:
        @classmethod
        def from_env(cls) -> _ProviderEnv:
            return cls()

        def with_test_defaults(self) -> _ProviderEnv:
            return self

        def apply_to_env(self) -> None:
            return None

    provider_env_module.ProviderEnv = _ProviderEnv  # type: ignore[attr-defined]

    config_pkg = ModuleType("devsynth.config")
    config_pkg.provider_env = provider_env_module  # type: ignore[attr-defined]
    config_pkg.get_settings = lambda: {}  # type: ignore[attr-defined]
    config_pkg.get_project_config = lambda *_, **__: {}  # type: ignore[attr-defined]
    config_pkg.save_config = lambda *_, **__: None  # type: ignore[attr-defined]
    config_spec = ModuleSpec("devsynth.config", loader=None, is_package=True)
    config_spec.submodule_search_locations = []
    config_pkg.__spec__ = config_spec  # type: ignore[attr-defined]
    config_pkg.__path__ = []  # type: ignore[attr-defined]

    yaml_module = ModuleType("yaml")
    yaml_module.dump = lambda data, *_, **__: "yaml: true\n"  # type: ignore[arg-type]

    argon2_module = ModuleType("argon2")

    class _PasswordHasher:
        def __init__(self, *_, **__):
            pass

        def hash(self, value: str) -> str:
            return f"hashed::{value}"

        def verify(self, hashed: str, value: str) -> bool:
            return hashed.endswith(value)

    argon2_exceptions = ModuleType("argon2.exceptions")
    argon2_exceptions.VerifyMismatchError = RuntimeError  # type: ignore[attr-defined]

    argon2_module.PasswordHasher = _PasswordHasher  # type: ignore[attr-defined]
    argon2_module.exceptions = argon2_exceptions  # type: ignore[attr-defined]

    cryptography_module = ModuleType("cryptography")
    fernet_module = ModuleType("cryptography.fernet")

    class _Fernet:
        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        @staticmethod
        def generate_key() -> bytes:
            return b"stub-key"

        def encrypt(self, data: bytes) -> bytes:
            return b"encrypted" + data

        def decrypt(self, token: bytes) -> bytes:
            return b"decrypted"

    fernet_module.Fernet = _Fernet  # type: ignore[attr-defined]
    cryptography_module.fernet = fernet_module  # type: ignore[attr-defined]

    tqdm_module = ModuleType("tqdm")
    tqdm_module.tqdm = lambda iterable=None, **__: iterable or []  # type: ignore[attr-defined]

    requests_module = ModuleType("requests")
    requests_module.get = lambda *_, **__: None  # type: ignore[attr-defined]
    requests_module.post = requests_module.get  # type: ignore[attr-defined]
    requests_module.request = requests_module.get  # type: ignore[attr-defined]
    requests_module.Session = object  # type: ignore[attr-defined]

    numpy_module = ModuleType("numpy")
    numpy_module.ndarray = object  # type: ignore[attr-defined]
    numpy_module.array = lambda data, *_, **__: data  # type: ignore[attr-defined]
    numpy_module.mean = lambda data, *_, **__: 0  # type: ignore[attr-defined]

    tiktoken_module = ModuleType("tiktoken")

    class _Encoding:
        def encode(self, text: str) -> list[int]:  # type: ignore[override]
            return []

        def decode(self, tokens: list[int]) -> str:  # type: ignore[override]
            return ""

    tiktoken_module.get_encoding = lambda *_: _Encoding()  # type: ignore[attr-defined]

    rdflib_module = ModuleType("rdflib")

    class _Graph:
        def __init__(self, *_, **__):
            pass

    class _Literal(str):
        pass

    class _URIRef(str):
        pass

    class _Namespace(str):
        def __getattr__(self, item: str) -> str:  # type: ignore[override]
            return f"{self}{item}"

    rdflib_module.RDF = object()  # type: ignore[attr-defined]
    rdflib_module.Graph = _Graph  # type: ignore[attr-defined]
    rdflib_module.Literal = _Literal  # type: ignore[attr-defined]
    rdflib_module.Namespace = _Namespace  # type: ignore[attr-defined]
    rdflib_module.URIRef = _URIRef  # type: ignore[attr-defined]

    namespace_module = ModuleType("rdflib.namespace")
    namespace_module.DC = _Namespace("http://purl.org/dc/elements/1.1/")  # type: ignore[attr-defined]
    namespace_module.FOAF = _Namespace("http://xmlns.com/foaf/0.1/")  # type: ignore[attr-defined]
    namespace_module.Namespace = _Namespace  # type: ignore[attr-defined]

    tinydb_module = ModuleType("tinydb")
    tinydb_module.TinyDB = object  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "devsynth.config", config_pkg)
    monkeypatch.setitem(
        sys.modules, "devsynth.config.provider_env", provider_env_module
    )
    monkeypatch.setitem(sys.modules, "yaml", yaml_module)
    monkeypatch.setitem(sys.modules, "argon2", argon2_module)
    monkeypatch.setitem(sys.modules, "argon2.exceptions", argon2_exceptions)
    monkeypatch.setitem(sys.modules, "cryptography", cryptography_module)
    monkeypatch.setitem(sys.modules, "cryptography.fernet", fernet_module)
    monkeypatch.setitem(sys.modules, "tqdm", tqdm_module)
    monkeypatch.setitem(sys.modules, "requests", requests_module)
    monkeypatch.setitem(sys.modules, "numpy", numpy_module)
    monkeypatch.setitem(sys.modules, "tiktoken", tiktoken_module)
    monkeypatch.setitem(sys.modules, "rdflib", rdflib_module)
    monkeypatch.setitem(sys.modules, "rdflib.namespace", namespace_module)
    monkeypatch.setitem(sys.modules, "tinydb", tinydb_module)
    monkeypatch.setenv("DEVSYNTH_CLI_MINIMAL", "1")


def _ensure_package(monkeypatch: pytest.MonkeyPatch, name: str, path: Path) -> None:
    package = ModuleType(name)
    package.__path__ = [str(path)]  # type: ignore[attr-defined]
    spec = ModuleSpec(name, loader=None, is_package=True)
    spec.submodule_search_locations = [str(path)]
    package.__spec__ = spec  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, name, package)


def _load_run_tests_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    repo_root = Path(__file__).resolve().parents[5]
    module_name = "devsynth.application.cli.commands.run_tests_cmd"
    module_path = repo_root / "src/devsynth/application/cli/commands/run_tests_cmd.py"

    _ensure_package(
        monkeypatch, "devsynth.application", repo_root / "src/devsynth/application"
    )
    _ensure_package(
        monkeypatch,
        "devsynth.application.cli",
        repo_root / "src/devsynth/application/cli",
    )
    _ensure_package(
        monkeypatch,
        "devsynth.application.cli.commands",
        repo_root / "src/devsynth/application/cli/commands",
    )

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load run_tests_cmd module spec")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


def _build_minimal_app(monkeypatch: pytest.MonkeyPatch) -> tuple[Typer, ModuleType]:
    """Register a reduced Typer surface that forwards to the production command."""

    module = _load_run_tests_module(monkeypatch)
    app = Typer()

    @app.command(name="run-tests")
    def run_tests_command(
        target: str = typer.Option("all-tests", "--target", help="Test target to run"),
        speed: list[str] = typer.Option(
            [],
            "--speed",
            help="Speed categories to run (can be used multiple times)",
            show_default=False,
        ),
        inventory: bool = typer.Option(
            False,
            "--inventory",
            help="Export test inventory to test_reports/test_inventory.json and exit",
        ),
        maxfail: int | None = typer.Option(
            None, "--maxfail", help="Exit after this many failures"
        ),
    ) -> None:
        if isinstance(speed, OptionInfo):
            speeds_arg = None
        else:
            speeds_arg = list(speed) if speed else None
        module.run_tests_cmd(
            target=target,
            speeds=speeds_arg,
            report=False,
            verbose=False,
            no_parallel=False,
            smoke=False,
            segment=False,
            segment_size=50,
            inventory=inventory,
            maxfail=maxfail,
            features=None,
            marker=None,
            bridge=None,
        )

    return app, module


@pytest.mark.fast
def test_cli_runner_rejects_invalid_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """Typer surface should emit remediation text when --target is invalid."""

    app, _ = _build_minimal_app(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["--target", "not-a-real-target"],
        prog_name="run-tests",
    )

    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)
    assert result.exception.code == 2
    assert "Invalid --target value" in result.stdout
    assert "docs/user_guides/cli_command_reference.md" in result.stdout


@pytest.mark.fast
def test_cli_runner_rejects_invalid_speed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid --speed flags should exit with actionable remediation guidance."""

    app, _ = _build_minimal_app(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--speed",
            "warp",
        ],
        prog_name="run-tests",
    )

    assert result.exit_code == 2
    assert "Invalid --speed value(s)" in result.stdout
    assert "Allowed: fast|medium|slow" in result.stdout


@pytest.mark.fast
def test_cli_runner_inventory_handles_collection_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Inventory exports tolerate collection errors and still succeed."""

    monkeypatch.chdir(tmp_path)

    calls: list[tuple[str, str | None]] = []

    def fake_collect(target: str, speed: str | None) -> list[str]:
        calls.append((target, speed))
        if target == "integration-tests" and speed == "medium":
            raise RuntimeError("collection failed")
        suffix = speed or "all"
        return [f"{target}::{suffix}::test_case"]

    app, cli_module = _build_minimal_app(monkeypatch)
    monkeypatch.setattr(cli_module, "collect_tests_with_cache", fake_collect)

    runner = CliRunner()
    result = runner.invoke(app, ["--inventory"], prog_name="run-tests")

    assert result.exit_code == 0
    assert "Test inventory exported to" in result.stdout
    assert len(calls) == 12  # 4 targets × 3 speed buckets

    inventory_path = tmp_path / "test_reports" / "test_inventory.json"
    payload = json.loads(inventory_path.read_text())

    assert payload["targets"]["integration-tests"]["medium"] == []
    assert payload["targets"]["unit-tests"]["fast"] == ["unit-tests::fast::test_case"]


@pytest.mark.fast
def test_cli_runner_failed_run_surfaces_maxfail_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failed Typer invocation should surface the maxfail troubleshooting tip."""

    app, cli_module = _build_minimal_app(monkeypatch)

    def fake_run_tests(*args: object, **kwargs: object) -> tuple[bool, str]:
        cmd = ["python", "-m", "pytest", "--maxfail", "2"]
        tips = run_tests_module._failure_tips(1, cmd)
        return False, "segment error\n" + tips

    monkeypatch.setattr(cli_module, "run_tests", fake_run_tests)

    runner = CliRunner()
    result = runner.invoke(app, ["--maxfail", "2"], prog_name="run-tests")

    assert result.exit_code == 1
    assert "Tests failed" in result.stdout
    assert "--maxfail=1" in result.stdout
    assert "Segment large suites" in result.stdout


@pytest.mark.fast
def test_cli_runner_inventory_write_failure_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Disk errors while exporting inventory should exit with code 1."""

    monkeypatch.chdir(tmp_path)

    def fake_collect(target: str, speed: str | None) -> list[str]:
        suffix = speed or "all"
        return [f"{target}::{suffix}::case"]

    app, cli_module = _build_minimal_app(monkeypatch)
    monkeypatch.setattr(cli_module, "collect_tests_with_cache", fake_collect)

    def fail_write(self: Path, *_: object, **__: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fail_write)

    runner = CliRunner()
    result = runner.invoke(app, ["--inventory"], prog_name="run-tests")

    assert result.exit_code == 1
    assert isinstance(result.exception, OSError)
    assert "disk full" in str(result.exception)


@pytest.mark.fast
def test_cli_runner_maxfail_option_propagates_to_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Typer surface must forward --maxfail to run_tests."""

    app, cli_module = _build_minimal_app(monkeypatch)

    received: dict[str, object] = {}

    def fake_run_tests(*args: object, **kwargs: object) -> tuple[bool, str]:
        received["args"] = args
        received["kwargs"] = dict(kwargs)
        return True, "pytest ok"

    monkeypatch.setattr(cli_module, "run_tests", fake_run_tests)
    monkeypatch.setattr(
        cli_module, "_coverage_instrumentation_status", lambda: (True, None)
    )
    monkeypatch.setattr(cli_module, "coverage_artifacts_status", lambda: (True, None))
    monkeypatch.setattr(
        cli_module,
        "enforce_coverage_threshold",
        lambda exit_on_failure=False: 95.0,
    )
    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--maxfail", "3", "--speed", "fast", "--target", "unit-tests"],
        prog_name="run-tests",
    )

    assert result.exit_code == 0
    assert received["kwargs"]["maxfail"] == 3
    assert received["kwargs"]["segment"] is False
