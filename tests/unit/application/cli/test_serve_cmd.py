import builtins
import importlib.util
import sys
from types import ModuleType
from pathlib import Path

MODULE_ATTRS = {
    "langgraph.checkpoint.base": {"BaseCheckpointSaver": object, "empty_checkpoint": None},
    "langgraph.graph": {"END": object(), "StateGraph": object},
    "openai": {"OpenAI": object, "AsyncOpenAI": object},
    "tinydb": {"TinyDB": object, "Query": object},
    "tinydb.storages": {"JSONStorage": object},
    "tiktoken": {},
    "numpy": {"array": lambda x: x},
    "duckdb": {},
}


def test_serve_cmd_missing_uvicorn(monkeypatch, tmp_path):
    path = tmp_path / "cli_commands.py"
    src_path = Path(__file__).parents[4] / "src" / "devsynth" / "application" / "cli" / "cli_commands.py"
    path.write_text(src_path.read_text())

    outputs = []

    sys.modules.pop("uvicorn", None)
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".")[0] == "uvicorn":
            raise ImportError("No module named 'uvicorn'")
        try:
            return real_import(name, globals, locals, fromlist, level)
        except ModuleNotFoundError:
            mod = ModuleType(name)
            for attr, val in MODULE_ATTRS.get(name, {}).items():
                setattr(mod, attr, val)
            sys.modules[name] = mod
            return mod

    monkeypatch.setattr(builtins, "__import__", fake_import)

    spec = importlib.util.spec_from_file_location("cli_commands", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore

    monkeypatch.setattr(module.bridge, "display_result", lambda msg, *, highlight=False: outputs.append(msg))

    module.serve_cmd(bridge=module.bridge)

    assert any("uvicorn" in msg.lower() for msg in outputs)
