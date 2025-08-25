import importlib
import sys

import pytest


@pytest.mark.fast
def test_import_devsynth_does_not_import_heavy_optionals(monkeypatch):
    # Ensure a clean slate
    for name in list(sys.modules):
        if name in ("streamlit", "dearpygui", "torch", "transformers", "lmstudio"):
            sys.modules.pop(name, None)

    import devsynth  # noqa: F401

    # Heavy optional deps should not be imported transitively
    for name in ("streamlit", "dearpygui", "torch", "transformers", "lmstudio"):
        assert name not in sys.modules, f"{name} imported at package import time"


@pytest.mark.fast
def test_cli_entrypoint_lazy_imports(monkeypatch):
    for name in list(sys.modules):
        if name in ("streamlit", "dearpygui", "torch", "transformers", "lmstudio"):
            sys.modules.pop(name, None)

    importlib.import_module("devsynth.__main__")

    for name in ("streamlit", "dearpygui", "torch", "transformers", "lmstudio"):
        assert name not in sys.modules, f"{name} imported at CLI entry import time"
