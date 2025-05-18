"""
Pytest fixtures for behavior tests.
"""
import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import provider system for LLM integration
from devsynth.adapters.provider_system import get_provider, complete, embed, ProviderType

@pytest.fixture
def tmp_project_dir():
    """
    Create a temporary directory for a DevSynth project.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Create basic project structure
    os.makedirs(os.path.join(temp_dir, '.devsynth'), exist_ok=True)
    
    # Create a mock config file
    with open(os.path.join(temp_dir, '.devsynth', 'config.json'), 'w') as f:
        f.write('{"model": "gpt-4", "project_name": "test-project"}')
    
    # Return the path to the temporary directory
    yield temp_dir
    
    # Clean up the temporary directory after the test
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def patch_env_and_cleanup(tmp_project_dir):
    """
    Patch environment variables for LLM providers and ensure all logs/artifacts are isolated and cleaned up.
    """
    # Patch environment variables for OpenAI and LM Studio
    old_env = dict(os.environ)
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["LM_STUDIO_ENDPOINT"] = "http://127.0.0.1:1234"
    os.environ["DEVSYNTH_PROJECT_DIR"] = tmp_project_dir
    # Redirect logs to temp dir
    logs_dir = os.path.join(tmp_project_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    old_cwd = os.getcwd()
    os.chdir(tmp_project_dir)
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


@pytest.fixture
def llm_provider():
    """
    Get a provider for LLM completion that works with either OpenAI or LM Studio.

    This provides a unified interface for tests to use LLMs, automatically
    selecting the best available provider and handling fallback if needed.
    """
    # Get a provider with fallback enabled (will try OpenAI then LM Studio)
    provider = get_provider(fallback=True)
    return provider


@pytest.fixture
def llm_complete():
    """
    Fixture providing a function to get completions from the LLM.

    This is a convenience wrapper around the provider system's complete function.
    Tests can use this to generate text without worrying about provider details.
    """
    def _complete(prompt, system_prompt=None, temperature=0.7, max_tokens=2000):
        return complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            fallback=True  # Enable fallback to try all available providers
        )

    return _complete


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
            "template": "default"
        }
    }
    
    # Patch the workflow_manager in the commands module
    with patch('devsynth.application.orchestration.workflow.workflow_manager', mock_manager):
        with patch('devsynth.application.cli.cli_commands.workflow_manager', mock_manager):
            yield mock_manager


@pytest.fixture
def project_template_dir():
    """
    Create a temporary directory with project templates.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Create default template structure
    default_template_dir = os.path.join(temp_dir, 'default')
    os.makedirs(default_template_dir, exist_ok=True)
    
    # Create a default template config file
    with open(os.path.join(default_template_dir, 'config.json'), 'w') as f:
        f.write('{"model": "gpt-4", "template": "default"}')
    
    # Create web-app template structure
    webapp_template_dir = os.path.join(temp_dir, 'web-app')
    os.makedirs(webapp_template_dir, exist_ok=True)
    
    # Create a web-app template config file
    with open(os.path.join(webapp_template_dir, 'config.json'), 'w') as f:
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
