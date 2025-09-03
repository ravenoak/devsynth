"""Tests to ensure the `devsynth doctor` path does not import heavy UI modules.

ReqID: FR-DOCTOR-UI-GUARD

These tests guard against regressions where optional UI dependencies (Streamlit,
NiceGUI) are imported at CLI startup or during doctor command execution.
They simulate missing UI packages and assert that doctor_cmd runs without
attempting to import them.
"""

from __future__ import annotations

import sys
from typing import Any

import pytest

from devsynth.application.cli.commands.doctor_cmd import doctor_cmd


@pytest.mark.fast
def test_doctor_cmd_does_not_import_streamlit_or_nicegui(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """doctor_cmd should not import Streamlit/NiceGUI when run with defaults.

    We monkeypatch importlib.import_module to raise ImportError if any code
    attempts to import "streamlit" or "nicegui" directly. The doctor command
    should complete without triggering those imports.
    """

    import importlib

    original_import_module = importlib.import_module

    def guarded_import_module(name: str, package: Any | None = None):  # type: ignore[override]
        if name in {"streamlit", "nicegui"}:
            raise ImportError(f"Guarded import attempted: {name}")
        return original_import_module(name, package)  # type: ignore[arg-type]

    monkeypatch.setattr(importlib, "import_module", guarded_import_module)

    # Ensure these modules are not already loaded in this test process
    for m in [
        "streamlit",
        "nicegui",
        "devsynth.interface.webui",
        "devsynth.interface.nicegui_webui",
    ]:
        sys.modules.pop(m, None)

    # Execute the doctor command; it should not raise and should not import UI modules
    doctor_cmd(config_dir="config", quick=False)

    assert "streamlit" not in sys.modules
    assert "nicegui" not in sys.modules
    assert "devsynth.interface.webui" not in sys.modules
    assert "devsynth.interface.nicegui_webui" not in sys.modules
