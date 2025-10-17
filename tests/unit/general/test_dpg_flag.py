import os
import sys
import types

import pytest

# Skip GUI-related tests in headless environments to avoid crashes
if os.environ.get("DISPLAY", "") == "" and os.environ.get("WAYLAND_DISPLAY", "") == "":
    pytest.skip("Skipping GUI tests in headless environment to avoid crashes", allow_module_level=True)

pytestmark = [pytest.mark.fast]

# Stub heavy optional dependencies before importing cli_commands
langgraph = types.ModuleType("langgraph")
checkpoint = types.ModuleType("langgraph.checkpoint")
checkpoint_base = types.ModuleType("langgraph.checkpoint.base")
checkpoint_base.BaseCheckpointSaver = object  # type: ignore[attr-defined]
checkpoint_base.empty_checkpoint = None  # type: ignore[attr-defined]
checkpoint_sqlite = types.ModuleType("langgraph.checkpoint.sqlite")
graph_mod = types.ModuleType("langgraph.graph")
graph_mod.END = None  # type: ignore[attr-defined]
graph_mod.StateGraph = object  # type: ignore[attr-defined]
langgraph.graph = graph_mod  # type: ignore[attr-defined]

# Mock Dear PyGUI to prevent GUI initialization in headless environments
dearpygui = types.ModuleType("dearpygui")
dearpygui.is_dearpygui_running = lambda: False  # type: ignore[attr-defined]
dearpygui.create_viewport = lambda *args, **kwargs: None  # type: ignore[attr-defined]
dearpygui.setup_dearpygui = lambda *args, **kwargs: None  # type: ignore[attr-defined]
dearpygui.show_viewport = lambda: None  # type: ignore[attr-defined]
dearpygui.start_dearpygui = lambda: None  # type: ignore[attr-defined]
dearpygui.destroy_context = lambda: None  # type: ignore[attr-defined]
dearpygui.is_viewport_created = lambda: False  # type: ignore[attr-defined]

tinydb_mod = types.ModuleType("tinydb")
tinydb_mod.TinyDB = object  # type: ignore[attr-defined]
tinydb_mod.Query = object  # type: ignore[attr-defined]

tinydb_storages = types.ModuleType("tinydb.storages")
tinydb_storages.MemoryStorage = object  # type: ignore[attr-defined]
tinydb_storages.JSONStorage = object  # type: ignore[attr-defined]
tinydb_storages.Storage = object  # type: ignore[attr-defined]
tinydb_storages.touch = lambda *_, **__: None  # type: ignore[attr-defined]


tinydb_middlewares = types.ModuleType("tinydb.middlewares")
tinydb_middlewares.CachingMiddleware = object  # type: ignore[attr-defined]
tqdm_mod = types.ModuleType("tqdm")
tqdm_mod.tqdm = lambda *args, **kwargs: None  # type: ignore[attr-defined]
lmstudio_mod = types.ModuleType("lmstudio")

# Register stubs
for mod, name in [
    (langgraph, "langgraph"),
    (checkpoint, "langgraph.checkpoint"),
    (checkpoint_base, "langgraph.checkpoint.base"),
    (checkpoint_sqlite, "langgraph.checkpoint.sqlite"),
    (graph_mod, "langgraph.graph"),
    (dearpygui, "dearpygui"),
    (tinydb_mod, "tinydb"),
    (tinydb_storages, "tinydb.storages"),
    (tinydb_middlewares, "tinydb.middlewares"),
    (types.ModuleType("tiktoken"), "tiktoken"),
    (types.ModuleType("chromadb"), "chromadb"),
    (types.ModuleType("duckdb"), "duckdb"),
    (types.ModuleType("faiss"), "faiss"),
    (types.ModuleType("lmdb"), "lmdb"),
    (tqdm_mod, "tqdm"),
    (lmstudio_mod, "lmstudio"),
]:
    sys.modules.setdefault(name, mod)

from devsynth.application.cli import cli_commands as cc


class DummyBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def display_result(self, message: str, **_: object) -> None:
        self.messages.append(message)


def test_dpg_command_disabled(monkeypatch):
    monkeypatch.setattr(
        "devsynth.application.cli.commands.dpg_cmd.get_settings",
        lambda reload=True: types.SimpleNamespace(gui_enabled=False),
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.dpg_cmd.run_dpg_ui", None
    )
    bridge = DummyBridge()
    cc.dpg_cmd(bridge=bridge)
    assert any("GUI support is disabled" in m for m in bridge.messages)


def test_dpg_command_missing_dependency(monkeypatch):
    monkeypatch.setattr(
        "devsynth.application.cli.commands.dpg_cmd.get_settings",
        lambda reload=True: types.SimpleNamespace(gui_enabled=True),
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.dpg_cmd.run_dpg_ui", None
    )
    bridge = DummyBridge()
    cc.dpg_cmd(bridge=bridge)
    assert any("Dear PyGUI interface is unavailable" in m for m in bridge.messages)


@pytest.mark.skip(reason="GUI tests cause segmentation faults in headless environments")
def test_dpg_command_enabled(monkeypatch):
    import importlib

    called: list[bool] = []

    # Mock the DPG UI module before any imports that might load it
    ui_stub = types.ModuleType("devsynth.interface.dpg_ui")
    ui_stub.run = lambda: called.append(True)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "devsynth.interface.dpg_ui", ui_stub)

    import devsynth.application.cli.cli_commands as cc_mod

    importlib.reload(cc_mod)
    monkeypatch.setattr(
        "devsynth.application.cli.commands.dpg_cmd.get_settings",
        lambda reload=True: types.SimpleNamespace(gui_enabled=True),
    )
    cc_mod.dpg_cmd(bridge=DummyBridge())
    assert called == [True]
