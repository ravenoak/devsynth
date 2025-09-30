"""Regression tests for the strictly typed WSDE team coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from devsynth.agents.wsde_team_coordinator import (
    RetrospectiveNote,
    RetrospectiveSummary,
    WSDETeamCoordinatorAgent,
)


@dataclass
class _StubMemoryManager:
    """Minimal memory manager exposing the hooks exercised by the coordinator."""

    flushed: bool = False

    def __post_init__(self) -> None:
        self.sync_manager = _StubSyncManager()

    def flush_updates(self) -> None:
        self.flushed = True


@dataclass
class _StubSyncManager:
    """Sync manager stub providing queue metadata for ``flush_memory_queue``."""

    _queue: list[tuple[str, object]] = field(default_factory=list)
    _queue_lock: object | None = None


@dataclass
class _RecordingTeam:
    """Team stub that records summaries and exposes a memory manager."""

    records: list[RetrospectiveSummary] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.memory_manager = _StubMemoryManager()

    def record_retrospective(self, summary: RetrospectiveSummary) -> None:
        self.records.append(summary)


@dataclass
class _PrimusAgent:
    name: str
    has_been_primus: bool = False


@dataclass
class _PrimusAwareTeam(_RecordingTeam):
    """Team stub that rotates primus responsibility on each retrospective."""

    agents: list[_PrimusAgent] = field(
        default_factory=lambda: [
            _PrimusAgent("alpha"),
            _PrimusAgent("beta"),
            _PrimusAgent("gamma"),
        ]
    )
    primus_index: int = 0
    primus_history: list[str] = field(default_factory=list)

    def record_retrospective(self, summary: RetrospectiveSummary) -> None:
        super().record_retrospective(summary)
        current = self.agents[self.primus_index]
        current.has_been_primus = True
        self.primus_history.append(current.name)
        self.primus_index = (self.primus_index + 1) % len(self.agents)
        if all(agent.has_been_primus for agent in self.agents):
            for agent in self.agents:
                agent.has_been_primus = False


@pytest.mark.fast
def test_run_retrospective_records_summary_and_flushes_memory() -> None:
    """Coordinator aggregates typed notes and flushes memory updates."""

    notes: list[RetrospectiveNote] = [
        {"positives": ["great"], "improvements": ["better"], "action_items": ["act"]},
        {"positives": ["stellar"], "action_items": ["follow-up"]},
    ]
    team = _RecordingTeam()
    agent = WSDETeamCoordinatorAgent(team)

    summary = agent.run_retrospective(notes, sprint=42)

    assert summary["positives"] == ["great", "stellar"]
    assert summary["improvements"] == ["better"]
    assert summary["action_items"] == ["act", "follow-up"]
    assert summary["sprint"] == 42
    assert team.records == [summary]
    assert team.memory_manager.flushed is True


@pytest.mark.fast
def test_run_retrospective_supports_primus_rotation_cycle() -> None:
    """Retrospective summaries keep custom primus rotation logic intact."""

    note: RetrospectiveNote = {
        "positives": ["cohesive"],
        "improvements": ["pair more"],
        "action_items": ["retro follow-up"],
    }
    team = _PrimusAwareTeam()
    agent = WSDETeamCoordinatorAgent(team)

    for sprint in range(3):
        agent.run_retrospective([note], sprint=sprint)

    assert team.primus_history == ["alpha", "beta", "gamma"]

    # Next cycle resets flags via the rotation logic.
    agent.run_retrospective([note], sprint=3)
    assert team.primus_history[-2:] == ["gamma", "alpha"]
    assert [agent.has_been_primus for agent in team.agents] == [True, False, False]
