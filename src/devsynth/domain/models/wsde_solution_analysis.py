"""
Solution analysis methods for the WSDETeam class.

This module contains methods for analyzing solutions, generating comparative analyses,
and evaluating solutions.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Import the base WSDETeam class for type hints
from devsynth.domain.models.wsde_base import WSDETeam
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def _analyze_solution(
    self: WSDETeam, solution: dict[str, Any], task: dict[str, Any], solution_number: int
) -> dict[str, Any]:
    """
    Analyze a solution for a task.

    This method performs a detailed analysis of a solution, identifying its strengths,
    weaknesses, and how well it addresses the task requirements.

    Args:
        self: The WSDETeam instance
        solution: The solution to analyze
        task: The task context
        solution_number: The number of the solution in the list of solutions

    Returns:
        A dictionary containing the analysis
    """
    logger.info(
        f"Analyzing solution {solution_number} for task: {task.get('id', 'unknown')}"
    )

    # Extract content and code from solution
    content = solution.get("content", "")
    code = solution.get("code", "")

    # Extract requirements and constraints from task
    requirements = task.get("requirements", [])
    constraints = task.get("constraints", [])

    # Analyze how well the solution addresses each requirement
    requirement_analyses = []
    for req in requirements:
        # Simple analysis: check if the requirement is mentioned in the content or code
        content_match = req.lower() in content.lower()
        code_match = req.lower() in code.lower()
        addressed = content_match or code_match

        requirement_analyses.append(
            {
                "requirement": req,
                "addressed": addressed,
                "explanation": f"The requirement is {'addressed' if addressed else 'not clearly addressed'} in the solution.",
            }
        )

    # Analyze how well the solution respects each constraint
    constraint_analyses = []
    for constraint in constraints:
        # Simple analysis: check if the constraint is mentioned in the content or code
        content_match = constraint.lower() in content.lower()
        code_match = constraint.lower() in code.lower()
        addressed = content_match or code_match

        constraint_analyses.append(
            {
                "constraint": constraint,
                "respected": addressed,
                "explanation": f"The constraint is {'respected' if addressed else 'not clearly addressed'} in the solution.",
            }
        )

    # Identify strengths of the solution
    strengths = []

    # Check for comprehensive content
    if len(content) > 500:
        strengths.append("Comprehensive explanation")

    # Check for code implementation
    if code:
        strengths.append("Includes code implementation")

    # Check for addressing most requirements
    requirements_addressed = sum(
        1 for analysis in requirement_analyses if analysis["addressed"]
    )
    if requirements_addressed > 0.7 * len(requirements):
        strengths.append(
            f"Addresses {requirements_addressed} out of {len(requirements)} requirements"
        )

    # Identify weaknesses of the solution
    weaknesses = []

    # Check for missing content
    if len(content) < 100:
        weaknesses.append("Limited explanation")

    # Check for missing code
    if not code:
        weaknesses.append("No code implementation")

    # Check for unaddressed requirements
    requirements_unaddressed = len(requirements) - requirements_addressed
    if requirements_unaddressed > 0.3 * len(requirements):
        weaknesses.append(
            f"Does not address {requirements_unaddressed} out of {len(requirements)} requirements"
        )

    # Create the analysis
    analysis = {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "solution_id": solution.get("id", "unknown"),
        "solution_number": solution_number,
        "requirement_analyses": requirement_analyses,
        "constraint_analyses": constraint_analyses,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "requirements_addressed": requirements_addressed,
        "requirements_total": len(requirements),
        "constraints_respected": sum(
            1 for analysis in constraint_analyses if analysis["respected"]
        ),
        "constraints_total": len(constraints),
    }

    return analysis


def _generate_comparative_analysis(
    self: WSDETeam, solution_analyses: list[dict[str, Any]], task: dict[str, Any]
) -> dict[str, Any]:
    """
    Generate a comparative analysis of multiple solutions.

    This method compares multiple solutions and identifies their relative strengths
    and weaknesses.

    Args:
        self: The WSDETeam instance
        solution_analyses: The analyses of the solutions to compare
        task: The task context

    Returns:
        A dictionary containing the comparative analysis
    """
    logger.info(
        f"Generating comparative analysis for task: {task.get('id', 'unknown')}"
    )

    # Extract requirements and constraints from task
    requirements = task.get("requirements", [])
    constraints = task.get("constraints", [])

    # Compare how well each solution addresses each requirement
    requirement_comparisons = {}
    for req in requirements:
        req_comparison = {
            "requirement": req,
            "solution_scores": {},
            "best_solution": None,
            "explanation": "",
        }

        # Find which solutions address this requirement
        for analysis in solution_analyses:
            solution_number = analysis["solution_number"]
            req_analyses = analysis["requirement_analyses"]

            # Find the analysis for this requirement
            req_analysis = next(
                (r for r in req_analyses if r["requirement"] == req), None
            )
            if req_analysis:
                req_comparison["solution_scores"][solution_number] = (
                    1 if req_analysis["addressed"] else 0
                )

        # Determine the best solution for this requirement
        best_solutions = [
            solution_number
            for solution_number, score in req_comparison["solution_scores"].items()
            if score == 1
        ]

        if best_solutions:
            req_comparison["best_solution"] = best_solutions[0]
            if len(best_solutions) == 1:
                req_comparison["explanation"] = (
                    f"Solution {best_solutions[0]} best addresses this requirement."
                )
            else:
                req_comparison["explanation"] = (
                    f"Solutions {', '.join(map(str, best_solutions))} equally address this requirement."
                )
        else:
            req_comparison["explanation"] = (
                "No solution adequately addresses this requirement."
            )

        requirement_comparisons[req] = req_comparison

    # Compare how well each solution respects each constraint
    constraint_comparisons = {}
    for constraint in constraints:
        constraint_comparison = {
            "constraint": constraint,
            "solution_scores": {},
            "best_solution": None,
            "explanation": "",
        }

        # Find which solutions respect this constraint
        for analysis in solution_analyses:
            solution_number = analysis["solution_number"]
            constraint_analyses = analysis["constraint_analyses"]

            # Find the analysis for this constraint
            constraint_analysis = next(
                (c for c in constraint_analyses if c["constraint"] == constraint), None
            )
            if constraint_analysis:
                constraint_comparison["solution_scores"][solution_number] = (
                    1 if constraint_analysis["respected"] else 0
                )

        # Determine the best solution for this constraint
        best_solutions = [
            solution_number
            for solution_number, score in constraint_comparison[
                "solution_scores"
            ].items()
            if score == 1
        ]

        if best_solutions:
            constraint_comparison["best_solution"] = best_solutions[0]
            if len(best_solutions) == 1:
                constraint_comparison["explanation"] = (
                    f"Solution {best_solutions[0]} best respects this constraint."
                )
            else:
                constraint_comparison["explanation"] = (
                    f"Solutions {', '.join(map(str, best_solutions))} equally respect this constraint."
                )
        else:
            constraint_comparison["explanation"] = (
                "No solution adequately respects this constraint."
            )

        constraint_comparisons[constraint] = constraint_comparison

    # Calculate overall scores for each solution
    overall_scores = {}
    for analysis in solution_analyses:
        solution_number = analysis["solution_number"]

        # Calculate score based on requirements addressed and constraints respected
        req_score = analysis["requirements_addressed"] / max(
            1, analysis["requirements_total"]
        )
        constraint_score = analysis["constraints_respected"] / max(
            1, analysis["constraints_total"]
        )

        # Overall score is the average of the two scores
        overall_score = (req_score + constraint_score) / 2

        overall_scores[solution_number] = {
            "requirements_score": req_score,
            "constraints_score": constraint_score,
            "overall_score": overall_score,
        }

    # Determine the best overall solution
    best_solution = (
        max(overall_scores.items(), key=lambda x: x[1]["overall_score"])[0]
        if overall_scores
        else None
    )

    # Create the comparative analysis
    comparative_analysis = {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "task_id": task.get("id", "unknown"),
        "requirement_comparisons": requirement_comparisons,
        "constraint_comparisons": constraint_comparisons,
        "overall_scores": overall_scores,
        "best_solution": best_solution,
        "explanation": (
            f"Solution {best_solution} has the highest overall score."
            if best_solution
            else "No solution could be determined as the best."
        ),
    }

    return comparative_analysis


def _generate_multi_solution_synthesis(
    self: WSDETeam,
    solutions: list[dict[str, Any]],
    comparative_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate a synthesis from multiple solutions.

    This method creates a synthesis that incorporates the best aspects of multiple solutions
    based on a comparative analysis.

    Args:
        self: The WSDETeam instance
        solutions: The solutions to synthesize
        comparative_analysis: The comparative analysis of the solutions

    Returns:
        A dictionary containing the synthesis
    """
    logger.info("Generating multi-solution synthesis")

    # Get the best solution as a starting point
    best_solution_number = comparative_analysis.get("best_solution")
    if best_solution_number is None or best_solution_number > len(solutions):
        logger.warning("No best solution identified or invalid best solution number")
        best_solution_number = 1  # Default to the first solution

    best_solution = solutions[best_solution_number - 1]

    # Extract content and code from the best solution
    content = best_solution.get("content", "")
    code = best_solution.get("code", "")

    # Get the requirement comparisons
    requirement_comparisons = comparative_analysis.get("requirement_comparisons", {})

    # Identify requirements that are better addressed by other solutions
    improvements = []
    for req, comparison in requirement_comparisons.items():
        best_for_req = comparison.get("best_solution")
        if best_for_req is not None and best_for_req != best_solution_number:
            # This requirement is better addressed by another solution
            solution_for_req = solutions[best_for_req - 1]

            # Extract the relevant content and code from the other solution
            req_content = solution_for_req.get("content", "")
            req_code = solution_for_req.get("code", "")

            # Find the relevant parts of the content and code that address this requirement
            # This is a simplistic approach; in reality, this would be more sophisticated
            req_lower = req.lower()

            # Find paragraphs in the content that mention the requirement
            paragraphs = re.split(r"\n\s*\n", req_content)
            relevant_paragraphs = [p for p in paragraphs if req_lower in p.lower()]

            # Find functions or classes in the code that might address the requirement
            # This is a very simplistic approach
            code_lines = req_code.split("\n")
            relevant_code_blocks = []
            current_block = []
            in_relevant_block = False

            for line in code_lines:
                if req_lower in line.lower():
                    in_relevant_block = True

                if in_relevant_block:
                    current_block.append(line)

                if in_relevant_block and line.strip() == "":
                    in_relevant_block = False
                    if current_block:
                        relevant_code_blocks.append("\n".join(current_block))
                        current_block = []

            if current_block:
                relevant_code_blocks.append("\n".join(current_block))

            # Add the improvements
            if relevant_paragraphs:
                content += "\n\n" + "\n\n".join(relevant_paragraphs)
                improvements.append(
                    f"Incorporated explanation for '{req}' from solution {best_for_req}"
                )

            if relevant_code_blocks:
                code += "\n\n" + "\n\n".join(relevant_code_blocks)
                improvements.append(
                    f"Incorporated code for '{req}' from solution {best_for_req}"
                )

    # Create the synthesis
    synthesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "base_solution_id": best_solution.get("id", "unknown"),
        "base_solution_number": best_solution_number,
        "content": content,
        "code": code,
        "improvements": improvements,
        "reasoning": f"This synthesis is based on solution {best_solution_number} as the best overall solution, with improvements incorporated from other solutions where they better address specific requirements.",
    }

    return synthesis


def _generate_comparative_evaluation(
    self: WSDETeam,
    synthesis: dict[str, Any],
    solutions: list[dict[str, Any]],
    comparative_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate an evaluation of a multi-solution synthesis.

    This method evaluates how well the synthesis incorporates the best aspects
    of multiple solutions.

    Args:
        self: The WSDETeam instance
        synthesis: The synthesis to evaluate
        solutions: The original solutions
        comparative_analysis: The comparative analysis of the solutions

    Returns:
        A dictionary containing the evaluation
    """
    logger.info(
        f"Generating comparative evaluation for synthesis: {synthesis.get('id', 'unknown')}"
    )

    # Extract content and code from synthesis
    content = synthesis.get("content", "")
    code = synthesis.get("code", "")

    # Get the requirement comparisons
    requirement_comparisons = comparative_analysis.get("requirement_comparisons", {})

    # Evaluate how well the synthesis addresses each requirement
    requirement_evaluations = []
    for req, comparison in requirement_comparisons.items():
        # Simple evaluation: check if the requirement is mentioned in the content or code
        content_match = req.lower() in content.lower()
        code_match = req.lower() in code.lower()
        addressed = content_match or code_match

        # Check if the synthesis incorporates the best solution for this requirement
        best_for_req = comparison.get("best_solution")
        incorporated = False

        if best_for_req is not None:
            # Check if an improvement was made for this requirement
            for improvement in synthesis.get("improvements", []):
                if (
                    req.lower() in improvement.lower()
                    and f"solution {best_for_req}" in improvement
                ):
                    incorporated = True
                    break

        requirement_evaluations.append(
            {
                "requirement": req,
                "addressed": addressed,
                "best_solution_incorporated": incorporated,
                "explanation": f"The requirement is {'addressed' if addressed else 'not clearly addressed'} in the synthesis. The best solution for this requirement {'was' if incorporated else 'was not'} incorporated.",
            }
        )

    # Calculate scores
    requirements_addressed = sum(
        1 for eval in requirement_evaluations if eval["addressed"]
    )
    requirements_incorporated = sum(
        1 for eval in requirement_evaluations if eval["best_solution_incorporated"]
    )
    requirements_total = len(requirement_evaluations)

    addressed_score = requirements_addressed / max(1, requirements_total)
    incorporation_score = requirements_incorporated / max(1, requirements_total)

    # Overall score is the average of the two scores
    overall_score = (addressed_score + incorporation_score) / 2

    # Create the evaluation
    evaluation = {
        "id": str(uuid4()),
        "timestamp": datetime.now().isoformat(),
        "synthesis_id": synthesis.get("id", "unknown"),
        "requirement_evaluations": requirement_evaluations,
        "requirements_addressed": requirements_addressed,
        "requirements_incorporated": requirements_incorporated,
        "requirements_total": requirements_total,
        "addressed_score": addressed_score,
        "incorporation_score": incorporation_score,
        "overall_score": overall_score,
        "explanation": f"The synthesis addresses {requirements_addressed} out of {requirements_total} requirements and incorporates the best solution for {requirements_incorporated} requirements. The overall score is {overall_score:.2f} out of 1.0, indicating {'excellent' if overall_score > 0.8 else 'good' if overall_score > 0.6 else 'fair' if overall_score > 0.4 else 'poor'} quality.",
    }

    return evaluation
