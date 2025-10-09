"""Shared fixtures and stubs for tests under :mod:`tests.unit.testing`."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Callable, Iterable, Sequence

import pytest

CoverageHook = Callable[[Path], None]

_CONFIG_MODULE = ModuleType("devsynth.config")
_SETTINGS_MODULE = ModuleType("devsynth.config.settings")


def _ensure_path_exists(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


_SETTINGS_MODULE.ensure_path_exists = _ensure_path_exists  # type: ignore[attr-defined]
_CONFIG_MODULE.settings = _SETTINGS_MODULE  # type: ignore[attr-defined]
sys.modules.setdefault("devsynth.config", _CONFIG_MODULE)
sys.modules.setdefault("devsynth.config.settings", _SETTINGS_MODULE)


@pytest.fixture(autouse=True)
def stub_devsynth_config(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Reinstall the lightweight ``devsynth.config`` stub for each test."""

    monkeypatch.setitem(sys.modules, "devsynth.config", _CONFIG_MODULE)
    monkeypatch.setitem(sys.modules, "devsynth.config.settings", _SETTINGS_MODULE)
    return _CONFIG_MODULE


@pytest.fixture
def coverage_stub_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., SimpleNamespace]:
    """Provide a factory that installs a fake ``coverage.Coverage`` implementation."""

    def factory(
        *,
        measured_files: Sequence[str] | None,
        on_html: CoverageHook | None = None,
        on_json: CoverageHook | None = None,
        on_load: Callable[["FakeCoverage"], None] | None = None,
    ) -> SimpleNamespace:
        html_calls: list[Path] = []
        json_calls: list[Path] = []
        instances: list["FakeCoverage"] = []

        class FakeCoverage:
            """Test double mimicking the ``coverage.Coverage`` API surface."""

            def __init__(self, data_file: str) -> None:
                self.data_file = data_file
                instances.append(self)

            def load(self) -> None:
                if on_load is not None:
                    on_load(self)

            def get_data(self) -> SimpleNamespace:
                files: Iterable[str] = [] if measured_files is None else measured_files
                return SimpleNamespace(measured_files=lambda: list(files))

            def html_report(self, directory: str) -> None:
                path = Path(directory)
                html_calls.append(path)
                if on_html is not None:
                    on_html(path)

            def json_report(self, outfile: str) -> None:
                path = Path(outfile)
                json_calls.append(path)
                if on_json is not None:
                    on_json(path)

        module = ModuleType("coverage")
        module.Coverage = FakeCoverage  # type: ignore[attr-defined]
        module.FakeCoverage = FakeCoverage  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "coverage", module)

        return SimpleNamespace(
            html_calls=html_calls,
            json_calls=json_calls,
            instances=instances,
            module=module,
        )

    return factory
