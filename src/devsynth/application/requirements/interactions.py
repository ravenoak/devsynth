"""Step-wise requirements gathering workflow using :class:`UXBridge`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from collections.abc import Sequence

import yaml

from devsynth.config import get_project_config, save_config
from devsynth.interface.ux_bridge import UXBridge


class RequirementsCollector:
    """Collect basic project requirements interactively."""

    def __init__(
        self, bridge: UXBridge, *, output_file: str = "interactive_requirements.json"
    ) -> None:
        self.bridge = bridge
        self.output_file = output_file

    def gather(self) -> None:
        """Ask questions via the bridge and persist the answers."""
        try:
            name = self.bridge.ask_question("Project name?")
            language = self.bridge.ask_question("Primary language?")
            features = self.bridge.ask_question("Desired features (comma separated)?")

            if not self.bridge.confirm_choice("Save these settings?"):
                self.bridge.display_result("Cancelled")
                return

            data = {
                "name": name,
                "language": language,
                "features": (
                    [f.strip() for f in features.split(";") if f.strip()]
                    if ";" in features
                    else [f.strip() for f in features.split(",") if f.strip()]
                ),
            }

            path = Path(self.output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                if path.suffix in {".yml", ".yaml"}:
                    yaml.safe_dump(data, f, sort_keys=False)
                else:
                    json.dump(data, f, indent=2)

            self.bridge.display_result("Requirements saved")
        except Exception as err:  # pragma: no cover - defensive
            self.bridge.display_result(f"[red]Error:[/red] {err}")


def gather_requirements(
    bridge: UXBridge,
    *,
    output_file: str = "requirements_plan.yaml",
) -> None:
    """Interactively gather project goals, constraints and priority.

    Parameters
    ----------
    bridge:
        Interface bridge used to ask questions and display results.
    output_file:
        Path where the gathered plan should be written. Extension determines
        whether YAML or JSON is used.
    """

    steps: Sequence[tuple[str, str, Sequence[str] | None, str]] = [
        ("goals", "Project goals (comma separated)", None, ""),
        ("constraints", "Project constraints (comma separated)", None, ""),
        (
            "priority",
            "Overall priority",
            ["low", "medium", "high"],
            "medium",
        ),
    ]

    responses: dict[str, str] = {}
    index = 0
    while index < len(steps):
        key, message, choices, default = steps[index]
        prefix = f"Step {index + 1}/{len(steps)}: "
        reply = bridge.ask_question(
            prefix + message + " (type 'back' to go back)",
            choices=choices,
            default=default,
        )
        if reply.lower() == "back":
            if index > 0:
                index -= 1
            else:
                bridge.display_result("[yellow]Already at first step.[/yellow]")
            continue
        responses[key] = reply
        index += 1

    data = {
        "goals": [g.strip() for g in responses["goals"].split(",") if g.strip()],
        "constraints": [
            c.strip() for c in responses["constraints"].split(",") if c.strip()
        ],
        "priority": responses["priority"],
    }

    path = Path(output_file)
    with open(path, "w", encoding="utf-8") as f:
        if path.suffix == ".json":
            json.dump(data, f, indent=2)
        else:
            yaml.safe_dump(data, f, sort_keys=False)

    cfg = get_project_config(Path("."))
    cfg.goals = responses["goals"]
    cfg.constraints = responses["constraints"]
    if hasattr(cfg, "priority"):
        setattr(cfg, "priority", responses["priority"])
    # Always write to .devsynth/project.yaml so gathered data is centralized.
    save_config(cfg, use_pyproject=False)

    bridge.display_result(f"[green]Requirements saved to {output_file}[/green]")


__all__ = ["RequirementsCollector", "gather_requirements"]
