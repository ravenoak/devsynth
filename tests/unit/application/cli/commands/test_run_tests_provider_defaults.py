"""Tests for ProviderEnv defaults applied by run-tests CLI.

ReqID: FR-22 (CLI behavior) | PlanRef: docs/tasks.md #7
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from devsynth.application.cli.commands import run_tests_cmd as module


class _DummyBridge:
    def print(self, *args, **kwargs):  # pragma: no cover - trivial
        pass


@pytest.mark.fast
def test_run_tests_cmd_applies_stub_offline_defaults_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Ensure variables are unset
    for key in [
        "DEVSYNTH_PROVIDER",
        "DEVSYNTH_OFFLINE",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
    ]:
        monkeypatch.delenv(key, raising=False)

    with patch.object(module, "run_tests", return_value=(True, "")):
        module.run_tests_cmd(
            target="unit-tests", speeds=["fast"], bridge=_DummyBridge()
        )

    assert os.environ.get("DEVSYNTH_PROVIDER") == "stub"
    assert os.environ.get("DEVSYNTH_OFFLINE") == "true"
    # availability default should be false
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "false"
