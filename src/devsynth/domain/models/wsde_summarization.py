"""Summarization helpers for WSDE teams."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from devsynth.domain.models.wsde_base import WSDETeam


def summarize_consensus_result(
    self: WSDETeam, consensus_result: dict[str, Any]
) -> str:
    """Summarize a consensus result in a human-readable format."""

    if not consensus_result:
        return "No consensus result available."

    summary_parts: list[str] = []

    method = consensus_result.get("method", "unknown")
    summary_parts.append(f"Consensus was reached using {method}.")

    if "majority_opinion" in consensus_result:
        majority_opinion = consensus_result["majority_opinion"]
        summary_parts.append(f"The majority opinion is: {majority_opinion}")

    if "synthesis" in consensus_result:
        synthesis = consensus_result["synthesis"]
        if isinstance(synthesis, dict) and "text" in synthesis:
            summary_parts.append(f"Synthesis: {synthesis['text']}")
        elif isinstance(synthesis, str):
            summary_parts.append(f"Synthesis: {synthesis}")

    if "conflicts_identified" in consensus_result:
        conflicts = consensus_result["conflicts_identified"]
        if conflicts == 1:
            summary_parts.append("1 conflict was identified and resolved.")
        else:
            summary_parts.append(f"{conflicts} conflicts were identified and resolved.")

    if "stakeholder_explanation" in consensus_result:
        explanation = consensus_result["stakeholder_explanation"]
        summary_parts.append(f"Explanation: {explanation}")

    return "\n".join(summary_parts)


def summarize_voting_result(self: WSDETeam, voting_result: dict[str, Any]) -> str:
    """Summarize a voting result in a human-readable format."""

    if not voting_result:
        return "No voting result available."

    summary_parts: list[str] = []

    status = voting_result.get("status", "unknown")
    if status != "completed":
        return f"Voting is not complete. Current status: {status}"

    winner = voting_result.get("winner")
    if winner:
        summary_parts.append(f"The winning option is: {winner}")

    if "vote_counts" in voting_result:
        vote_counts = voting_result["vote_counts"]
        count_parts = [
            f"{option}: {count} votes" for option, count in vote_counts.items()
        ]
        summary_parts.append("Vote distribution: " + ", ".join(count_parts))

    if "vote_weights" in voting_result:
        weights = voting_result["vote_weights"]
        weight_parts = [f"{agent}: {weight:.2f}" for agent, weight in weights.items()]
        summary_parts.append("Vote weights: " + ", ".join(weight_parts))

    if voting_result.get("tie_broken", False):
        summary_parts.append(
            f"A tie was broken using {voting_result.get('tie_breaker_method', 'unknown')}"
        )

    return "\n".join(summary_parts)


__all__ = ["summarize_consensus_result", "summarize_voting_result"]
