"""
WSDE knowledge integration and memory management functionality.

This module contains functionality for knowledge integration and memory management
in a WSDE team, including methods for applying dialectical reasoning with knowledge
graph, generating antithesis and synthesis with knowledge graph, and identifying
relevant knowledge.

See ``docs/specifications/finalize-dialectical-reasoning.md`` for the
requirements that drive these reasoning utilities.
"""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Tuple
from uuid import uuid4

# Import the base WSDETeam class for type hints
from devsynth.domain.models.wsde_base import WSDETeam
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass(frozen=True)
class KnowledgeGraphBestPractice:
    """Structured representation of a best practice from the knowledge graph."""

    name: str
    description: str = ""
    keywords: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "KnowledgeGraphBestPractice":
        """Create a best practice entry from a raw payload."""

        if not isinstance(payload, Mapping):
            raise TypeError("Best practice payload must be a mapping")

        name = str(payload.get("name", "")).strip()
        description_raw = payload.get("description", "")
        description = (
            str(description_raw).strip() if description_raw is not None else ""
        )

        keywords_raw = payload.get("keywords", [])
        keywords: tuple[str, ...]
        if isinstance(keywords_raw, Iterable) and not isinstance(
            keywords_raw, (str, bytes)
        ):
            keywords = tuple(
                str(keyword).strip() for keyword in keywords_raw if keyword
            )
        else:
            keywords = ()

        return cls(name=name, description=description, keywords=keywords)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the best practice into a JSON-compatible dictionary."""

        return {
            "name": self.name,
            "description": self.description,
            "keywords": list(self.keywords),
        }


@dataclass(frozen=True)
class KnowledgeGraphSimilarSolution:
    """Structured representation of a similar solution from the knowledge graph."""

    approach: str | None = None
    strengths: tuple[str, ...] = ()
    key_insights: tuple[str, ...] = ()

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, Any]
    ) -> "KnowledgeGraphSimilarSolution":
        """Create a similar solution entry from a raw payload."""

        if not isinstance(payload, Mapping):
            raise TypeError("Similar solution payload must be a mapping")

        approach_raw = payload.get("approach")
        approach = str(approach_raw).strip() if approach_raw is not None else None

        strengths_raw = payload.get("strengths", [])
        if isinstance(strengths_raw, Iterable) and not isinstance(
            strengths_raw, (str, bytes)
        ):
            strengths = tuple(
                str(strength).strip() for strength in strengths_raw if strength
            )
        else:
            strengths = ()

        insights_raw = payload.get("key_insights", [])
        if isinstance(insights_raw, Iterable) and not isinstance(
            insights_raw, (str, bytes)
        ):
            key_insights = tuple(
                str(insight).strip() for insight in insights_raw if insight
            )
        else:
            key_insights = ()

        return cls(approach=approach, strengths=strengths, key_insights=key_insights)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the similar solution into a JSON-compatible dictionary."""

        return {
            "approach": self.approach,
            "strengths": list(self.strengths),
            "key_insights": list(self.key_insights),
        }


@dataclass(frozen=True)
class KnowledgeGraphInsights:
    """Collection of structured knowledge graph artifacts used for reasoning."""

    similar_solutions: tuple[KnowledgeGraphSimilarSolution, ...] = ()
    best_practices: tuple[KnowledgeGraphBestPractice, ...] = ()

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, Any] | None
    ) -> "KnowledgeGraphInsights":
        """Create an insights bundle from the raw knowledge graph response."""

        if payload is None:
            return cls()

        if not isinstance(payload, Mapping):
            raise TypeError("Knowledge graph insights payload must be a mapping")

        similar_raw = payload.get("similar_solutions", [])
        similar: tuple[KnowledgeGraphSimilarSolution, ...]
        if isinstance(similar_raw, Iterable) and not isinstance(
            similar_raw, (str, bytes)
        ):
            similar = tuple(
                KnowledgeGraphSimilarSolution.from_payload(item)
                for item in similar_raw
                if isinstance(item, Mapping)
            )
        else:
            similar = ()

        practices_raw = payload.get("best_practices", [])
        if isinstance(practices_raw, Iterable) and not isinstance(
            practices_raw, (str, bytes)
        ):
            practices = tuple(
                KnowledgeGraphBestPractice.from_payload(item)
                for item in practices_raw
                if isinstance(item, Mapping)
            )
        else:
            practices = ()

        return cls(similar_solutions=similar, best_practices=practices)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the insights into a JSON-compatible dictionary."""

        return {
            "similar_solutions": [
                solution.to_dict() for solution in self.similar_solutions
            ],
            "best_practices": [practice.to_dict() for practice in self.best_practices],
        }


def apply_dialectical_reasoning_with_knowledge_graph(
    self: WSDETeam,
    task: dict[str, Any],
    critic_agent: Any,
    wsde_memory_integration: Any,
):
    """
    Apply dialectical reasoning with knowledge graph integration.

    This method implements a dialectical reasoning process that leverages
    a knowledge graph to enhance the antithesis and synthesis generation.

    Args:
        task: The task containing the thesis to be analyzed
        critic_agent: The agent that will generate the antithesis
        wsde_memory_integration: Memory integration component for knowledge graph access

    Returns:
        Dictionary containing the dialectical reasoning results
    """
    if not task or "solution" not in task:
        self.logger.warning("Cannot apply dialectical reasoning: no solution provided")
        return {"status": "failed", "reason": "no_solution"}

    if not wsde_memory_integration:
        self.logger.warning(
            "Cannot apply dialectical reasoning with knowledge graph: no memory integration provided"
        )
        return {"status": "failed", "reason": "no_memory_integration"}

    # Extract the thesis solution
    thesis_solution = task["solution"]

    # Get task ID for memory retrieval
    task_id = self._get_task_id(task)

    # Retrieve relevant knowledge from the knowledge graph
    raw_insights = wsde_memory_integration.retrieve_relevant_knowledge(
        task_id=task_id,
        query=task.get("description", ""),
        solution=thesis_solution,
        max_results=10,
    )
    knowledge_graph_insights = KnowledgeGraphInsights.from_payload(raw_insights)

    # Generate antithesis with knowledge graph insights
    antithesis = self._generate_antithesis_with_knowledge_graph(
        thesis_solution, critic_agent, knowledge_graph_insights
    )

    # Generate synthesis with knowledge graph insights
    synthesis = self._generate_synthesis_with_knowledge_graph(
        thesis_solution, antithesis, knowledge_graph_insights
    )

    # Generate evaluation with knowledge graph insights
    evaluation = self._generate_evaluation_with_knowledge_graph(
        synthesis, antithesis, task, knowledge_graph_insights
    )

    # Create result
    result = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "task_id": task_id,
        "thesis": thesis_solution,
        "antithesis": antithesis,
        "synthesis": synthesis,
        "evaluation": evaluation,
        "knowledge_graph_insights": knowledge_graph_insights.to_dict(),
        "method": "dialectical_reasoning_with_knowledge_graph",
    }

    # Invoke dialectical hooks if any
    for hook in self.dialectical_hooks:
        hook(task, [result])

    # Store result in memory
    wsde_memory_integration.store_dialectical_result(task, result)

    return result


def _get_task_id(self: WSDETeam, task: dict[str, Any]):
    """
    Get a unique identifier for a task.

    Args:
        task: The task to identify

    Returns:
        String identifier for the task
    """
    # Use existing ID if available
    if "id" in task:
        return task["id"]

    # Generate ID based on task content
    task_hash = hash(
        str(task.get("description", "")) + str(task.get("requirements", ""))
    )
    return f"task_{task_hash}"


def _generate_antithesis_with_knowledge_graph(
    self: WSDETeam,
    thesis_solution: dict[str, Any],
    critic_agent: Any,
    knowledge_graph_insights: KnowledgeGraphInsights,
):
    """
    Generate an antithesis using knowledge graph insights.

    Args:
        thesis_solution: The thesis solution
        critic_agent: The agent that will generate the antithesis
        knowledge_graph_insights: Insights from the knowledge graph

    Returns:
        Dictionary containing the antithesis
    """
    # In a real implementation, this would call critic_agent.critique() with knowledge_graph_insights
    # For now, we'll generate a simulated antithesis

    antithesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "agent": critic_agent.name if hasattr(critic_agent, "name") else "critic",
        "critiques": [],
        "alternative_approaches": [],
        "improvement_suggestions": [],
        "knowledge_based_critiques": [],
    }

    # Generate critiques based on thesis content
    if "content" in thesis_solution:
        content = thesis_solution["content"]

        # Simulate finding issues in the content
        if isinstance(content, str):
            # Check for common issues in text content
            if len(content) < 100:
                antithesis["critiques"].append("Content is too brief and lacks detail")

            if "example" not in content.lower():
                antithesis["critiques"].append(
                    "No examples provided to illustrate concepts"
                )

            # Suggest improvements
            antithesis["improvement_suggestions"].append(
                "Add more detailed explanations"
            )
            antithesis["improvement_suggestions"].append("Include concrete examples")

            # Suggest alternative approaches
            antithesis["alternative_approaches"].append(
                "Consider a more structured format with sections"
            )
            antithesis["alternative_approaches"].append(
                "Add visual diagrams to complement text"
            )

    # Generate critiques based on thesis code
    if "code" in thesis_solution:
        code = thesis_solution["code"]

        # Simulate finding issues in the code
        if isinstance(code, str):
            # Check for common issues in code
            if "try" in code and "except" not in code:
                antithesis["critiques"].append(
                    "Try block without proper exception handling"
                )

            if "print(" in code:
                antithesis["critiques"].append(
                    "Using print statements instead of proper logging"
                )

            # Suggest improvements
            antithesis["improvement_suggestions"].append(
                "Add proper error handling with try/except blocks"
            )
            antithesis["improvement_suggestions"].append(
                "Replace print statements with logger calls"
            )

            # Suggest alternative approaches
            antithesis["alternative_approaches"].append(
                "Consider using a context manager for resource handling"
            )
            antithesis["alternative_approaches"].append(
                "Implement a more modular design with smaller functions"
            )

    # Generate knowledge-based critiques
    for solution in knowledge_graph_insights.similar_solutions:
        for strength in solution.strengths:
            if not any(
                strength.lower() in critique.lower()
                for critique in antithesis["critiques"]
            ):
                antithesis["knowledge_based_critiques"].append(
                    f"Solution lacks {strength} which was effective in similar cases"
                )

        if solution.approach:
            antithesis["alternative_approaches"].append(
                f"Consider alternative approach: {solution.approach}"
            )

    # Generate critiques based on best practices from knowledge graph
    for practice in knowledge_graph_insights.best_practices:
        practice_name = practice.name
        practice_description = practice.description

        # Check if the solution follows this best practice
        if "content" in thesis_solution and isinstance(thesis_solution["content"], str):
            if practice_name.lower() not in thesis_solution["content"].lower():
                antithesis["knowledge_based_critiques"].append(
                    f"Solution does not follow best practice: {practice_name} - {practice_description}"
                )

        if "code" in thesis_solution and isinstance(thesis_solution["code"], str):
            if practice_name.lower() not in thesis_solution["code"].lower():
                antithesis["knowledge_based_critiques"].append(
                    f"Code does not implement best practice: {practice_name} - {practice_description}"
                )

    # If no specific critiques were generated, add some generic ones
    if not antithesis["critiques"] and not antithesis["knowledge_based_critiques"]:
        antithesis["critiques"] = [
            "The solution lacks comprehensive error handling",
            "The approach could be more efficient",
            "The solution doesn't consider all edge cases",
        ]

        antithesis["improvement_suggestions"] = [
            "Add more robust error handling",
            "Optimize the approach for better efficiency",
            "Consider additional edge cases",
        ]

        antithesis["alternative_approaches"] = [
            "Consider a different algorithm that handles edge cases better",
            "Implement a more modular design for better maintainability",
        ]

    return antithesis


def _generate_synthesis_with_knowledge_graph(
    self: WSDETeam,
    thesis_solution: dict[str, Any],
    antithesis: dict[str, Any],
    knowledge_graph_insights: KnowledgeGraphInsights,
):
    """
    Generate a synthesis using knowledge graph insights.

    Args:
        thesis_solution: The thesis solution
        antithesis: The antithesis with critiques and suggestions
        knowledge_graph_insights: Insights from the knowledge graph

    Returns:
        Dictionary containing the synthesis
    """
    synthesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "integrated_critiques": [],
        "rejected_critiques": [],
        "improvements": [],
        "knowledge_integrations": [],
        "reasoning": "",
        "content": None,
        "code": None,
    }

    # Extract content and code from thesis
    original_content = thesis_solution.get("content", "")
    original_code = thesis_solution.get("code", "")

    # Initialize improved content and code
    improved_content = original_content
    improved_code = original_code

    # Process regular critiques
    critiques = antithesis.get("critiques", [])
    for critique in critiques:
        # Process content-related critiques
        if (
            "content" in critique.lower()
            or "brief" in critique.lower()
            or "detail" in critique.lower()
            or "example" in critique.lower()
        ):
            if original_content:
                # Simulate improving content
                improved_content = (
                    "# Improved based on critique: "
                    + critique
                    + "\n\n"
                    + improved_content
                )
                synthesis["integrated_critiques"].append(critique)
                synthesis["improvements"].append(
                    "Enhanced content with more detail and examples"
                )

        # Process code-related critiques
        elif (
            "code" in critique.lower()
            or "error handling" in critique.lower()
            or "exception" in critique.lower()
            or "logging" in critique.lower()
        ):
            if original_code:
                # Simulate improving code
                improved_code = (
                    "# Improved based on critique: " + critique + "\n\n" + improved_code
                )
                synthesis["integrated_critiques"].append(critique)
                synthesis["improvements"].append(
                    "Enhanced code with better error handling and logging"
                )

    # Process knowledge-based critiques
    knowledge_critiques = antithesis.get("knowledge_based_critiques", [])
    for critique in knowledge_critiques:
        # Simulate integrating knowledge-based improvements
        if "best practice" in critique.lower():
            if original_code:
                improved_code = (
                    "# Implemented best practice from knowledge graph\n" + improved_code
                )
            if original_content:
                improved_content = (
                    "# Incorporated best practice from knowledge graph\n\n"
                    + improved_content
                )

            synthesis["integrated_critiques"].append(critique)
            synthesis["knowledge_integrations"].append(
                "Implemented best practice from knowledge graph"
            )

        elif (
            "similar cases" in critique.lower()
            or "similar solutions" in critique.lower()
        ):
            if original_code:
                improved_code = (
                    "# Integrated insights from similar solutions\n" + improved_code
                )
            if original_content:
                improved_content = (
                    "# Applied patterns from similar successful solutions\n\n"
                    + improved_content
                )

            synthesis["integrated_critiques"].append(critique)
            synthesis["knowledge_integrations"].append(
                "Integrated insights from similar solutions"
            )

    # Integrate knowledge from similar solutions
    for solution in knowledge_graph_insights.similar_solutions:
        for insight in solution.key_insights:
            synthesis["knowledge_integrations"].append(f"Integrated insight: {insight}")

    # Integrate best practices from knowledge graph
    for practice in knowledge_graph_insights.best_practices[
        :3
    ]:  # Limit to top 3 practices
        synthesis["knowledge_integrations"].append(
            f"Applied best practice: {practice.name}"
        )

    # Set improved content and code
    if improved_content != original_content:
        synthesis["content"] = improved_content

    if improved_code != original_code:
        synthesis["code"] = improved_code

    # Identify critiques that weren't integrated
    all_critiques = critiques + knowledge_critiques
    all_integrated = set(synthesis["integrated_critiques"])
    synthesis["rejected_critiques"] = [
        c for c in all_critiques if c not in all_integrated
    ]

    # Generate reasoning
    reasoning_parts = []

    # Summarize integrated critiques
    if synthesis["integrated_critiques"]:
        reasoning_parts.append("## Integrated Critiques")
        for critique in synthesis["integrated_critiques"]:
            reasoning_parts.append(f"- {critique}")

    # Summarize knowledge integrations
    if synthesis["knowledge_integrations"]:
        reasoning_parts.append("\n## Knowledge Graph Integrations")
        for integration in synthesis["knowledge_integrations"]:
            reasoning_parts.append(f"- {integration}")

    # Summarize improvements
    if synthesis["improvements"]:
        reasoning_parts.append("\n## Improvements")
        for improvement in synthesis["improvements"]:
            reasoning_parts.append(f"- {improvement}")

    # Combine all parts
    synthesis["reasoning"] = "\n".join(reasoning_parts)

    return synthesis


def _generate_evaluation_with_knowledge_graph(
    self: WSDETeam,
    synthesis: dict[str, Any],
    antithesis: dict[str, Any],
    task: dict[str, Any],
    knowledge_graph_insights: KnowledgeGraphInsights,
):
    """
    Generate an evaluation using knowledge graph insights.

    Args:
        synthesis: The synthesis solution
        antithesis: The antithesis with critiques
        task: The original task
        knowledge_graph_insights: Insights from the knowledge graph

    Returns:
        Dictionary containing the evaluation
    """
    evaluation = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "strengths": [],
        "weaknesses": [],
        "alignment_with_knowledge": [],
        "overall_assessment": "",
        "confidence_score": 0.0,
    }

    # Identify strengths
    # 1. Critiques that were addressed
    integrated_critiques = synthesis.get("integrated_critiques", [])
    if integrated_critiques:
        evaluation["strengths"].append(
            f"Addressed {len(integrated_critiques)} critiques from the antithesis"
        )

    # 2. Knowledge integrations
    knowledge_integrations = synthesis.get("knowledge_integrations", [])
    if knowledge_integrations:
        evaluation["strengths"].append(
            f"Successfully integrated {len(knowledge_integrations)} insights from the knowledge graph"
        )

    # 3. Improvements made
    improvements = synthesis.get("improvements", [])
    if improvements:
        for improvement in improvements:
            evaluation["strengths"].append(f"Improvement: {improvement}")

    # Identify weaknesses
    # 1. Critiques that were not addressed
    rejected_critiques = synthesis.get("rejected_critiques", [])
    if rejected_critiques:
        evaluation["weaknesses"].append(
            f"Failed to address {len(rejected_critiques)} critiques"
        )
        if len(rejected_critiques) <= 3:
            for critique in rejected_critiques:
                evaluation["weaknesses"].append(f"Unaddressed critique: {critique}")

    # 2. Missing best practices from knowledge graph
    if knowledge_graph_insights.best_practices:
        best_practice_names = [
            practice.name for practice in knowledge_graph_insights.best_practices
        ]

        # Check which best practices were integrated
        integrated_practices = []
        for integration in knowledge_integrations:
            for practice in best_practice_names:
                if practice in integration:
                    integrated_practices.append(practice)

        # Identify missing practices
        missing_practices = [
            practice
            for practice in best_practice_names
            if practice not in integrated_practices
        ]
        if missing_practices:
            evaluation["weaknesses"].append(
                f"Did not integrate {len(missing_practices)} relevant best practices"
            )
            if len(missing_practices) <= 3:
                for practice in missing_practices:
                    evaluation["weaknesses"].append(
                        f"Missing best practice: {practice}"
                    )

    # Evaluate alignment with knowledge graph
    for solution in knowledge_graph_insights.similar_solutions:
        if not solution.approach:
            continue

        approach = solution.approach
        if (
            synthesis.get("content")
            and approach.lower() in synthesis["content"].lower()
        ):
            evaluation["alignment_with_knowledge"].append(
                f"Solution aligns with successful approach: {approach}"
            )
        elif synthesis.get("code") and approach.lower() in synthesis["code"].lower():
            evaluation["alignment_with_knowledge"].append(
                f"Solution aligns with successful approach: {approach}"
            )
        else:
            evaluation["alignment_with_knowledge"].append(
                f"Solution differs from successful approach: {approach}"
            )

    # Calculate confidence score (0.0 to 1.0)
    # Based on strengths, weaknesses, and knowledge alignment
    strength_score = len(evaluation["strengths"]) * 0.1
    weakness_penalty = len(evaluation["weaknesses"]) * 0.1
    alignment_score = (
        sum(1 for item in evaluation["alignment_with_knowledge"] if "aligns" in item)
        * 0.1
    )

    confidence_score = min(
        1.0, max(0.0, 0.5 + strength_score - weakness_penalty + alignment_score)
    )
    evaluation["confidence_score"] = round(confidence_score, 2)

    # Generate overall assessment
    if confidence_score >= 0.8:
        assessment = "Excellent solution that effectively addresses critiques and integrates knowledge graph insights."
    elif confidence_score >= 0.6:
        assessment = "Good solution that addresses most critiques and incorporates knowledge graph insights, with some room for improvement."
    elif confidence_score >= 0.4:
        assessment = "Adequate solution that addresses some critiques and knowledge graph insights, but has significant room for improvement."
    else:
        assessment = "Limited solution that fails to adequately address critiques or integrate knowledge graph insights."

    evaluation["overall_assessment"] = (
        f"{assessment} (Confidence: {confidence_score:.2f})"
    )

    return evaluation


def apply_enhanced_dialectical_reasoning_with_knowledge(
    self: WSDETeam,
    task: dict[str, Any],
    critic_agent: Any,
    external_knowledge: dict[str, Any],
):
    """
    Apply enhanced dialectical reasoning with external knowledge.

    This method implements an advanced dialectical reasoning process that
    incorporates external knowledge to enhance the antithesis and synthesis.

    Args:
        task: The task containing the thesis to be analyzed
        critic_agent: The agent that will generate the antithesis
        external_knowledge: External knowledge to incorporate

    Returns:
        Dictionary containing the dialectical reasoning results
    """
    if not task or "solution" not in task:
        self.logger.warning(
            "Cannot apply enhanced dialectical reasoning: no solution provided"
        )
        return {"status": "failed", "reason": "no_solution"}

    # Extract the thesis solution
    thesis_solution = task["solution"]

    # Identify relevant knowledge for this task and solution
    relevant_knowledge = self._identify_relevant_knowledge(
        task, thesis_solution, external_knowledge
    )

    # Generate enhanced antithesis with knowledge
    antithesis = self._generate_enhanced_antithesis_with_knowledge(
        thesis_solution, critic_agent, relevant_knowledge
    )

    # Generate enhanced synthesis with knowledge
    synthesis = self._generate_enhanced_synthesis_with_standards(
        thesis_solution, antithesis, relevant_knowledge
    )

    # Generate evaluation with compliance checks
    evaluation = self._generate_evaluation_with_compliance(
        synthesis, antithesis, task, relevant_knowledge
    )

    # Create result
    result = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "task_id": task.get("id", str(uuid4())),
        "thesis": thesis_solution,
        "antithesis": antithesis,
        "synthesis": synthesis,
        "evaluation": evaluation,
        "relevant_knowledge": relevant_knowledge,
        "method": "enhanced_dialectical_reasoning_with_knowledge",
    }

    # Invoke dialectical hooks if any
    for hook in self.dialectical_hooks:
        hook(task, [result])

    return result


def _identify_relevant_knowledge(
    self: WSDETeam,
    task: dict[str, Any],
    solution: dict[str, Any],
    external_knowledge: dict[str, Any],
):
    """
    Identify knowledge relevant to a specific task and solution.

    Args:
        task: The task being worked on
        solution: The solution to analyze
        external_knowledge: External knowledge repository

    Returns:
        Dictionary containing relevant knowledge
    """
    relevant_knowledge = {
        "standards": [],
        "best_practices": [],
        "patterns": [],
        "domain_specific": {},
    }

    # Extract keywords from task and solution
    keywords = []

    # Extract from task description
    if "description" in task and isinstance(task["description"], str):
        keywords.extend(task["description"].lower().split())

    # Extract from task requirements
    if "requirements" in task:
        requirements = task["requirements"]
        if isinstance(requirements, list):
            for req in requirements:
                if isinstance(req, str):
                    keywords.extend(req.lower().split())
                elif isinstance(req, dict) and "description" in req:
                    keywords.extend(req["description"].lower().split())
        elif isinstance(requirements, str):
            keywords.extend(requirements.lower().split())

    # Extract from solution content
    if "content" in solution and isinstance(solution["content"], str):
        keywords.extend(solution["content"].lower().split())

    # Extract from solution code
    if "code" in solution and isinstance(solution["code"], str):
        # Extract meaningful code tokens (skip common syntax)
        code_tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", solution["code"])
        keywords.extend([token.lower() for token in code_tokens])

    # Remove duplicates and common words
    common_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "when",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "must",
        "can",
        "could",
        "to",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "can",
        "will",
        "just",
        "don",
        "should",
        "now",
    }
    keywords = [kw for kw in keywords if kw not in common_words and len(kw) > 2]

    # Find relevant standards
    if "standards" in external_knowledge:
        for standard in external_knowledge["standards"]:
            standard_name = standard.get("name", "").lower()
            standard_keywords = standard.get("keywords", [])

            # Check if standard is relevant to the task/solution
            if any(kw in standard_name for kw in keywords) or any(
                kw in keywords for kw in standard_keywords
            ):
                relevant_knowledge["standards"].append(standard)

    # Find relevant best practices
    if "best_practices" in external_knowledge:
        for practice in external_knowledge["best_practices"]:
            practice_name = practice.get("name", "").lower()
            practice_keywords = practice.get("keywords", [])

            # Check if practice is relevant to the task/solution
            if any(kw in practice_name for kw in keywords) or any(
                kw in keywords for kw in practice_keywords
            ):
                relevant_knowledge["best_practices"].append(practice)

    # Find relevant patterns
    if "patterns" in external_knowledge:
        for pattern in external_knowledge["patterns"]:
            pattern_name = pattern.get("name", "").lower()
            pattern_keywords = pattern.get("keywords", [])

            # Check if pattern is relevant to the task/solution
            if any(kw in pattern_name for kw in keywords) or any(
                kw in keywords for kw in pattern_keywords
            ):
                relevant_knowledge["patterns"].append(pattern)

    # Find relevant domain-specific knowledge
    if "domains" in external_knowledge:
        for domain, domain_knowledge in external_knowledge["domains"].items():
            domain_keywords = domain_knowledge.get("keywords", [])

            # Check if domain is relevant to the task/solution
            if any(kw in domain.lower() for kw in keywords) or any(
                kw in keywords for kw in domain_keywords
            ):
                relevant_knowledge["domain_specific"][domain] = domain_knowledge

    return relevant_knowledge


def _generate_enhanced_antithesis_with_knowledge(
    self: WSDETeam,
    thesis: dict[str, Any],
    critic_agent: Any,
    relevant_knowledge: dict[str, Any],
):
    """
    Generate an enhanced antithesis using relevant knowledge.

    Args:
        thesis: The thesis solution
        critic_agent: The agent that will generate the antithesis
        relevant_knowledge: Relevant knowledge for the task

    Returns:
        Dictionary containing the enhanced antithesis
    """
    # In a real implementation, this would call critic_agent.critique() with relevant_knowledge
    # For now, we'll generate a simulated antithesis

    antithesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "agent": critic_agent.name if hasattr(critic_agent, "name") else "critic",
        "critiques": [],
        "standard_violations": [],
        "best_practice_gaps": [],
        "pattern_suggestions": [],
        "domain_specific_critiques": {},
        "improvement_suggestions": [],
    }

    # Generate critiques based on standards
    for standard in relevant_knowledge.get("standards", []):
        standard_name = standard.get("name", "")
        standard_requirements = standard.get("requirements", [])

        for requirement in standard_requirements:
            # Check if the solution meets this requirement
            requirement_met = False

            if "content" in thesis and isinstance(thesis["content"], str):
                if requirement.lower() in thesis["content"].lower():
                    requirement_met = True

            if "code" in thesis and isinstance(thesis["code"], str):
                if requirement.lower() in thesis["code"].lower():
                    requirement_met = True

            if not requirement_met:
                antithesis["standard_violations"].append(
                    f"Violation of {standard_name}: {requirement}"
                )

    # Generate critiques based on best practices
    for practice in relevant_knowledge.get("best_practices", []):
        practice_name = practice.get("name", "")
        practice_description = practice.get("description", "")

        # Check if the solution follows this best practice
        practice_followed = False

        if "content" in thesis and isinstance(thesis["content"], str):
            if practice_name.lower() in thesis["content"].lower():
                practice_followed = True

        if "code" in thesis and isinstance(thesis["code"], str):
            if practice_name.lower() in thesis["code"].lower():
                practice_followed = True

        if not practice_followed:
            antithesis["best_practice_gaps"].append(
                f"Missing best practice: {practice_name} - {practice_description}"
            )

    # Generate pattern suggestions
    for pattern in relevant_knowledge.get("patterns", []):
        pattern_name = pattern.get("name", "")
        pattern_description = pattern.get("description", "")

        # Check if the solution uses this pattern
        pattern_used = False

        if "content" in thesis and isinstance(thesis["content"], str):
            if pattern_name.lower() in thesis["content"].lower():
                pattern_used = True

        if "code" in thesis and isinstance(thesis["code"], str):
            if pattern_name.lower() in thesis["code"].lower():
                pattern_used = True

        if not pattern_used:
            antithesis["pattern_suggestions"].append(
                f"Consider using {pattern_name} pattern: {pattern_description}"
            )

    # Generate domain-specific critiques
    for domain, domain_knowledge in relevant_knowledge.get(
        "domain_specific", {}
    ).items():
        domain_critiques = []

        if "principles" in domain_knowledge:
            for principle in domain_knowledge["principles"]:
                # Check if the solution follows this principle
                principle_followed = False

                if "content" in thesis and isinstance(thesis["content"], str):
                    if principle.lower() in thesis["content"].lower():
                        principle_followed = True

                if "code" in thesis and isinstance(thesis["code"], str):
                    if principle.lower() in thesis["code"].lower():
                        principle_followed = True

                if not principle_followed:
                    domain_critiques.append(
                        f"Does not follow {domain} principle: {principle}"
                    )

        if domain_critiques:
            antithesis["domain_specific_critiques"][domain] = domain_critiques

    # Generate general critiques
    if "content" in thesis:
        content = thesis["content"]

        # Simulate finding issues in the content
        if isinstance(content, str):
            # Check for common issues in text content
            if len(content) < 100:
                antithesis["critiques"].append("Content is too brief and lacks detail")

            if "example" not in content.lower():
                antithesis["critiques"].append(
                    "No examples provided to illustrate concepts"
                )

    if "code" in thesis:
        code = thesis["code"]

        # Simulate finding issues in the code
        if isinstance(code, str):
            # Check for common issues in code
            if "try" in code and "except" not in code:
                antithesis["critiques"].append(
                    "Try block without proper exception handling"
                )

            if "print(" in code:
                antithesis["critiques"].append(
                    "Using print statements instead of proper logging"
                )

    # Generate improvement suggestions
    # From standards
    for violation in antithesis["standard_violations"]:
        suggestion = "Implement " + violation.replace("Violation of ", "").replace(
            ":", " requirement:"
        )
        antithesis["improvement_suggestions"].append(suggestion)

    # From best practices
    for gap in antithesis["best_practice_gaps"]:
        suggestion = gap.replace("Missing best practice: ", "Adopt best practice: ")
        antithesis["improvement_suggestions"].append(suggestion)

    # From patterns
    for pattern_suggestion in antithesis["pattern_suggestions"]:
        antithesis["improvement_suggestions"].append(pattern_suggestion)

    # From domain-specific critiques
    for domain, critiques in antithesis["domain_specific_critiques"].items():
        for critique in critiques:
            suggestion = critique.replace("Does not follow", "Follow").replace(
                "principle:", "principle by incorporating"
            )
            antithesis["improvement_suggestions"].append(suggestion)

    # If no specific critiques were generated, add some generic ones
    if (
        not antithesis["critiques"]
        and not antithesis["standard_violations"]
        and not antithesis["best_practice_gaps"]
    ):
        antithesis["critiques"] = [
            "The solution lacks comprehensive error handling",
            "The approach could be more efficient",
            "The solution doesn't consider all edge cases",
        ]

        antithesis["improvement_suggestions"].extend(
            [
                "Add more robust error handling",
                "Optimize the approach for better efficiency",
                "Consider additional edge cases",
            ]
        )

    return antithesis


def _generate_enhanced_synthesis_with_standards(
    self: WSDETeam,
    thesis: dict[str, Any],
    antithesis: dict[str, Any],
    relevant_knowledge: dict[str, Any],
):
    """
    Generate an enhanced synthesis with standards compliance.

    Args:
        thesis: The thesis solution
        antithesis: The antithesis with critiques
        relevant_knowledge: Relevant knowledge for the task

    Returns:
        Dictionary containing the enhanced synthesis
    """
    synthesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "integrated_critiques": [],
        "addressed_standards": [],
        "implemented_practices": [],
        "applied_patterns": [],
        "domain_improvements": {},
        "rejected_critiques": [],
        "reasoning": "",
        "content": None,
        "code": None,
        "standards_compliance": {},
    }

    # Extract content and code from thesis
    original_content = thesis.get("content", "")
    original_code = thesis.get("code", "")

    # Initialize improved content and code
    improved_content = original_content
    improved_code = original_code

    # Process standard violations
    standard_violations = antithesis.get("standard_violations", [])
    for violation in standard_violations:
        # Extract standard name and requirement
        parts = violation.split(": ", 1)
        if len(parts) == 2:
            standard_name = parts[0].replace("Violation of ", "")
            requirement = parts[1]

            # Simulate addressing the standard
            if original_code:
                improved_code = (
                    f"# Addressed standard: {standard_name}\n# Requirement: {requirement}\n\n"
                    + improved_code
                )
            if original_content:
                improved_content = (
                    f"# Addressed standard: {standard_name}\n# Requirement: {requirement}\n\n"
                    + improved_content
                )

            synthesis["integrated_critiques"].append(violation)
            synthesis["addressed_standards"].append(standard_name)

    # Process best practice gaps
    best_practice_gaps = antithesis.get("best_practice_gaps", [])
    for gap in best_practice_gaps:
        # Extract practice name
        if "Missing best practice: " in gap:
            practice_info = gap.replace("Missing best practice: ", "")
            practice_name = (
                practice_info.split(" - ")[0]
                if " - " in practice_info
                else practice_info
            )

            # Simulate implementing the practice
            if original_code:
                improved_code = (
                    f"# Implemented best practice: {practice_name}\n\n" + improved_code
                )
            if original_content:
                improved_content = (
                    f"# Implemented best practice: {practice_name}\n\n"
                    + improved_content
                )

            synthesis["integrated_critiques"].append(gap)
            synthesis["implemented_practices"].append(practice_name)

    # Process pattern suggestions
    pattern_suggestions = antithesis.get("pattern_suggestions", [])
    for suggestion in pattern_suggestions:
        # Extract pattern name
        if "Consider using " in suggestion and " pattern: " in suggestion:
            pattern_name = suggestion.split("Consider using ")[1].split(" pattern: ")[0]

            # Simulate applying the pattern
            if original_code:
                improved_code = f"# Applied pattern: {pattern_name}\n\n" + improved_code
            if original_content:
                improved_content = (
                    f"# Applied pattern: {pattern_name}\n\n" + improved_content
                )

            synthesis["integrated_critiques"].append(suggestion)
            synthesis["applied_patterns"].append(pattern_name)

    # Process domain-specific critiques
    domain_critiques = antithesis.get("domain_specific_critiques", {})
    for domain, critiques in domain_critiques.items():
        domain_improvements = []

        for critique in critiques:
            # Simulate addressing the domain-specific critique
            if "principle: " in critique:
                principle = critique.split("principle: ")[1]

                if original_code:
                    improved_code = (
                        f"# Addressed {domain} principle: {principle}\n\n"
                        + improved_code
                    )
                if original_content:
                    improved_content = (
                        f"# Addressed {domain} principle: {principle}\n\n"
                        + improved_content
                    )

                synthesis["integrated_critiques"].append(critique)
                domain_improvements.append(
                    f"Implemented {domain} principle: {principle}"
                )

        if domain_improvements:
            synthesis["domain_improvements"][domain] = domain_improvements

    # Process general critiques
    critiques = antithesis.get("critiques", [])
    for critique in critiques:
        # Process content-related critiques
        if (
            "content" in critique.lower()
            or "brief" in critique.lower()
            or "detail" in critique.lower()
            or "example" in critique.lower()
        ):
            if original_content:
                # Simulate improving content
                improved_content = (
                    f"# Addressed critique: {critique}\n\n" + improved_content
                )
                synthesis["integrated_critiques"].append(critique)

        # Process code-related critiques
        elif (
            "code" in critique.lower()
            or "error handling" in critique.lower()
            or "exception" in critique.lower()
            or "logging" in critique.lower()
        ):
            if original_code:
                # Simulate improving code
                improved_code = f"# Addressed critique: {critique}\n\n" + improved_code
                synthesis["integrated_critiques"].append(critique)

    # Set improved content and code
    if improved_content != original_content:
        synthesis["content"] = improved_content

    if improved_code != original_code:
        synthesis["code"] = improved_code

    # Check standards compliance
    standards_compliance = {}

    # Check each standard
    for standard in relevant_knowledge.get("standards", []):
        standard_name = standard.get("name", "")
        standard_requirements = standard.get("requirements", [])

        # Count how many requirements are met
        met_requirements = 0
        total_requirements = len(standard_requirements)

        for requirement in standard_requirements:
            # Check if the improved solution meets this requirement
            requirement_met = False

            if (
                synthesis.get("content")
                and requirement.lower() in synthesis["content"].lower()
            ):
                requirement_met = True

            if (
                synthesis.get("code")
                and requirement.lower() in synthesis["code"].lower()
            ):
                requirement_met = True

            # Also check if we explicitly addressed this standard
            if standard_name in synthesis["addressed_standards"]:
                requirement_met = True

            if requirement_met:
                met_requirements += 1

        # Calculate compliance percentage
        compliance_percentage = (met_requirements / max(1, total_requirements)) * 100

        # Determine compliance level
        if compliance_percentage >= 90:
            compliance_level = "high"
        elif compliance_percentage >= 70:
            compliance_level = "medium"
        else:
            compliance_level = "low"

        standards_compliance[standard_name] = {
            "compliance_level": compliance_level,
            "compliance_percentage": round(compliance_percentage, 1),
            "met_requirements": met_requirements,
            "total_requirements": total_requirements,
        }

    synthesis["standards_compliance"] = standards_compliance

    # Identify critiques that weren't integrated
    all_critiques = (
        critiques + standard_violations + best_practice_gaps + pattern_suggestions
    )

    for domain_critiques_list in domain_critiques.values():
        all_critiques.extend(domain_critiques_list)

    all_integrated = set(synthesis["integrated_critiques"])
    synthesis["rejected_critiques"] = [
        c for c in all_critiques if c not in all_integrated
    ]

    # Generate reasoning
    reasoning_parts = []

    # Summarize integrated critiques
    if synthesis["integrated_critiques"]:
        reasoning_parts.append("## Integrated Critiques")
        for critique in synthesis["integrated_critiques"]:
            reasoning_parts.append(f"- {critique}")

    # Summarize standards compliance
    if synthesis["standards_compliance"]:
        reasoning_parts.append("\n## Standards Compliance")
        for standard, compliance in synthesis["standards_compliance"].items():
            reasoning_parts.append(
                f"- {standard}: {compliance['compliance_level'].capitalize()} ({compliance['compliance_percentage']}%)"
            )
            reasoning_parts.append(
                f"  - Met {compliance['met_requirements']} of {compliance['total_requirements']} requirements"
            )

    # Summarize implemented practices
    if synthesis["implemented_practices"]:
        reasoning_parts.append("\n## Implemented Best Practices")
        for practice in synthesis["implemented_practices"]:
            reasoning_parts.append(f"- {practice}")

    # Summarize applied patterns
    if synthesis["applied_patterns"]:
        reasoning_parts.append("\n## Applied Patterns")
        for pattern in synthesis["applied_patterns"]:
            reasoning_parts.append(f"- {pattern}")

    # Summarize domain improvements
    if synthesis["domain_improvements"]:
        reasoning_parts.append("\n## Domain-Specific Improvements")
        for domain, improvements in synthesis["domain_improvements"].items():
            reasoning_parts.append(f"\n### {domain.replace('_', ' ').title()}")
            for improvement in improvements:
                reasoning_parts.append(f"- {improvement}")

    # Combine all parts
    synthesis["reasoning"] = "\n".join(reasoning_parts)

    return synthesis


def _generate_evaluation_with_compliance(
    self: WSDETeam,
    synthesis: dict[str, Any],
    antithesis: dict[str, Any],
    task: dict[str, Any],
    relevant_knowledge: dict[str, Any],
):
    """
    Generate an evaluation with compliance assessment.

    Args:
        synthesis: The synthesis solution
        antithesis: The antithesis with critiques
        task: The original task
        relevant_knowledge: Relevant knowledge for the task

    Returns:
        Dictionary containing the evaluation with compliance assessment
    """
    evaluation = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "strengths": [],
        "weaknesses": [],
        "standards_assessment": {},
        "best_practices_assessment": {},
        "domain_specific_assessment": {},
        "overall_quality_score": 0.0,
        "overall_assessment": "",
    }

    # Evaluate standards compliance
    standards_compliance = synthesis.get("standards_compliance", {})
    overall_standards_score = 0.0
    standards_count = 0

    for standard, compliance in standards_compliance.items():
        compliance_level = compliance.get("compliance_level", "low")
        compliance_percentage = compliance.get("compliance_percentage", 0.0)

        # Convert compliance level to score
        if compliance_level == "high":
            score = 1.0
        elif compliance_level == "medium":
            score = 0.7
        else:  # low
            score = 0.3

        # Add to overall score
        overall_standards_score += score
        standards_count += 1

        # Add assessment
        evaluation["standards_assessment"][standard] = {
            "score": score,
            "compliance_level": compliance_level,
            "compliance_percentage": compliance_percentage,
        }

        # Add strength or weakness based on compliance
        if compliance_level == "high":
            evaluation["strengths"].append(
                f"High compliance with {standard} standard ({compliance_percentage}%)"
            )
        elif compliance_level == "medium":
            evaluation["strengths"].append(
                f"Moderate compliance with {standard} standard ({compliance_percentage}%)"
            )
        else:
            evaluation["weaknesses"].append(
                f"Low compliance with {standard} standard ({compliance_percentage}%)"
            )

    # Calculate average standards score
    average_standards_score = overall_standards_score / max(1, standards_count)

    # Evaluate best practices implementation
    implemented_practices = synthesis.get("implemented_practices", [])
    all_practices = relevant_knowledge.get("best_practices", [])
    all_practice_names = [practice.get("name", "") for practice in all_practices]

    # Calculate best practices score
    best_practices_score = len(implemented_practices) / max(1, len(all_practice_names))

    # Add assessment
    evaluation["best_practices_assessment"] = {
        "score": best_practices_score,
        "implemented_count": len(implemented_practices),
        "total_count": len(all_practice_names),
        "implementation_percentage": round(best_practices_score * 100, 1),
    }

    # Add strength or weakness based on implementation
    if best_practices_score >= 0.8:
        evaluation["strengths"].append(
            f"Excellent implementation of best practices ({round(best_practices_score * 100, 1)}%)"
        )
    elif best_practices_score >= 0.5:
        evaluation["strengths"].append(
            f"Good implementation of best practices ({round(best_practices_score * 100, 1)}%)"
        )
    else:
        evaluation["weaknesses"].append(
            f"Limited implementation of best practices ({round(best_practices_score * 100, 1)}%)"
        )

    # Evaluate domain-specific improvements
    domain_improvements = synthesis.get("domain_improvements", {})
    domain_specific_score = 0.0
    domain_count = 0

    for domain, improvements in domain_improvements.items():
        # Calculate domain score based on number of improvements
        domain_score = min(
            1.0, len(improvements) / 3.0
        )  # Cap at 1.0, 3 improvements = perfect score

        # Add to overall score
        domain_specific_score += domain_score
        domain_count += 1

        # Add assessment
        evaluation["domain_specific_assessment"][domain] = {
            "score": domain_score,
            "improvements_count": len(improvements),
            "quality_level": (
                "high"
                if domain_score >= 0.8
                else "medium" if domain_score >= 0.5 else "low"
            ),
        }

        # Add strength or weakness based on score
        if domain_score >= 0.8:
            evaluation["strengths"].append(
                f"Excellent {domain.replace('_', ' ')} improvements"
            )
        elif domain_score >= 0.5:
            evaluation["strengths"].append(
                f"Good {domain.replace('_', ' ')} improvements"
            )
        else:
            evaluation["weaknesses"].append(
                f"Limited {domain.replace('_', ' ')} improvements"
            )

    # Calculate average domain score
    average_domain_score = domain_specific_score / max(1, domain_count)

    # Calculate overall quality score (weighted average)
    standards_weight = 0.4
    practices_weight = 0.3
    domain_weight = 0.3

    overall_quality_score = (
        average_standards_score * standards_weight
        + best_practices_score * practices_weight
        + average_domain_score * domain_weight
    )

    evaluation["overall_quality_score"] = round(overall_quality_score, 2)

    # Generate overall assessment
    if overall_quality_score >= 0.8:
        assessment = "Excellent solution that effectively addresses standards, best practices, and domain-specific considerations."
    elif overall_quality_score >= 0.6:
        assessment = "Good solution that addresses most standards and best practices, with some room for improvement in domain-specific areas."
    elif overall_quality_score >= 0.4:
        assessment = "Adequate solution that addresses some standards and best practices, but has significant room for improvement."
    else:
        assessment = "Limited solution that fails to adequately address standards, best practices, and domain-specific considerations."

    evaluation["overall_assessment"] = (
        f"{assessment} (Quality Score: {overall_quality_score:.2f})"
    )

    return evaluation
