"""Programmatic API mirroring the CLI workflows."""
from __future__ import annotations

from typing import Optional

from devsynth.interface.ux_bridge import UXBridge


class AgentAPI:
    """Expose workflow functions for other integrations."""

    def __init__(self, bridge: UXBridge) -> None:
        self.bridge = bridge

    def init(
        self,
        path: str = ".",
        *,
        project_root: Optional[str] = None,
        language: Optional[str] = None,
        goals: Optional[str] = None,
    ) -> None:
        from devsynth.application.cli import init_cmd

        init_cmd(
            path=path,
            project_root=project_root,
            language=language,
            goals=goals,
            bridge=self.bridge,
        )

    def spec(self, requirements_file: str = "requirements.md") -> None:
        from devsynth.application.cli import spec_cmd

        spec_cmd(requirements_file=requirements_file, bridge=self.bridge)

    def inspect(self, input_file: str = "requirements.md") -> None:
        from devsynth.application.cli import inspect_cmd

        inspect_cmd(input_file=input_file, interactive=False, bridge=self.bridge)

    def test(self, spec_file: str = "specs.md") -> None:
        from devsynth.application.cli import test_cmd

        test_cmd(spec_file=spec_file, bridge=self.bridge)

    def code(self) -> None:
        from devsynth.application.cli import code_cmd

        code_cmd(bridge=self.bridge)

    def run_pipeline(self, target: Optional[str] = None) -> None:
        from devsynth.application.cli import run_pipeline_cmd

        run_pipeline_cmd(target=target, bridge=self.bridge)

    def config(self, key: Optional[str] = None, value: Optional[str] = None) -> None:
        from devsynth.application.cli import config_cmd

        config_cmd(key=key, value=value, bridge=self.bridge)


__all__ = ["AgentAPI"]
