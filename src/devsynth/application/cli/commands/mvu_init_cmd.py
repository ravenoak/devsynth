"""CLI command to scaffold MVU configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()

_DEFAULT_CONFIG = {
    "schema": "docs/specifications/mvuuschema.json",
    "storage": {
        "path": "docs/specifications/mvuu_database.json",
        "format": "json",
    },
    "issues": {
        "github": {
            "base_url": "https://api.github.com/repos/ORG/REPO",
            "token": "YOUR_GITHUB_TOKEN",
        },
        "jira": {
            "base_url": "https://jira.example.com",
            "token": "YOUR_JIRA_TOKEN",
        },
    },
}


def mvu_init_cmd(*, bridge: UXBridge | None = None) -> None:
    """Create a default `.devsynth/mvu.yml` configuration file."""
    bridge = bridge or CLIUXBridge()
    cfg_path = Path(".devsynth") / "mvu.yml"
    if cfg_path.exists():
        bridge.print("[green]MVU configuration already exists.[/green]")
        return

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(_DEFAULT_CONFIG, f, sort_keys=False)

    bridge.print(f"[green]Created {cfg_path}[/green]")


if __name__ == "__main__":  # pragma: no cover - convenience for manual run
    mvu_init_cmd()
