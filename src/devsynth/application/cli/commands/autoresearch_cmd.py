"""CLI command for enabling Autoresearch personas."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.core.mvu.models import MVUU
from devsynth.domain.models.wsde_roles import iter_research_personas


def _persona_choices() -> list[str]:  # pragma: no cover - trivial helper
    return [persona.identifier for persona in iter_research_personas()]


def autoresearch_cmd(argv: list[str] | None = None) -> int:
    """Configure research personas and emit MVUU telemetry."""

    parser = argparse.ArgumentParser(
        prog="autoresearch",
        description="Configure Autoresearch personas for WSDE collaboration",
    )
    parser.add_argument(
        "--enable-personas",
        action="store_true",
        help="Activate persona-aware primus selection",
    )
    parser.add_argument(
        "--persona",
        action="append",
        choices=_persona_choices(),
        help="Specify one or more personas to activate",
    )
    parser.add_argument(
        "--trace-id",
        help="Optional TraceID to reuse for MVUU emission",
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="Skip MVUU trace emission",
    )
    args = parser.parse_args(argv)

    coordinator = WSDETeamCoordinator()
    personas = list(args.persona or [])
    if args.enable_personas and not personas:
        personas = _persona_choices()
    active_personas = coordinator.configure_personas(args.enable_personas, personas)

    telemetry_snapshot = list(coordinator.research_persona_telemetry)
    if args.enable_personas:
        team = coordinator.create_team("autoresearch_cli")
        coordinator._record_persona_event(
            "cli_team_initialized",
            {
                "team": team.name,
                "personas": active_personas,
            },
        )
        telemetry_snapshot = list(coordinator.research_persona_telemetry)

    payload: dict[str, object] = {
        "personas": active_personas,
        "telemetry": telemetry_snapshot,
    }

    if not args.no_trace:
        trace_id = args.trace_id or f"AR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        mvuu = MVUU(
            utility_statement="Autoresearch persona toggles applied",
            affected_files=[
                "src/devsynth/domain/models/wsde_roles.py",
                "src/devsynth/application/collaboration/wsde_team_extended.py",
                "src/devsynth/adapters/agents/agent_adapter.py",
            ],
            tests=[
                "tests/unit/cli/test_autoresearch_persona_cli.py",
                "tests/unit/general/test_wsde_team_coordinator.py",
            ],
            TraceID=trace_id,
            mvuu=True,
            issue="Autoresearch-agent-specialization",
            notes="Research personas activated via CLI",
        )
        payload["mvuu"] = mvuu.as_dict()

    print(json.dumps(payload))
    return 0


__all__ = ["autoresearch_cmd"]
