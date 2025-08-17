"""
WSDE voting and consensus building functionality.

This module contains functionality for voting and consensus building in a WSDE team,
including methods for voting on critical decisions, building consensus, and handling tied votes.
"""

import random
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Import the base WSDETeam class for type hints
from devsynth.domain.models.wsde_base import WSDETeam
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def vote_on_critical_decision(self: WSDETeam, task: Dict[str, Any]):
    """
    Conduct a vote on a critical decision.

    This method implements a democratic voting process where all team members
    vote on a critical decision. The voting can be weighted based on expertise
    or use simple majority voting.

    Args:
        task: The task containing the decision to be voted on

    Returns:
        Dictionary containing the voting results
    """
    if not self.agents:
        self.logger.warning("Cannot conduct vote: no agents in team")
        return {"status": "failed", "reason": "no_agents"}

    if "options" not in task or not task["options"]:
        self.logger.warning("Cannot conduct vote: no options provided")
        return {"status": "failed", "reason": "no_options"}

    raw_options = task["options"]
    options = [
        opt.get("id") if isinstance(opt, dict) else str(opt) for opt in raw_options
    ]
    voting_method = task.get("voting_method", "majority")
    domain = task.get("domain", "general")

    voting_result = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "task_id": task.get("id", str(uuid4())),
        "options": options,
        "votes": {},
        "method": voting_method,
        "status": "pending",
        "result": None,
        "vote_counts": {},
        "reasoning": {},
        "voting_initiated": True,
    }

    # Collect votes from all agents
    for agent in self.agents:
        # In a real implementation, this would call agent.vote() or similar
        # For now, we'll simulate voting based on agent expertise

        # Determine agent's vote
        if hasattr(agent, "expertise") and agent.expertise:
            # Calculate preference scores for each option
            option_scores = {}
            for option in options:
                score = 0
                for expertise in agent.expertise:
                    if expertise.lower() in option.lower():
                        score += 1
                option_scores[option] = score

            # Select option with highest score, or random if tied
            max_score = max(option_scores.values())
            best_options = [
                opt for opt, score in option_scores.items() if score == max_score
            ]
            vote = random.choice(best_options)

            # Generate reasoning
            reasoning = (
                f"Selected based on expertise in {', '.join(agent.expertise[:2])}"
            )
        else:
            # Random vote if no expertise
            vote = random.choice(options)
            reasoning = "No specific expertise, selected randomly"

        # Record vote
        voting_result["votes"][agent.name] = vote
        voting_result["reasoning"][agent.name] = reasoning

    # Count votes
    vote_counts = {
        opt: sum(1 for vote in voting_result["votes"].values() if vote == opt)
        for opt in options
    }
    voting_result["vote_counts"] = vote_counts

    # Determine result based on voting method
    if voting_method == "majority":
        voting_result = self._apply_majority_voting(task, voting_result)
    elif voting_method == "weighted":
        voting_result = self._apply_weighted_voting(task, voting_result, domain)
    else:
        self.logger.warning(f"Unknown voting method: {voting_method}, using majority")
        voting_result = self._apply_majority_voting(task, voting_result)

    if isinstance(voting_result.get("result"), str):
        voting_result["result"] = {
            "winner": voting_result["result"],
            "method": (
                "weighted_vote" if voting_method == "weighted" else "majority_vote"
            ),
        }
    elif isinstance(voting_result.get("result"), dict):
        voting_result["result"].setdefault(
            "method",
            "weighted_vote" if voting_method == "weighted" else "majority_vote",
        )

    self._record_voting_history(task, voting_result)

    return voting_result


def _apply_majority_voting(
    self: WSDETeam, task: Dict[str, Any], voting_result: Dict[str, Any]
):
    """
    Apply majority voting to determine the result.

    Args:
        task: The task containing the decision to be voted on
        voting_result: The voting result dictionary

    Returns:
        Updated voting result dictionary
    """
    options = voting_result["options"]
    vote_counts = voting_result["vote_counts"]

    # Find option(s) with most votes
    max_votes = max(vote_counts.values())
    winning_options = [opt for opt, count in vote_counts.items() if count == max_votes]

    # Check for tie
    if len(winning_options) > 1:
        return self._handle_tied_vote(task, voting_result, vote_counts, winning_options)

    winning_option = winning_options[0]
    voting_result["status"] = "completed"
    voting_result["result"] = winning_option
    voting_result["explanation"] = (
        f"Option '{winning_option}' received {max_votes} votes out of {len(self.agents)} "
        f"({max_votes/len(self.agents)*100:.1f}%)."
    )
    self.logger.info(
        f"Vote completed: '{winning_option}' won with {max_votes} votes "
        f"({max_votes/len(self.agents)*100:.1f}%)"
    )
    return voting_result


def _handle_tied_vote(
    self: WSDETeam,
    task: Dict[str, Any],
    voting_result: Dict[str, Any],
    vote_counts: Dict[str, int],
    tied_options: List[str],
):
    """Handle a tied vote by falling back to consensus building."""

    voting_result["status"] = "tied"
    voting_result["result"] = {"tied": True, "tied_options": tied_options}
    consensus = self.build_consensus({"id": task.get("id"), "options": tied_options})
    voting_result["result"]["consensus_result"] = consensus
    return voting_result


def _apply_weighted_voting(
    self: WSDETeam, task: Dict[str, Any], voting_result: Dict[str, Any], domain: str
):
    """
    Apply weighted voting based on agent expertise in the specified domain.

    Args:
        task: The task containing the decision to be voted on
        voting_result: The voting result dictionary
        domain: The domain to use for weighting votes

    Returns:
        Updated voting result dictionary
    """
    options = voting_result["options"]
    votes = voting_result["votes"]

    # Calculate weights based on expertise in the domain
    weights = {}
    for agent in self.agents:
        if hasattr(agent, "expertise") and agent.expertise:
            # Calculate domain relevance score
            domain_score = 1.0  # Base weight
            for expertise in agent.expertise:
                if (
                    domain.lower() in expertise.lower()
                    or expertise.lower() in domain.lower()
                ):
                    domain_score += 1.0  # Increase weight for domain-relevant expertise
            weights[agent.name] = domain_score
        else:
            weights[agent.name] = 1.0  # Default weight

    # Calculate weighted votes
    weighted_votes = {}
    for option in options:
        weighted_votes[option] = sum(
            weights.get(agent_name, 1.0)
            for agent_name, vote in votes.items()
            if vote == option
        )

    # Find option(s) with highest weighted votes
    max_weighted_votes = max(weighted_votes.values())
    winning_options = [
        opt for opt, count in weighted_votes.items() if count == max_weighted_votes
    ]

    # Check for tie
    if len(winning_options) > 1:
        # Handle tie
        # For weighted voting, we'll use the primus as tie-breaker
        primus = self.get_primus()
        if primus and primus.name in votes:
            primus_vote = votes[primus.name]
            if primus_vote in winning_options:
                # Primus voted for one of the tied options
                winning_option = primus_vote
                voting_result["status"] = "completed"
                voting_result["result"] = winning_option
                voting_result["weighted_votes"] = weighted_votes
                voting_result["weights"] = weights
                voting_result["explanation"] = (
                    f"Weighted vote tie between options {', '.join(winning_options)}. "
                    f"Tie broken by Primus ({primus.name}) who voted for '{winning_option}'."
                )

                self.logger.info(
                    f"Weighted vote tie resolved by Primus: '{winning_option}' selected by {primus.name}"
                )
            else:
                # Primus didn't vote for any of the tied options, use random
                winning_option = random.choice(winning_options)
                voting_result["status"] = "completed"
                voting_result["result"] = winning_option
                voting_result["weighted_votes"] = weighted_votes
                voting_result["weights"] = weights
                voting_result["explanation"] = (
                    f"Weighted vote tie between options {', '.join(winning_options)}. "
                    f"Tie broken by random selection, choosing '{winning_option}'."
                )

                self.logger.info(
                    f"Weighted vote tie resolved randomly: '{winning_option}' selected"
                )
        else:
            # No primus or primus didn't vote, use random
            winning_option = random.choice(winning_options)
            voting_result["status"] = "completed"
            voting_result["result"] = winning_option
            voting_result["weighted_votes"] = weighted_votes
            voting_result["weights"] = weights
            voting_result["explanation"] = (
                f"Weighted vote tie between options {', '.join(winning_options)}. "
                f"Tie broken by random selection, choosing '{winning_option}'."
            )

            self.logger.info(
                f"Weighted vote tie resolved randomly: '{winning_option}' selected"
            )
    else:
        # Clear winner
        winning_option = winning_options[0]
        voting_result["status"] = "completed"
        voting_result["result"] = winning_option
        voting_result["weighted_votes"] = weighted_votes
        voting_result["weights"] = weights
        voting_result["explanation"] = (
            f"Option '{winning_option}' received the highest weighted vote score of {max_weighted_votes:.1f}."
        )

        self.logger.info(
            f"Weighted vote completed: '{winning_option}' won with score {max_weighted_votes:.1f}"
        )

    return voting_result


def _record_voting_history(
    self: WSDETeam, task: Dict[str, Any], voting_result: Dict[str, Any]
):
    """
    Record voting history for future reference.

    Args:
        task: The task containing the decision that was voted on
        voting_result: The voting result dictionary
    """
    # Add task context to the voting result
    voting_record = voting_result.copy()
    voting_record["task_context"] = {
        "id": task.get("id", "unknown"),
        "description": task.get("description", ""),
        "domain": task.get("domain", "general"),
    }

    # Add to voting history
    self.voting_history.append(voting_record)
    self.logger.debug(f"Recorded voting result for task {task.get('id', 'unknown')}")


def consensus_vote(self: WSDETeam, task: Dict[str, Any]):
    """
    Conduct a simple consensus vote.

    This is a simplified version of vote_on_critical_decision that uses
    majority voting without complex tie-breaking strategies.

    Args:
        task: The task containing the decision to be voted on

    Returns:
        Dictionary containing the voting results
    """
    # Create a simplified task with majority voting
    consensus_task = task.copy()
    consensus_task["voting_method"] = "majority"
    consensus_task["tie_strategy"] = "random"

    # Conduct the vote
    result = self.vote_on_critical_decision(consensus_task)

    # Simplify the result
    simplified_result = {
        "status": result["status"],
        "decision": result["result"],
        "explanation": result["explanation"] if "explanation" in result else "",
        "vote_counts": result["vote_counts"] if "vote_counts" in result else {},
    }

    return simplified_result


def build_consensus(self: WSDETeam, task: Dict[str, Any]):
    """
    Build consensus through a collaborative decision-making process.

    This method implements a more sophisticated consensus-building process
    that involves discussion, compromise, and iterative refinement of options.

    Args:
        task: The task to build consensus on

    Returns:
        Dictionary containing the consensus result
    """
    if not self.agents:
        self.logger.warning("Cannot build consensus: no agents in team")
        return {"status": "failed", "reason": "no_agents"}

    if "options" not in task or not task["options"]:
        self.logger.warning("Cannot build consensus: no options provided")
        return {"status": "failed", "reason": "no_options"}

    # Extract consensus parameters
    options = task["options"]
    domain = task.get("domain", "general")
    consensus_threshold = task.get(
        "consensus_threshold", 0.75
    )  # Percentage required for consensus
    max_rounds = task.get("max_rounds", 3)  # Maximum number of discussion rounds

    # Initialize consensus result
    consensus_result = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "task_id": task.get("id", str(uuid4())),
        "options": options,
        "initial_preferences": {},
        "final_preferences": {},
        "rounds": [],
        "status": "in_progress",
        "result": None,
        "explanation": "",
    }

    # Collect initial preferences from all agents
    for agent in self.agents:
        # In a real implementation, this would call agent.evaluate_options() or similar
        # For now, we'll simulate preferences based on agent expertise

        # Determine agent's preferences
        if hasattr(agent, "expertise") and agent.expertise:
            # Calculate preference scores for each option
            option_scores = {}
            for option in options:
                score = 0
                for expertise in agent.expertise:
                    if expertise.lower() in option.lower():
                        score += 1
                option_scores[option] = score

            # Normalize scores to sum to 1.0
            total_score = sum(option_scores.values()) or 1.0  # Avoid division by zero
            preferences = {
                opt: score / total_score for opt, score in option_scores.items()
            }
        else:
            # Equal preferences if no expertise
            preferences = {opt: 1.0 / len(options) for opt in options}

        consensus_result["initial_preferences"][agent.name] = preferences

    # Copy initial preferences to current preferences
    current_preferences = {
        agent.name: prefs.copy()
        for agent, prefs in zip(
            self.agents, consensus_result["initial_preferences"].values()
        )
    }

    # Consensus building rounds
    for round_num in range(1, max_rounds + 1):
        round_result = {
            "round": round_num,
            "preferences": current_preferences.copy(),
            "discussions": [],
            "adjustments": {},
        }

        # Calculate current consensus level
        option_support = {
            opt: sum(prefs.get(opt, 0) for prefs in current_preferences.values())
            / len(self.agents)
            for opt in options
        }
        max_support = max(option_support.values())
        leading_options = [
            opt for opt, support in option_support.items() if support == max_support
        ]

        # Check if we've reached consensus
        if max_support >= consensus_threshold:
            # Consensus reached
            consensus_option = leading_options[0]  # If multiple, take the first one
            consensus_result["status"] = "completed"
            consensus_result["result"] = consensus_option
            consensus_result["final_preferences"] = current_preferences
            consensus_result["rounds"].append(round_result)
            consensus_result["explanation"] = (
                f"Consensus reached on option '{consensus_option}' with {max_support*100:.1f}% support "
                f"after {round_num} rounds of discussion."
            )

            self.logger.info(
                f"Consensus built: '{consensus_option}' selected with {max_support*100:.1f}% support"
            )
            break

        # No consensus yet, simulate discussion and preference adjustments
        # In a real implementation, this would involve agent interactions

        # For each agent, adjust preferences based on leading options and other agents' preferences
        adjustments = {}
        for agent in self.agents:
            agent_prefs = current_preferences[agent.name]

            # Calculate average preferences of other agents
            other_agents = [a for a in self.agents if a.name != agent.name]
            if other_agents:
                other_prefs = {
                    opt: sum(
                        current_preferences[a.name].get(opt, 0) for a in other_agents
                    )
                    / len(other_agents)
                    for opt in options
                }

                # Adjust preferences slightly toward group average
                adjustment_factor = 0.2  # How much to adjust toward group consensus
                adjusted_prefs = {}
                for opt in options:
                    # Move preference toward group average
                    adjusted_prefs[opt] = (
                        agent_prefs[opt] * (1 - adjustment_factor)
                        + other_prefs[opt] * adjustment_factor
                    )

                # Normalize adjusted preferences
                total = sum(adjusted_prefs.values()) or 1.0
                adjusted_prefs = {
                    opt: score / total for opt, score in adjusted_prefs.items()
                }

                # Record adjustment
                adjustments[agent.name] = adjusted_prefs

        # Update preferences for next round
        current_preferences = adjustments
        round_result["adjustments"] = adjustments
        consensus_result["rounds"].append(round_result)

    # If we exit the loop without reaching consensus, use the option with highest support
    if consensus_result["status"] == "in_progress":
        # Calculate final support levels
        option_support = {
            opt: sum(prefs.get(opt, 0) for prefs in current_preferences.values())
            / len(self.agents)
            for opt in options
        }
        max_support = max(option_support.values())
        leading_options = [
            opt for opt, support in option_support.items() if support == max_support
        ]

        consensus_option = leading_options[0]  # If multiple, take the first one
        consensus_result["status"] = "partial_consensus"
        consensus_result["result"] = consensus_option
        consensus_result["final_preferences"] = current_preferences
        consensus_result["explanation"] = (
            f"Partial consensus on option '{consensus_option}' with {max_support*100:.1f}% support "
            f"after {max_rounds} rounds of discussion."
        )

        self.logger.info(
            f"Partial consensus: '{consensus_option}' selected with {max_support*100:.1f}% support"
        )

    return consensus_result
