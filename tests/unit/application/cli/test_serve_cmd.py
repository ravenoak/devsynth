import builtins
import importlib.util
import sys
from types import ModuleType
from pathlib import Path
from unittest.mock import MagicMock
import pytest
mock_httpx_aiohttp = MagicMock()
mock_httpx_aiohttp.HttpxAiohttpClient = object
sys.modules['httpx_aiohttp'] = mock_httpx_aiohttp
MODULE_ATTRS = {'langgraph.checkpoint.base': {'BaseCheckpointSaver': object, 'empty_checkpoint': None}, 'langgraph.graph': {'END': object(), 'StateGraph': object}, 'openai': {'OpenAI': object, 'AsyncOpenAI': object}, 'tinydb': {'TinyDB': object, 'Query': object}, 'tinydb.storages': {'JSONStorage': object}, 'tiktoken': {}, 'numpy': {'array': lambda x: x}, 'duckdb': {}, 'devsynth.application.orchestration.refactor_workflow': {'refactor_workflow_manager': object}, 'httpx_aiohttp': {'HttpxAiohttpClient': object}}

@pytest.mark.medium
def test_serve_cmd_missing_uvicorn_succeeds(monkeypatch, tmp_path):
    """Test that serve cmd missing uvicorn succeeds.

ReqID: N/A"""
    path = tmp_path / 'cli_commands.py'
    src_path = Path(__file__).parents[4] / 'src' / 'devsynth' / 'application' / 'cli' / 'cli_commands.py'
    content = src_path.read_text()
    content = content.replace('from ..orchestration.refactor_workflow import refactor_workflow_manager', '# Mock for refactor_workflow_manager\nrefactor_workflow_manager = object()')
    content = content.replace('from .commands.edrr_cycle_cmd import edrr_cycle_cmd', '# Mock for edrr_cycle_cmd\nedrr_cycle_cmd = object()')
    content = content.replace('from .commands.doctor_cmd import doctor_cmd', '# Mock for doctor_cmd\ndoctor_cmd = object()')
    path.write_text(content)
    outputs = []
    sys.modules.pop('uvicorn', None)
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split('.')[0] == 'uvicorn':
            raise ImportError("No module named 'uvicorn'")
        try:
            return real_import(name, globals, locals, fromlist, level)
        except ModuleNotFoundError:
            mod = ModuleType(name)
            for attr, val in MODULE_ATTRS.get(name, {}).items():
                setattr(mod, attr, val)
            sys.modules[name] = mod
            return mod
    monkeypatch.setattr(builtins, '__import__', fake_import)
    spec = importlib.util.spec_from_file_location('cli_commands', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.bridge, 'display_result', lambda msg, *, highlight=False: outputs.append(msg))
    module.serve_cmd(bridge=module.bridge)
    assert any(('uvicorn' in msg.lower() for msg in outputs))