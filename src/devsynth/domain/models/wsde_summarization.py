"""
Summarization utilities for WSDE teams.

This module provides methods for summarizing consensus and voting results.
It adds these methods to the WSDETeam class through monkey patching.
"""

from typing import Dict, Any, List


# Forward declaration for type hints
class WSDETeam:
    pass


def summarize_consensus_result(self, consensus_result: Dict[str, Any]) -> str:
    """
    Summarize a consensus result in a human-readable format.
    
    Args:
        consensus_result: The consensus result to summarize
        
    Returns:
        A string summary of the consensus result
    """
    if not consensus_result:
        return "No consensus result available."
        
    summary_parts = []
    
    # Add the consensus method
    method = consensus_result.get("method", "unknown")
    summary_parts.append(f"Consensus was reached using {method}.")
    
    # Add the majority opinion if available
    if "majority_opinion" in consensus_result:
        majority_opinion = consensus_result["majority_opinion"]
        summary_parts.append(f"The majority opinion is: {majority_opinion}")
        
    # Add synthesis information if available
    if "synthesis" in consensus_result:
        synthesis = consensus_result["synthesis"]
        if isinstance(synthesis, dict) and "text" in synthesis:
            summary_parts.append(f"Synthesis: {synthesis['text']}")
        elif isinstance(synthesis, str):
            summary_parts.append(f"Synthesis: {synthesis}")
            
    # Add information about conflicts if available
    if "conflicts_identified" in consensus_result:
        conflicts = consensus_result["conflicts_identified"]
        if conflicts == 1:
            summary_parts.append("1 conflict was identified and resolved.")
        else:
            summary_parts.append(f"{conflicts} conflicts were identified and resolved.")
            
    # Add stakeholder explanation if available
    if "stakeholder_explanation" in consensus_result:
        explanation = consensus_result["stakeholder_explanation"]
        summary_parts.append(f"Explanation: {explanation}")
        
    # Join all parts with newlines
    return "\n".join(summary_parts)


def summarize_voting_result(self, voting_result: Dict[str, Any]) -> str:
    """
    Summarize a voting result in a human-readable format.
    
    Args:
        voting_result: The voting result to summarize
        
    Returns:
        A string summary of the voting result
    """
    if not voting_result:
        return "No voting result available."
        
    summary_parts = []
    
    # Check if voting was completed
    status = voting_result.get("status", "unknown")
    if status != "completed":
        return f"Voting is not complete. Current status: {status}"
        
    # Get the result information
    result = voting_result.get("result", {})
    method = result.get("method", "unknown")
    winner = result.get("winner", "unknown")
    
    summary_parts.append(f"Voting was completed using {method}.")
    summary_parts.append(f"The winning option is: {winner}")
    
    # Add vote counts if available
    if "vote_counts" in voting_result:
        vote_counts = voting_result["vote_counts"]
        count_parts = []
        for option, count in vote_counts.items():
            count_parts.append(f"{option}: {count} votes")
        summary_parts.append("Vote distribution: " + ", ".join(count_parts))
        
    # Add vote weights if available
    if "vote_weights" in voting_result:
        weights = voting_result["vote_weights"]
        weight_parts = []
        for agent, weight in weights.items():
            weight_parts.append(f"{agent}: {weight:.2f}")
        summary_parts.append("Vote weights: " + ", ".join(weight_parts))
        
    # Add tie-breaking information if applicable
    if result.get("tie_broken", False):
        summary_parts.append(f"A tie was broken using {result.get('tie_breaker_method', 'unknown')}.")
        
    # Join all parts with newlines
    return "\n".join(summary_parts)


# Monkey patch the WSDETeam class to add the summarization methods
def _patch_wsde_team():
    """
    Add the summarization methods to the WSDETeam class.
    This function is called when this module is imported.
    """
    try:
        # Import the WSDETeam class
        from devsynth.domain.models.wsde import WSDETeam as ActualWSDETeam
        
        # Add the summarization methods to the WSDETeam class
        if not hasattr(ActualWSDETeam, 'summarize_consensus_result'):
            ActualWSDETeam.summarize_consensus_result = summarize_consensus_result
            
        if not hasattr(ActualWSDETeam, 'summarize_voting_result'):
            ActualWSDETeam.summarize_voting_result = summarize_voting_result
            
        # Log that the methods were added
        from devsynth.logging_setup import DevSynthLogger
        logger = DevSynthLogger(__name__)
        logger.info("Added summarization methods to WSDETeam class")
        
    except ImportError as e:
        # Log the error but don't raise it
        from devsynth.logging_setup import DevSynthLogger
        logger = DevSynthLogger(__name__)
        logger.warning(f"Failed to patch WSDETeam class: {e}")
        
# Call the patch function when this module is imported
_patch_wsde_team()