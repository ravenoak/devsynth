import pytest
import yaml

from devsynth.adapters.jira_adapter import JiraAdapter

pytestmark = [pytest.mark.medium]


def test_jira_adapter_config_loading(tmp_path) -> None:
    """Ensure the Jira adapter reads configuration values."""
    cfg = tmp_path / "jira.yml"
    cfg.write_text(
        "jira:\n"
        "  url: https://example.atlassian.net\n"
        "  email: user@example.com\n"
        "  token: token\n"
        "  project_key: TEST\n"
    )
    data = yaml.safe_load(cfg.read_text())["jira"]

    adapter = JiraAdapter(
        url=data["url"],
        email=data["email"],
        token=data["token"],
        project_key=data["project_key"],
    )

    assert adapter.project_key == "TEST"
