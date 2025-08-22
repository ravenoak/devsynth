"""Pytest fixtures for behavior tests."""

import importlib.util
import os
import shutil
import sys
import tempfile
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

try:
    from devsynth.config.settings import ensure_path_exists
except ModuleNotFoundError:

    def ensure_path_exists(path: str) -> str:  # pragma: no cover - fallback
        os.makedirs(path, exist_ok=True)
        return path


# Stub optional heavy dependencies so test collection succeeds without them
_stub_modules = [
    "langgraph",
    "langgraph.checkpoint",
    "langgraph.checkpoint.base",
    "langgraph.graph",
    "langchain",
    "langchain_openai",
    "langchain_community",
    "tiktoken",
    "tinydb",
    "tinydb.storages",
    "tinydb.middlewares",
    "duckdb",
    "lmdb",
    "faiss",
    "httpx",
    "lmstudio",
    "typer",
    "typer.main",
    "typer.models",
    "openai",
    "openai.types",
    "openai.types.chat",
    "torch",
    "transformers",
    "astor",
]

for _name in _stub_modules:
    if _name in sys.modules:
        continue
    if importlib.util.find_spec(_name) is None:
        _mod = ModuleType(_name)
        if _name == "langgraph.checkpoint.base":
            _mod.BaseCheckpointSaver = object
            _mod.empty_checkpoint = object()
        if _name == "langgraph.graph":
            _mod.END = None
            _mod.StateGraph = object
        if _name == "tinydb":
            _mod.TinyDB = object
            _mod.Query = object
        if _name == "tinydb.storages":
            _mod.JSONStorage = object
            _mod.MemoryStorage = object
            _mod.Storage = object
            _mod.touch = lambda *a, **k: None
        if _name == "tinydb.middlewares":
            _mod.CachingMiddleware = object
        if _name == "openai":
            _mod.OpenAI = object
            _mod.AsyncOpenAI = object
        if _name == "openai.types.chat":
            _mod.ChatCompletion = object
            _mod.ChatCompletionChunk = object
        if _name == "transformers":
            _mod.AutoModelForCausalLM = object
            _mod.AutoTokenizer = object
        if _name == "httpx":
            _mod.RequestError = Exception
            _mod.HTTPStatusError = Exception
        if _name == "typer":
            _mod.main = ModuleType("typer.main")
            _mod.main.get_click_type = lambda annotation: annotation
            _mod.models = ModuleType("typer.models")
            _mod.models.Context = object
            sys.modules["typer.main"] = _mod.main
            sys.modules["typer.models"] = _mod.models
        sys.modules[_name] = _mod

# Add the src directory to the Python path if needed
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

import click
import typer
import typer.main

# Import provider system for LLM integration
try:
    from devsynth.adapters.provider_system import (
        ProviderType,
        complete,
        embed,
        get_provider,
    )
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    ProviderType = MagicMock()

    def complete(*args, **kwargs):
        return {}

    def embed(*args, **kwargs):
        return []

    def get_provider(*args, **kwargs):
        return MagicMock()


try:
    from devsynth.interface.ux_bridge import UXBridge
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    UXBridge = MagicMock()


@pytest.fixture
def tmp_project_dir():
    """
    Create a temporary directory for a DevSynth project.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create basic project structure
    devsynth_dir = os.path.join(temp_dir, ".devsynth")
    os.makedirs(devsynth_dir, exist_ok=True)  # Explicitly create the directory

    # Create a mock config file
    config_path = os.path.join(devsynth_dir, "config.json")
    with open(config_path, "w") as f:
        f.write('{"model": "gpt-4", "project_name": "test-project"}')

    # Return the path to the temporary directory
    yield temp_dir

    # Clean up the temporary directory after the test
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def patch_env_and_cleanup(tmp_project_dir):
    """
    Patch environment variables for LLM providers and ensure all logs/artifacts are isolated and cleaned up.
    Also mock LLM provider functions to prevent real API calls.
    """
    # Patch environment variables for OpenAI and LM Studio
    old_env = dict(os.environ)
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["LM_STUDIO_ENDPOINT"] = "http://127.0.0.1:1234"
    os.environ["DEVSYNTH_PROJECT_DIR"] = tmp_project_dir
    # Redirect logs to temp dir
    logs_dir = os.path.join(tmp_project_dir, "logs")
    ensure_path_exists(logs_dir)
    old_cwd = os.getcwd()
    os.chdir(tmp_project_dir)

    # Mock the provider system functions to prevent real API calls
    mock_provider = MagicMock()
    mock_provider.complete.return_value = (
        "This is a mock completion response for testing purposes."
    )
    mock_provider.embed.return_value = [
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
    ]  # Mock embedding vector
    mock_provider.provider_type = ProviderType.OPENAI

    # Define mock functions
    def mock_complete(
        prompt, system_prompt=None, temperature=0.7, max_tokens=2000, fallback=False
    ):
        if "error" in str(prompt).lower():
            return "Error scenario response"
        elif "empty" in str(prompt).lower():
            return ""
        else:
            return f"Mock response for: {str(prompt)[:30]}..."

    def mock_embed(text, fallback=False):
        return [0.1, 0.2, 0.3, 0.4, 0.5]  # Mock embedding vector

    # Apply patches
    with patch(
        "devsynth.adapters.provider_system.get_provider", return_value=mock_provider
    ):
        with patch(
            "devsynth.adapters.provider_system.complete", side_effect=mock_complete
        ):
            with patch(
                "devsynth.adapters.provider_system.embed", side_effect=mock_embed
            ):
                yield

    # Cleanup: restore env and cwd, remove logs if present
    os.environ.clear()
    os.environ.update(old_env)
    os.chdir(old_cwd)
    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)
    # Remove any stray .devsynth or logs in cwd
    for artifact in [".devsynth", "logs"]:
        path = os.path.join(old_cwd, artifact)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    """Allow Typer to handle custom parameter types used in the CLI."""
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if (
            origin in {UXBridge, typer.models.Context}
            or annotation is dict
            or origin is dict
        ):
            return click.STRING
        return orig(annotation=annotation, parameter_info=parameter_info)

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)


@pytest.fixture
def llm_provider():
    """
    Mock provider for LLM completion that works with either OpenAI or LM Studio.

    This provides a unified interface for tests to use LLMs, automatically
    selecting the best available provider and handling fallback if needed.
    """
    # Create a mock provider
    mock_provider = MagicMock()
    mock_provider.complete.return_value = (
        "This is a mock completion response for testing purposes."
    )
    mock_provider.embed.return_value = [
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
    ]  # Mock embedding vector
    mock_provider.provider_type = ProviderType.OPENAI

    # Patch the get_provider function to return our mock
    with patch(
        "devsynth.adapters.provider_system.get_provider", return_value=mock_provider
    ):
        yield mock_provider


@pytest.fixture
def llm_complete():
    """
    Fixture providing a mocked function to get completions from the LLM.

    This is a convenience wrapper that returns predefined responses for testing.
    """

    def _complete(prompt, system_prompt=None, temperature=0.7, max_tokens=2000):
        # Return a predictable response based on the prompt for testing
        if "error" in prompt.lower():
            return "Error scenario response"
        elif "empty" in prompt.lower():
            return ""
        else:
            return f"Mock response for: {prompt[:30]}..."

    # Patch the complete function
    with patch("devsynth.adapters.provider_system.complete", side_effect=_complete):
        yield _complete


@pytest.fixture
def mock_workflow_manager():
    """
    Mock the workflow manager to avoid actual execution.
    """
    # Create a mock for the workflow manager
    mock_manager = MagicMock()

    # Configure the mock to return success for execute_command
    mock_manager.execute_command.return_value = {
        "success": True,
        "message": "Operation completed successfully",
        "value": "mock_value",
        "config": {
            "model": "gpt-4",
            "project_name": "test-project",
            "template": "default",
        },
    }

    # Patch the workflow_manager in the commands module
    with patch(
        "devsynth.application.orchestration.workflow.workflow_manager",
        mock_manager,
    ):
        with patch("devsynth.core.workflow_manager", mock_manager):
            yield mock_manager


@pytest.fixture
def project_template_dir():
    """
    Create a temporary directory with project templates.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create default template structure
    default_template_dir = os.path.join(temp_dir, "default")
    ensure_path_exists(default_template_dir)

    # Create a default template config file
    with open(os.path.join(default_template_dir, "config.json"), "w") as f:
        f.write('{"model": "gpt-4", "template": "default"}')

    # Create web-app template structure
    webapp_template_dir = os.path.join(temp_dir, "web-app")
    ensure_path_exists(webapp_template_dir)

    # Create a web-app template config file
    with open(os.path.join(webapp_template_dir, "config.json"), "w") as f:
        f.write('{"model": "gpt-4", "template": "web-app", "framework": "flask"}')

    # Return the path to the temporary directory
    yield temp_dir

    # Clean up the temporary directory after the test
    shutil.rmtree(temp_dir)


@pytest.fixture
def command_context():
    """
    Store context about the command being executed.
    """
    return {"command": "", "output": ""}
