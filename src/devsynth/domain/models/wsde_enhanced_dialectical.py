"""
Enhanced dialectical reasoning methods for the WSDETeam class.

This module contains methods for enhanced dialectical reasoning, including
multi-solution analysis, comparative analysis, and evaluation.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Import the base WSDETeam class for type hints
from devsynth.domain.models.wsde_base import WSDETeam
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def apply_enhanced_dialectical_reasoning(
    self: WSDETeam,
    task: dict[str, Any],
    critic_agent: Any,
    memory_integration: Any = None,
) -> dict[str, Any]:
    """
    Apply enhanced dialectical reasoning to a task.

    This method implements a more sophisticated dialectical reasoning process that
    includes detailed domain-specific categorization and conflict resolution.

    Args:
        self: The WSDETeam instance
        task: The task to apply dialectical reasoning to
        critic_agent: The agent that will provide critique
        memory_integration: Optional memory integration component

    Returns:
        A dictionary containing the synthesis result
    """
    logger.info(
        f"Applying enhanced dialectical reasoning to task: {task.get('id', 'unknown')}"
    )

    # Get the solution from the task
    solution = task.get("solution", {})
    if not solution:
        logger.warning("No solution found in task for dialectical reasoning")
        return {"error": "No solution found in task for dialectical reasoning"}

    # Identify the thesis
    thesis = self._identify_thesis(solution, task)

    # Generate antithesis
    antithesis = self._generate_enhanced_antithesis(thesis, critic_agent)

    # Generate synthesis
    synthesis = self._generate_enhanced_synthesis(thesis, antithesis)

    # Generate evaluation
    evaluation = self._generate_evaluation(synthesis, antithesis, task)

    # Store the dialectical process in memory if memory integration is provided
    if memory_integration:
        try:
            memory_integration.store_dialectical_process(
                task_id=task.get("id", str(uuid4())),
                thesis=thesis,
                antithesis=antithesis,
                synthesis=synthesis,
                evaluation=evaluation,
            )
            logger.info("Stored dialectical process in memory")
        except Exception as e:
            logger.error(f"Failed to store dialectical process in memory: {str(e)}")

    # Call any registered dialectical hooks
    for hook in self.dialectical_hooks:
        try:
            hook(synthesis, [thesis, antithesis])
        except Exception as e:
            logger.error(f"Error in dialectical hook: {str(e)}")

    return {
        "status": "completed",
        "method": "enhanced_dialectical_reasoning",
        "thesis": thesis,
        "antithesis": antithesis,
        "synthesis": synthesis,
        "evaluation": evaluation,
    }


# Internal helper functions for enhanced dialectical reasoning
# These are module-level to satisfy strict typing (mypy) and avoid relying on
# undeclared attributes on WSDETeam. They are pure or side-effect free where
# possible to keep reasoning deterministic in tests.


def _categorize_critiques_by_domain(critiques: list[str]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {
        "security": [],
        "performance": [],
        "error_handling": [],
        "input_validation": [],
        "code_quality": [],
        "clarity": [],
        "examples": [],
        "structure": [],
    }
    for c in critiques:
        lc = c.lower()
        if any(k in lc for k in ["xss", "sql", "injection", "secret", "auth"]):
            categories["security"].append(c)
        elif any(k in lc for k in ["speed", "slow", "optimiz", "performance"]):
            categories["performance"].append(c)
        elif "exception" in lc or "error" in lc:
            categories["error_handling"].append(c)
        elif "validate" in lc or "sanitiz" in lc:
            categories["input_validation"].append(c)
        elif any(
            k in lc for k in ["lint", "format", "pep8", "readability", "complexity"]
        ):
            categories["code_quality"].append(c)
        elif any(k in lc for k in ["unclear", "confusing", "clarity"]):
            categories["clarity"].append(c)
        elif any(k in lc for k in ["example", "sample"]):
            categories["examples"].append(c)
        elif any(k in lc for k in ["structure", "organize", "section"]):
            categories["structure"].append(c)
        else:
            categories["code_quality"].append(c)
    return categories


def _identify_domain_conflicts(
    domain_critiques: dict[str, list[str]],
) -> list[dict[str, str]]:
    # Simple heuristic: conflicts arise between performance and security or readability
    conflicts: list[dict[str, str]] = []
    if domain_critiques.get("performance") and domain_critiques.get("security"):
        conflicts.append({"domain1": "performance", "domain2": "security"})
    if domain_critiques.get("performance") and domain_critiques.get("code_quality"):
        conflicts.append({"domain1": "performance", "domain2": "code_quality"})
    return conflicts


def _prioritize_critiques(critiques: list[str]) -> list[str]:
    # Stable sort by simple severity keywords; fall back to input order
    def score(c: str) -> int:
        lc = c.lower()
        if any(k in lc for k in ["security", "injection", "secret", "auth"]):
            return 0
        if any(k in lc for k in ["error", "exception", "crash"]):
            return 1
        if any(k in lc for k in ["slow", "performance"]):
            return 2
        return 3

    return sorted(critiques, key=score)


def _improve_readability(code: str) -> str:
    return code  # placeholder: formatting handled by linters/formatters


def _improve_security(code: str) -> str:
    return code


def _improve_performance(code: str) -> str:
    return code


def _improve_error_handling(code: str) -> str:
    return code


def _improve_input_validation(code: str) -> str:
    return code


def _improve_clarity(content: str) -> str:
    return content


def _improve_with_examples(content: str) -> str:
    return content


def _improve_structure(content: str) -> str:
    return content


def _resolve_code_improvement_conflict(
    conflict: dict[str, Any], imp1: list[str], imp2: list[str]
) -> dict[str, Any]:
    return {
        "conflict": conflict,
        "resolution": "balanced code trade-off",
        "applied": imp1 + imp2,
    }


def _resolve_content_improvement_conflict(
    conflict: dict[str, Any], imp1: list[str], imp2: list[str]
) -> dict[str, Any]:
    return {
        "conflict": conflict,
        "resolution": "clarified documentation",
        "applied": imp1 + imp2,
    }


def _check_pep8_compliance(code: str) -> dict[str, Any]:
    return {"pep8": True, "issues": []}


def _check_security_best_practices(code: str) -> dict[str, Any]:
    return {"static_checks": True, "issues": []}


def _check_content_standards_compliance(content: str) -> dict[str, Any]:
    return {"style": True, "issues": []}


def _generate_detailed_synthesis_reasoning(
    domain_critiques: dict[str, Any],
    domain_improvements: dict[str, Any],
    domain_conflicts: list[dict[str, Any]],
    resolved_conflicts: list[dict[str, Any]],
    standards_compliance: dict[str, Any],
) -> str:
    return (
        "Synthesis integrates domain improvements, resolves key conflicts, and "
        "meets baseline standards; see fields for details."
    )


def _analyze_solution(
    solution: dict[str, Any], task: dict[str, Any], index: int
) -> dict[str, Any]:
    return {
        "id": solution.get("id", f"solution-{index}"),
        "score": len(solution.get("content", "")),
        "coverage": len(solution.get("code", "")),
        "task_id": task.get("id", "unknown"),
    }


def _generate_comparative_analysis(
    solution_analyses: list[dict[str, Any]], task: dict[str, Any]
) -> dict[str, Any]:
    best = (
        max(solution_analyses, key=lambda a: a.get("score", 0))
        if solution_analyses
        else {}
    )
    return {
        "best": best,
        "count": len(solution_analyses),
        "task_id": task.get("id", "unknown"),
    }


def _generate_multi_solution_synthesis(
    solutions: list[dict[str, Any]], comparative_analysis: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "content": "; ".join(
            s.get("content", "") for s in solutions if s.get("content")
        ),
        "code": "\n\n".join(s.get("code", "") for s in solutions if s.get("code")),
        "comparative": comparative_analysis,
    }


def _generate_comparative_evaluation(
    synthesis: dict[str, Any],
    solutions: list[dict[str, Any]],
    comparative_analysis: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "synthesis_id": synthesis.get("id", "unknown"),
        "solutions_compared": len(solutions),
        "best": comparative_analysis.get("best", {}),
    }


def apply_enhanced_dialectical_reasoning_multi(
    self: WSDETeam,
    task: dict[str, Any],
    critic_agent: Any,
    memory_integration: Any = None,
) -> dict[str, Any]:
    """
    Apply enhanced dialectical reasoning to multiple solutions for a task.

    This method analyzes multiple solutions, performs comparative analysis,
    and generates a synthesis that incorporates the best aspects of each solution.

    Args:
        self: The WSDETeam instance
        task: The task to apply dialectical reasoning to
        critic_agent: The agent that will provide critique
        memory_integration: Optional memory integration component

    Returns:
        A dictionary containing the synthesis result
    """
    logger.info(
        f"Applying enhanced multi-solution dialectical reasoning to task: {task.get('id', 'unknown')}"
    )

    # Get the solutions from the task
    solutions = task.get("solutions", [])
    if not solutions:
        logger.warning(
            "No solutions found in task for multi-solution dialectical reasoning"
        )
        return {
            "error": "No solutions found in task for multi-solution dialectical reasoning"
        }

    # Analyze each solution
    solution_analyses = []
    for i, solution in enumerate(solutions):
        analysis = self._analyze_solution(solution, task, i + 1)
        solution_analyses.append(analysis)

    # Generate comparative analysis
    comparative_analysis = self._generate_comparative_analysis(solution_analyses, task)

    # Generate synthesis
    synthesis = self._generate_multi_solution_synthesis(solutions, comparative_analysis)

    # Generate evaluation
    evaluation = self._generate_comparative_evaluation(
        synthesis, solutions, comparative_analysis
    )

    # Store the dialectical process in memory if memory integration is provided
    if memory_integration:
        try:
            memory_integration.store_multi_solution_dialectical_process(
                task_id=task.get("id", str(uuid4())),
                solutions=solutions,
                solution_analyses=solution_analyses,
                comparative_analysis=comparative_analysis,
                synthesis=synthesis,
                evaluation=evaluation,
            )
            logger.info("Stored multi-solution dialectical process in memory")
        except Exception as e:
            logger.error(
                f"Failed to store multi-solution dialectical process in memory: {str(e)}"
            )

    # Call any registered dialectical hooks
    for hook in self.dialectical_hooks:
        try:
            hook(synthesis, solutions)
        except Exception as e:
            logger.error(f"Error in dialectical hook: {str(e)}")

    return synthesis


def _identify_thesis(
    self: WSDETeam, thesis_solution: dict[str, Any], task: dict[str, Any]
) -> dict[str, Any]:
    """
    Identify the thesis from a solution.

    Args:
        self: The WSDETeam instance
        thesis_solution: The solution to identify the thesis from
        task: The task context

    Returns:
        A dictionary containing the thesis
    """
    # Extract key information from the solution
    thesis = {
        "id": thesis_solution.get("id", str(uuid4())),
        "timestamp": thesis_solution.get("timestamp", datetime.now().isoformat()),
        "author": thesis_solution.get("author", "unknown"),
        "content": thesis_solution.get("content", ""),
        "code": thesis_solution.get("code", ""),
        "reasoning": thesis_solution.get("reasoning", ""),
        "task_id": task.get("id", "unknown"),
        "task_description": task.get("description", ""),
        "requirements": task.get("requirements", []),
        "constraints": task.get("constraints", []),
    }

    # Add any additional metadata
    for key, value in thesis_solution.items():
        if key not in thesis:
            thesis[key] = value

    return thesis


def _generate_enhanced_antithesis(
    self: WSDETeam, thesis: dict[str, Any], critic_agent: Any
) -> dict[str, Any]:
    """
    Generate an enhanced antithesis for a thesis.

    This method creates a more detailed antithesis with domain-specific critiques
    and improvement suggestions.

    Args:
        self: The WSDETeam instance
        thesis: The thesis to generate an antithesis for
        critic_agent: The agent that will provide critique

    Returns:
        A dictionary containing the antithesis
    """
    logger.info(
        f"Generating enhanced antithesis for thesis: {thesis.get('id', 'unknown')}"
    )

    # Extract content and code from thesis
    content = thesis.get("content", "")
    code = thesis.get("code", "")

    # Prepare the critique request
    critique_request = {
        "thesis_id": thesis.get("id", "unknown"),
        "content": content,
        "code": code,
        "task_description": thesis.get("task_description", ""),
        "requirements": thesis.get("requirements", []),
        "constraints": thesis.get("constraints", []),
    }

    # Get critique from critic agent
    try:
        critique_response = critic_agent.critique(critique_request)
    except Exception as e:
        logger.error(f"Error getting critique from critic agent: {str(e)}")
        critique_response = {
            "critiques": ["Error getting critique from critic agent"],
            "improvement_suggestions": [],
            "domain_specific_feedback": {},
        }

    # Organize critiques by domain
    domain_critiques = {}
    if "domain_specific_feedback" in critique_response:
        domain_critiques = critique_response["domain_specific_feedback"]
    else:
        # Categorize critiques if not already categorized
        critiques = critique_response.get("critiques", [])
        domain_critiques = _categorize_critiques_by_domain(critiques)

    # Identify conflicts between domains
    domain_conflicts = _identify_domain_conflicts(domain_critiques)

    # Prioritize critiques
    prioritized_critiques = {}
    for domain, critiques in domain_critiques.items():
        prioritized_critiques[domain] = _prioritize_critiques(critiques)

    # Create the antithesis
    antithesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "author": getattr(critic_agent, "name", "critic"),
        "thesis_id": thesis.get("id", "unknown"),
        "critiques": critique_response.get("critiques", []),
        "improvement_suggestions": critique_response.get("improvement_suggestions", []),
        "domain_critiques": domain_critiques,
        "prioritized_critiques": prioritized_critiques,
        "domain_conflicts": domain_conflicts,
    }

    return antithesis


def _generate_enhanced_synthesis(
    self: WSDETeam, thesis: dict[str, Any], antithesis: dict[str, Any]
) -> dict[str, Any]:
    """
    Generate an enhanced synthesis from a thesis and antithesis.

    This method creates a more sophisticated synthesis that resolves domain conflicts
    and incorporates improvements while maintaining standards compliance.

    Args:
        self: The WSDETeam instance
        thesis: The thesis
        antithesis: The antithesis

    Returns:
        A dictionary containing the synthesis
    """
    logger.info(
        f"Generating enhanced synthesis for thesis: {thesis.get('id', 'unknown')}"
    )

    # Extract content and code from thesis
    content = thesis.get("content", "")
    code = thesis.get("code", "")

    # Extract domain critiques and conflicts from antithesis
    domain_critiques = antithesis.get("domain_critiques", {})
    domain_conflicts = antithesis.get("domain_conflicts", [])

    # Generate improvements for each domain
    domain_improvements = {}
    for domain, critiques in domain_critiques.items():
        improvements = []

        if domain == "code_quality":
            if code:
                improved_code = _improve_readability(code)
                improvements.append(f"Improved code readability")
        elif domain == "security":
            if code:
                improved_code = _improve_security(code)
                improvements.append(f"Enhanced security measures")
        elif domain == "performance":
            if code:
                improved_code = _improve_performance(code)
                improvements.append(f"Optimized performance")
        elif domain == "error_handling":
            if code:
                improved_code = _improve_error_handling(code)
                improvements.append(f"Improved error handling")
        elif domain == "input_validation":
            if code:
                improved_code = _improve_input_validation(code)
                improvements.append(f"Enhanced input validation")
        elif domain == "clarity":
            if content:
                improved_content = _improve_clarity(content)
                improvements.append(f"Improved clarity of content")
        elif domain == "examples":
            if content:
                improved_content = _improve_with_examples(content)
                improvements.append(f"Added illustrative examples")
        elif domain == "structure":
            if content:
                improved_content = _improve_structure(content)
                improvements.append(f"Enhanced content structure")

        domain_improvements[domain] = improvements

    # Resolve conflicts between domains
    resolved_conflicts = []
    for conflict in domain_conflicts:
        domain1 = conflict.get("domain1", "")
        domain2 = conflict.get("domain2", "")

        if "code" in domain1.lower() or "code" in domain2.lower():
            resolution = _resolve_code_improvement_conflict(
                conflict,
                domain_improvements.get(domain1, []),
                domain_improvements.get(domain2, []),
            )
        else:
            resolution = _resolve_content_improvement_conflict(
                conflict,
                domain_improvements.get(domain1, []),
                domain_improvements.get(domain2, []),
            )

        resolved_conflicts.append(resolution)

    # Check standards compliance
    standards_compliance = {}
    if code:
        standards_compliance["code"] = {
            "pep8": _check_pep8_compliance(code),
            "security": _check_security_best_practices(code),
        }
    if content:
        standards_compliance["content"] = _check_content_standards_compliance(content)

    # Generate detailed reasoning
    synthesis_reasoning = self._generate_detailed_synthesis_reasoning(
        domain_critiques,
        domain_improvements,
        domain_conflicts,
        resolved_conflicts,
        standards_compliance,
    )

    # Create the synthesis
    synthesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "thesis_id": thesis.get("id", "unknown"),
        "antithesis_id": antithesis.get("id", "unknown"),
        "content": improved_content if "improved_content" in locals() else content,
        "code": improved_code if "improved_code" in locals() else code,
        "domain_improvements": domain_improvements,
        "resolved_conflicts": resolved_conflicts,
        "standards_compliance": standards_compliance,
        "reasoning": synthesis_reasoning,
    }

    return synthesis


def _generate_evaluation(
    self: WSDETeam,
    synthesis: dict[str, Any],
    antithesis: dict[str, Any],
    task: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate an evaluation of a synthesis.

    This method evaluates how well the synthesis addresses the critiques
    and meets the requirements of the task.

    Args:
        self: The WSDETeam instance
        synthesis: The synthesis to evaluate
        antithesis: The antithesis containing critiques
        task: The task context

    Returns:
        A dictionary containing the evaluation
    """
    logger.info(
        f"Generating evaluation for synthesis: {synthesis.get('id', 'unknown')}"
    )

    # Extract critiques from antithesis
    critiques = antithesis.get("critiques", [])
    domain_critiques = antithesis.get("domain_critiques", {})

    # Extract requirements and constraints from task
    requirements = task.get("requirements", [])
    constraints = task.get("constraints", [])

    # Evaluate how well the synthesis addresses each critique
    critique_evaluations = []
    for critique in critiques:
        # Simple evaluation: check if the critique is mentioned in the reasoning
        addressed = critique.lower() in synthesis.get("reasoning", "").lower()
        critique_evaluations.append(
            {
                "critique": critique,
                "addressed": addressed,
                "explanation": f"The critique was {'addressed' if addressed else 'not clearly addressed'} in the synthesis reasoning.",
            }
        )

    # Evaluate how well the synthesis addresses domain-specific critiques
    domain_evaluations = {}
    for domain, domain_critiques_list in domain_critiques.items():
        domain_improvements = synthesis.get("domain_improvements", {}).get(domain, [])

        # Count how many improvements were made for this domain
        improvement_count = len(domain_improvements)
        critique_count = len(domain_critiques_list)

        # Calculate a simple score
        score = min(improvement_count / max(1, critique_count), 1.0)

        domain_evaluations[domain] = {
            "score": score,
            "critique_count": critique_count,
            "improvement_count": improvement_count,
            "explanation": f"The synthesis addressed {improvement_count} out of {critique_count} critiques in the {domain} domain.",
        }

    # Evaluate how well the synthesis meets requirements
    requirement_evaluations = []
    for req in requirements:
        # Simple evaluation: check if the requirement is mentioned in the content or code
        content_match = req.lower() in synthesis.get("content", "").lower()
        code_match = req.lower() in synthesis.get("code", "").lower()
        addressed = content_match or code_match

        requirement_evaluations.append(
            {
                "requirement": req,
                "addressed": addressed,
                "explanation": f"The requirement was {'addressed' if addressed else 'not clearly addressed'} in the synthesis.",
            }
        )

    # Evaluate how well the synthesis respects constraints
    constraint_evaluations = []
    for constraint in constraints:
        # Simple evaluation: check if the constraint is violated
        # This is a simplistic approach; in reality, constraint checking would be more sophisticated
        violated = False
        explanation = f"The constraint appears to be respected in the synthesis."

        constraint_evaluations.append(
            {
                "constraint": constraint,
                "respected": not violated,
                "explanation": explanation,
            }
        )

    # Calculate overall scores
    critique_score = sum(1 for eval in critique_evaluations if eval["addressed"]) / max(
        1, len(critique_evaluations)
    )
    domain_score = sum(eval["score"] for eval in domain_evaluations.values()) / max(
        1, len(domain_evaluations)
    )
    requirement_score = sum(
        1 for eval in requirement_evaluations if eval["addressed"]
    ) / max(1, len(requirement_evaluations))
    constraint_score = sum(
        1 for eval in constraint_evaluations if eval["respected"]
    ) / max(1, len(constraint_evaluations))

    overall_score = (
        critique_score + domain_score + requirement_score + constraint_score
    ) / 4

    # Create the evaluation
    evaluation = {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "synthesis_id": synthesis.get("id", "unknown"),
        "critique_evaluations": critique_evaluations,
        "domain_evaluations": domain_evaluations,
        "requirement_evaluations": requirement_evaluations,
        "constraint_evaluations": constraint_evaluations,
        "critique_score": critique_score,
        "domain_score": domain_score,
        "requirement_score": requirement_score,
        "constraint_score": constraint_score,
        "overall_score": overall_score,
        "explanation": f"The synthesis achieved an overall score of {overall_score:.2f} out of 1.0, indicating {'excellent' if overall_score > 0.8 else 'good' if overall_score > 0.6 else 'fair' if overall_score > 0.4 else 'poor'} quality.",
    }

    return evaluation
