"""Voting and consensus strategies for WSDE teams."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from random import Random
from typing import Dict, Iterable, Mapping, Optional, Sequence
from uuid import uuid4

from devsynth.domain.models.wsde_core import WSDETeam
from devsynth.domain.models.wsde_typing import (
    ConsensusResult,
    ConsensusRound,
    ConsensusStatus,
    ConsensusTranscript,
    SupportsTeamAgent,
    TaskDict,
    VoteMethod,
    VoteRecord,
    VoteStatus,
    VotingTranscript,
)
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass(slots=True)
class VotingEngine:
    """Typed façade around WSDE voting behaviour."""

    team: WSDETeam

    def vote(
        self, task: TaskDict, rng: Optional[Random] = None
    ) -> VotingTranscript | Dict[str, object]:
        if not self.team.agents:
            logger.warning("Cannot conduct vote: no agents in team")
            return {"status": "failed", "reason": "no_agents"}
        if "options" not in task or not task["options"]:
            logger.warning("Cannot conduct vote: no options provided")
            return {"status": "failed", "reason": "no_options"}

        rng_instance = rng if rng is not None else Random()
        options = _normalise_options(task["options"])
        raw_method = str(task.get("voting_method", VoteMethod.MAJORITY.value))
        try:
            method = VoteMethod(raw_method)
        except ValueError:
            logger.warning(
                "Unknown voting method '%s', defaulting to majority", raw_method
            )
            method = VoteMethod.MAJORITY
        votes, reasoning = self._collect_votes(options, rng_instance)
        vote_counts = _count_votes(options, votes)
        record = self._apply_method(
            method, task, options, votes, vote_counts, rng_instance
        )

        transcript = VotingTranscript(
            identifier=str(uuid4()),
            timestamp=datetime.now(),
            task_id=str(task.get("id", uuid4())),
            method=method,
            options=tuple(options),
            votes=votes,
            reasoning=reasoning,
            record=record,
        )

        self._record_history(task, transcript)
        return transcript

    def consensus_vote(
        self, task: TaskDict, rng: Optional[Random] = None
    ) -> Dict[str, object]:
        consensus_task: TaskDict = dict(task)
        consensus_task["voting_method"] = VoteMethod.MAJORITY.value
        result = self.vote(consensus_task, rng)
        if isinstance(result, dict):
            return result
        return {
            "status": result.record.status.value,
            "decision": result.record.result,
            "explanation": result.record.explanation,
            "vote_counts": result.record.vote_counts,
        }

    def build_consensus(
        self, task: TaskDict, rng: Optional[Random] = None
    ) -> ConsensusTranscript | Dict[str, object]:
        if not self.team.agents:
            logger.warning("Cannot build consensus: no agents in team")
            return {"status": "failed", "reason": "no_agents"}
        if "options" not in task or not task["options"]:
            logger.warning("Cannot build consensus: no options provided")
            return {"status": "failed", "reason": "no_options"}

        rng_instance = rng if rng is not None else Random()
        options = _normalise_options(task["options"])
        threshold = float(task.get("consensus_threshold", 0.75))
        max_rounds = int(task.get("max_rounds", 3))

        initial_preferences = {
            agent.name: self._initial_preferences(agent, options)
            for agent in self.team.agents
        }
        current_preferences = {
            name: dict(prefs) for name, prefs in initial_preferences.items()
        }

        rounds: list[ConsensusRound] = []
        status = ConsensusStatus.IN_PROGRESS
        consensus_option: str | None = None
        explanation = ""

        for round_number in range(1, max_rounds + 1):
            round_snapshot = ConsensusRound(
                round_number=round_number,
                preferences={
                    name: dict(prefs) for name, prefs in current_preferences.items()
                },
                adjustments={},
                discussions=(),
            )
            option_support = {
                option: sum(
                    prefs.get(option, 0.0) for prefs in current_preferences.values()
                )
                / len(self.team.agents)
                for option in options
            }
            max_support = max(option_support.values())
            leading = [
                option
                for option, support in option_support.items()
                if support == max_support
            ]
            if max_support >= threshold:
                status = ConsensusStatus.COMPLETED
                consensus_option = leading[0]
                explanation = (
                    f"Consensus reached on option '{consensus_option}' with {max_support*100:.1f}% support "
                    f"after {round_number} rounds of discussion."
                )
                rounds.append(round_snapshot)
                break

            adjustments = self._adjust_preferences(current_preferences, options)
            current_preferences = adjustments
            round_snapshot = ConsensusRound(
                round_number=round_number,
                preferences=round_snapshot.preferences,
                adjustments=adjustments,
                discussions=(),
            )
            rounds.append(round_snapshot)

        if status is ConsensusStatus.IN_PROGRESS:
            option_support = {
                option: sum(
                    prefs.get(option, 0.0) for prefs in current_preferences.values()
                )
                / len(self.team.agents)
                for option in options
            }
            max_support = max(option_support.values())
            leading = [
                option
                for option, support in option_support.items()
                if support == max_support
            ]
            consensus_option = leading[0]
            status = ConsensusStatus.PARTIAL
            explanation = (
                f"Partial consensus on option '{consensus_option}' with {max_support*100:.1f}% support "
                f"after {max_rounds} rounds of discussion."
            )

        result = ConsensusResult(
            status=status,
            result=consensus_option,
            explanation=explanation,
            rounds=rounds,
            final_preferences={
                name: dict(prefs) for name, prefs in current_preferences.items()
            },
        )

        return ConsensusTranscript(
            identifier=str(uuid4()),
            timestamp=datetime.now(),
            task_id=str(task.get("id", uuid4())),
            options=tuple(options),
            initial_preferences=initial_preferences,
            result=result,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_votes(
        self, options: Sequence[str], rng: Random
    ) -> tuple[Dict[str, str], Dict[str, str]]:
        votes: Dict[str, str] = {}
        reasoning: Dict[str, str] = {}
        for agent in self.team.agents:
            vote, explanation = self._vote_for_agent(agent, options, rng)
            votes[agent.name] = vote
            reasoning[agent.name] = explanation
        return votes, reasoning

    def _vote_for_agent(
        self, agent: SupportsTeamAgent, options: Sequence[str], rng: Random
    ) -> tuple[str, str]:
        expertise = getattr(agent, "expertise", None) or []
        if expertise:
            scores = {
                option: sum(1 for topic in expertise if topic.lower() in option.lower())
                for option in options
            }
            max_score = max(scores.values())
            best = [option for option, score in scores.items() if score == max_score]
            choice = rng.choice(best)
            explanation = "Selected based on expertise in " + ", ".join(
                topic for topic in expertise[:2]
            )
        else:
            choice = rng.choice(list(options))
            explanation = "No specific expertise, selected randomly"
        return choice, explanation

    def _apply_method(
        self,
        method: VoteMethod,
        task: TaskDict,
        options: Sequence[str],
        votes: Dict[str, str],
        vote_counts: Dict[str, int],
        rng: Random,
    ) -> VoteRecord:
        if method is VoteMethod.MAJORITY:
            return self._apply_majority(task, options, vote_counts, rng)
        if method is VoteMethod.WEIGHTED:
            domain = str(task.get("domain", "general"))
            return self._apply_weighted(task, options, votes, domain, rng)
        logger.warning(
            "Unknown voting method: %s, falling back to majority", method.value
        )
        return self._apply_majority(task, options, vote_counts, rng)

    def _apply_majority(
        self,
        task: TaskDict,
        options: Sequence[str],
        vote_counts: Dict[str, int],
        rng: Random,
    ) -> VoteRecord:
        max_votes = max(vote_counts.values())
        winners = [
            option for option, count in vote_counts.items() if count == max_votes
        ]
        if len(winners) > 1:
            return self._handle_tie(task, winners, rng)
        winner = winners[0]
        explanation = (
            f"Option '{winner}' received {max_votes} votes out of {len(self.team.agents)} "
            f"({max_votes/len(self.team.agents)*100:.1f}%)."
        )
        return VoteRecord(
            method=VoteMethod.MAJORITY,
            options=list(options),
            votes={},
            vote_counts=vote_counts,
            status=VoteStatus.COMPLETED,
            explanation=explanation,
            result={"winner": winner, "method": "majority_vote"},
        )

    def _handle_tie(
        self,
        task: TaskDict,
        tied_options: Sequence[str],
        rng: Random,
    ) -> VoteRecord:
        rng_instance = rng if rng is not None else Random()
        consensus = self.build_consensus(
            {"id": task.get("id"), "options": list(tied_options)}, rng=rng_instance
        )
        consensus_payload = (
            consensus if isinstance(consensus, dict) else consensus.as_dict()
        )
        return VoteRecord(
            method=VoteMethod.MAJORITY,
            options=list(tied_options),
            votes={},
            vote_counts={option: 0 for option in tied_options},
            status=VoteStatus.TIED,
            explanation="Vote tied; initiated consensus process.",
            result={
                "tied": True,
                "tied_options": list(tied_options),
                "consensus_result": consensus_payload,
            },
        )

    def _apply_weighted(
        self,
        task: TaskDict,
        options: Sequence[str],
        votes: Dict[str, str],
        domain: str,
        rng: Random,
    ) -> VoteRecord:
        weights = self._weight_agents(domain)
        weighted_votes = {
            option: sum(
                weights.get(agent, 1.0)
                for agent, choice in votes.items()
                if choice == option
            )
            for option in options
        }
        max_weight = max(weighted_votes.values())
        winners = [
            option for option, value in weighted_votes.items() if value == max_weight
        ]
        if len(winners) > 1:
            primus = self.team.get_primus()
            if primus and primus.name in votes and votes[primus.name] in winners:
                winner = votes[primus.name]
                explanation = (
                    f"Weighted vote tie between options {', '.join(winners)}. "
                    f"Tie broken by Primus ({primus.name}) who voted for '{winner}'."
                )
            else:
                winner = rng.choice(list(winners))
                explanation = (
                    f"Weighted vote tie between options {', '.join(winners)}. "
                    f"Tie broken by random selection, choosing '{winner}'."
                )
        else:
            winner = winners[0]
            explanation = f"Option '{winner}' received the highest weighted vote score of {max_weight:.1f}."
        return VoteRecord(
            method=VoteMethod.WEIGHTED,
            options=list(options),
            votes=votes,
            vote_counts={
                option: int(weighted_votes[option]) for option in weighted_votes
            },
            status=VoteStatus.COMPLETED,
            explanation=explanation,
            result={"winner": winner, "method": "weighted_vote"},
            weights=weights,
            weighted_votes=weighted_votes,
        )

    def _weight_agents(self, domain: str) -> Dict[str, float]:
        weights: Dict[str, float] = {}
        for agent in self.team.agents:
            expertise = getattr(agent, "expertise", None) or []
            base = 1.0
            bonus = sum(
                1.0
                for item in expertise
                if domain.lower() in item.lower() or item.lower() in domain.lower()
            )
            weights[agent.name] = base + bonus
        return weights

    def _initial_preferences(
        self, agent: SupportsTeamAgent, options: Sequence[str]
    ) -> Dict[str, float]:
        expertise = getattr(agent, "expertise", None) or []
        if expertise:
            scores = {
                option: sum(1 for item in expertise if item.lower() in option.lower())
                for option in options
            }
            total = float(sum(scores.values()) or 1.0)
            return {option: value / total for option, value in scores.items()}
        weight = 1.0 / len(options)
        return {option: weight for option in options}

    def _adjust_preferences(
        self,
        current_preferences: Mapping[str, Dict[str, float]],
        options: Sequence[str],
    ) -> Dict[str, Dict[str, float]]:
        adjustments: Dict[str, Dict[str, float]] = {}
        for agent_name, prefs in current_preferences.items():
            others = [
                p for name, p in current_preferences.items() if name != agent_name
            ]
            if not others:
                adjustments[agent_name] = dict(prefs)
                continue
            average = {
                option: sum(p.get(option, 0.0) for p in others) / len(others)
                for option in options
            }
            factor = 0.2
            adjusted = {
                option: prefs.get(option, 0.0) * (1 - factor) + average[option] * factor
                for option in options
            }
            total = sum(adjusted.values()) or 1.0
            adjustments[agent_name] = {
                option: value / total for option, value in adjusted.items()
            }
        return adjustments

    def _record_history(self, task: TaskDict, transcript: VotingTranscript) -> None:
        record = transcript.as_dict()
        record["task_context"] = {
            "id": task.get("id", "unknown"),
            "description": task.get("description", ""),
            "domain": task.get("domain", "general"),
        }
        record["voting_initiated"] = True
        self.team.voting_history.append(record)


def _normalise_options(raw_options: Iterable[object]) -> list[str]:
    options: list[str] = []
    for option in raw_options:
        if isinstance(option, Mapping):
            option_id = option.get("id")
            options.append(str(option_id))
        else:
            options.append(str(option))
    return options


def _count_votes(options: Sequence[str], votes: Mapping[str, str]) -> Dict[str, int]:
    return {
        option: sum(1 for vote in votes.values() if vote == option)
        for option in options
    }


def _engine(team: WSDETeam) -> VotingEngine:
    engine = getattr(team, "_voting_engine", None)
    if not isinstance(engine, VotingEngine):
        engine = VotingEngine(team)
        setattr(team, "_voting_engine", engine)
    return engine


def vote_on_critical_decision(
    self: WSDETeam, task: TaskDict, rng: Optional[Random] = None
) -> Dict[str, object]:
    result = _engine(self).vote(task, rng)
    return result if isinstance(result, dict) else result.as_dict()


def _apply_majority_voting(
    self: WSDETeam,
    task: TaskDict,
    voting_result: Dict[str, object],
    rng: Optional[Random] = None,
) -> Dict[str, object]:
    result = _engine(self).vote(task, rng)
    return result if isinstance(result, dict) else result.as_dict()


def _handle_tied_vote(
    self: WSDETeam,
    task: TaskDict,
    voting_result: Dict[str, object],
    vote_counts: Dict[str, int],
    tied_options: Sequence[str],
    rng: Optional[Random] = None,
) -> Dict[str, object]:
    rng_instance = rng if rng is not None else Random()
    record = _engine(self)._handle_tie(task, tied_options, rng_instance)
    transcript = VotingTranscript(
        identifier=str(uuid4()),
        timestamp=datetime.now(),
        task_id=str(task.get("id", uuid4())),
        method=VoteMethod.MAJORITY,
        options=tuple(tied_options),
        votes={},
        reasoning={},
        record=record,
    )
    result_dict: Dict[str, object] = transcript.as_dict()
    return result_dict


def _apply_weighted_voting(
    self: WSDETeam,
    task: TaskDict,
    voting_result: Dict[str, object],
    domain: str,
    rng: Optional[Random] = None,
) -> Dict[str, object]:
    engine = _engine(self)
    options = voting_result.get("options", [])
    options_list = (
        [str(opt) for opt in options] if isinstance(options, Iterable) else []
    )
    raw_votes = voting_result.get("votes", {})
    votes = (
        {str(agent): str(choice) for agent, choice in raw_votes.items()}
        if isinstance(raw_votes, Mapping)
        else {}
    )
    rng_instance = rng if rng is not None else Random()
    record = engine._apply_weighted(task, options_list, votes, domain, rng_instance)
    raw_winner = (
        record.result if isinstance(record.result, str) else record.result.get("winner")
    )
    winner = str(raw_winner) if raw_winner is not None else ""
    return {
        "options": options_list,
        "votes": votes,
        "status": record.status.value,
        "result": winner,
        "weighted_votes": record.weighted_votes or {},
        "weights": record.weights or {},
        "explanation": record.explanation,
    }


def _record_voting_history(
    self: WSDETeam, task: TaskDict, voting_result: Dict[str, object]
) -> None:
    self.voting_history.append(
        {
            **voting_result,
            "task_context": {
                "id": task.get("id", "unknown"),
                "description": task.get("description", ""),
                "domain": task.get("domain", "general"),
            },
        }
    )


def consensus_vote(
    self: WSDETeam, task: TaskDict, rng: Optional[Random] = None
) -> Dict[str, object]:
    return _engine(self).consensus_vote(task, rng)


def build_consensus(
    self: WSDETeam, task: TaskDict, rng: Optional[Random] = None
) -> Dict[str, object]:
    result = _engine(self).build_consensus(task, rng)
    return result if isinstance(result, dict) else result.as_dict()


__all__ = [
    "vote_on_critical_decision",
    "_apply_majority_voting",
    "_handle_tied_vote",
    "_apply_weighted_voting",
    "_record_voting_history",
    "consensus_vote",
    "build_consensus",
]
