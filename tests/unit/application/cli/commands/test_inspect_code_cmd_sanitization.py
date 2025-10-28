import builtins
from types import SimpleNamespace
from typing import Any, Dict

import pytest

from devsynth.application.cli.commands.inspect_code_cmd import inspect_code_cmd


class _FakeConsole:
    def __init__(self) -> None:
        self.outputs: list[str] = []

    def print(self, msg: Any, *args: Any, **kwargs: Any) -> None:  # minimal capture
        self.outputs.append(str(msg))

    def status(self, _msg: str):  # context manager mock
        class _Ctx:
            def __enter__(self, *a, **k):
                return self

            def __exit__(self, *a, **k):
                return False

        return _Ctx()


import importlib


@pytest.fixture(autouse=True)
def patch_console(monkeypatch):
    # Patch Console used inside the command to our fake console
    fake = _FakeConsole()
    mod = importlib.import_module("devsynth.application.cli.commands.inspect_code_cmd")
    monkeypatch.setattr(mod, "Console", lambda: fake)
    return fake


@pytest.fixture
def fake_analyzers(monkeypatch):
    # Provide analyzers that return unsafe content containing angle brackets
    unsafe = "<script>alert('x')</script>"

    class _SelfAnalyzer:
        def __init__(self, path: str) -> None:
            self.path = path

        def analyze(self) -> dict[str, Any]:
            return {
                "insights": {
                    "architecture": {
                        "type": unsafe,
                        "confidence": 0.42,
                        "layers": {unsafe: [unsafe, "core"]},
                        "architecture_violations": [
                            {
                                "source_layer": unsafe,
                                "target_layer": "domain",
                                "description": unsafe,
                            }
                        ],
                    },
                    "code_quality": {
                        "total_files": 1,
                        "total_classes": 1,
                        "total_functions": 1,
                        "docstring_coverage": {
                            "files": 0.1,
                            "classes": 0.2,
                            "functions": 0.3,
                        },
                    },
                    "test_coverage": {
                        "total_symbols": 2,
                        "tested_symbols": 1,
                        "coverage_percentage": 0.5,
                    },
                    "improvement_opportunities": [],
                }
            }

    class _ProjectAnalyzer:
        def __init__(self, path: str) -> None:
            self.path = path

        def analyze(self) -> dict[str, Any]:
            return {
                "health_score": 7.2,
                "recommendations": [unsafe],
            }

    mod = importlib.import_module("devsynth.application.cli.commands.inspect_code_cmd")
    monkeypatch.setattr(mod, "SelfAnalyzer", _SelfAnalyzer)
    monkeypatch.setattr(mod, "ProjectStateAnalyzer", _ProjectAnalyzer)


@pytest.mark.fast
def test_inspect_code_cmd_sanitizes_dynamic_output(
    patch_console, fake_analyzers, monkeypatch, tmp_path
):
    # Ensure sanitization is enabled by default
    monkeypatch.delenv("DEVSYNTH_SANITIZATION_ENABLED", raising=False)

    # Run command with a path that includes unsafe chars
    unsafe_path = tmp_path / "<unsafe>"
    inspect_code_cmd(path=str(unsafe_path))

    output = "\n".join(patch_console.outputs)

    # Unsafe tokens must not appear raw in output; they should be escaped or removed.
    assert "<script>" not in output
    # Path component with angle brackets should be escaped
    assert "&lt;unsafe&gt;" in output
    assert "<unsafe>" not in output
