from pathlib import Path

import pytest
import yaml

from devsynth.adapters.github_project import GitHubProjectAdapter

pytestmark = [pytest.mark.medium]


def test_github_project_adapter_config_loading(tmp_path: Path) -> None:
    """Ensure the GitHub adapter reads configuration values."""
    cfg = tmp_path / "github_project.yml"
    cfg.write_text(
        "github_project:\n"
        "  token: token\n"
        "  organization: org\n"
        "  project_number: 1\n"
    )
    data = yaml.safe_load(cfg.read_text())["github_project"]

    adapter = GitHubProjectAdapter(
        token=data["token"],
        organization=data["organization"],
        project_number=data["project_number"],
    )

    assert adapter.organization == "org"
    assert adapter.project_number == 1
