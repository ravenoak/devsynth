"""Persona-aware coordination helpers for WSDE teams."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping, Sequence

from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.domain.models.wsde_roles import get_research_persona, iter_research_personas
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass(slots=True)
class ResearchPersonaCoordinator:
    """Mixin providing research persona configuration and telemetry."""

    research_personas_enabled: bool = False
    research_persona_preferences: list[str] = field(default_factory=list)
    research_persona_telemetry: list[dict[str, Any]] = field(default_factory=list)

    def configure_personas(
        self, enabled: bool, personas: Sequence[str] | None = None
    ) -> list[str]:
        """Toggle persona-aware behaviours and record the requested set."""

        self.research_personas_enabled = enabled
        self.research_persona_preferences.clear()
        if not enabled:
            self._record_persona_event("personas_disabled", {})
            return []

        selected = personas or [definition.identifier for definition in iter_research_personas()]
        for candidate in selected:
            try:
                definition = get_research_persona(candidate)
            except KeyError:
                logger.debug("Ignoring unknown persona toggle: %s", candidate)
                continue
            self.research_persona_preferences.append(definition.identifier)
        payload = {"personas": list(self.research_persona_preferences)}
        self._record_persona_event("personas_enabled", payload)
        return list(self.research_persona_preferences)

    # ------------------------------------------------------------------
    # Integration helpers used by WSDETeamCoordinator
    # ------------------------------------------------------------------

    def _configure_team_personas(self, team: WSDETeam) -> None:
        if not self.research_personas_enabled:
            return
        if hasattr(team, "enable_research_personas"):
            team.enable_research_personas(self.research_persona_preferences)

    def _apply_persona_strategy(
        self, team: WSDETeam, task: MutableMapping[str, Any]
    ) -> None:
        if not self.research_personas_enabled:
            return
        if not hasattr(team, "_apply_research_persona_selection"):
            return
        selection = team._apply_research_persona_selection(task)
        if selection is not None:
            self._record_persona_event(
                "persona_selected",
                {
                    "team": getattr(team, "name", "team"),
                    "persona": getattr(selection, "active_persona", None),
                    "agent": getattr(selection, "name", "agent"),
                    "task_id": str(task.get("id", "unknown")),
                },
            )
        else:
            self._record_persona_event(
                "persona_selection_fallback",
                {
                    "team": getattr(team, "name", "team"),
                    "task_id": str(task.get("id", "unknown")),
                    "personas": list(self.research_persona_preferences),
                },
            )

    def _record_persona_event(self, event: str, payload: Mapping[str, Any]) -> None:
        self.research_persona_telemetry.append(
            {
                "event": event,
                "payload": dict(payload),
            }
        )


__all__ = ["ResearchPersonaCoordinator"]
