from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.fast
def test_shell_scripts_enforce_non_root_and_env_validation():
    """Deployment shell scripts enforce non-root execution and env file checks."""
    scripts_dir = ROOT / "scripts/deployment"
    for script in scripts_dir.glob("*.sh"):
        content = script.read_text()
        assert "$EUID" in content, f"{script} missing non-root enforcement"
        if "ENV_FILE" in content:
            assert "Missing environment file" in content
            assert "Environment file $ENV_FILE must have 600 permissions" in content


def test_docker_compose_enforces_user_and_env_file():
    """docker-compose defines non-root users and required env files."""
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    services = compose.get("services", {})
    required_env_file_services = {
        "devsynth",
        "dev-tools",
        "test-runner",
        "publish",
        "rollback",
    }
    for name, config in services.items():
        assert "user" in config, f"{name} missing user directive"
    for name in required_env_file_services:
        assert "env_file" in services.get(name, {}), f"{name} missing env_file"
