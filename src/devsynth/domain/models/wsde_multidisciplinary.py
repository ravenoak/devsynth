"""
WSDE multi-disciplinary reasoning functionality.

This module contains functionality for multi-disciplinary reasoning in a WSDE team,
including methods for applying multi-disciplinary dialectical reasoning, gathering
disciplinary perspectives, identifying perspective conflicts, and generating
multi-disciplinary synthesis and evaluation.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
import re

from devsynth.logging_setup import DevSynthLogger

# Import the base WSDETeam class for type hints
from devsynth.domain.models.wsde_base import WSDETeam

logger = DevSynthLogger(__name__)


def apply_multi_disciplinary_dialectical_reasoning(self: WSDETeam, task: Dict[str, Any], 
                                                 critic_agent: Any, 
                                                 disciplinary_knowledge: Dict[str, Any],
                                                 disciplinary_agents: List[Any],
                                                 memory_integration: Any = None):
    """
    Apply multi-disciplinary dialectical reasoning to a task.

    This method implements an advanced dialectical reasoning process that incorporates
    perspectives from multiple disciplines to create a more comprehensive synthesis.

    Args:
        task: The task containing the solution to be analyzed
        critic_agent: The agent that will critique the solution
        disciplinary_knowledge: Knowledge base for different disciplines
        disciplinary_agents: List of agents with different disciplinary expertise
        memory_integration: Optional memory integration component

    Returns:
        Dictionary containing the multi-disciplinary dialectical reasoning results
    """
    if not task or "solution" not in task:
        self.logger.warning("Cannot apply multi-disciplinary dialectical reasoning: no solution provided")
        return {"status": "failed", "reason": "no_solution"}

    # Extract the thesis solution
    thesis_solution = task["solution"]

    # Gather perspectives from different disciplines
    perspectives = self._gather_disciplinary_perspectives(
        thesis_solution, task, disciplinary_agents, disciplinary_knowledge
    )

    # Identify conflicts between perspectives
    conflicts = self._identify_perspective_conflicts(perspectives)

    # Generate synthesis incorporating multiple perspectives
    synthesis = self._generate_multi_disciplinary_synthesis(
        thesis_solution, perspectives, conflicts, critic_agent
    )

    # Generate evaluation of the synthesis
    evaluation = self._generate_multi_disciplinary_evaluation(
        synthesis, perspectives, task
    )

    # Create result
    result = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "task_id": task.get("id", str(uuid4())),
        "thesis": thesis_solution,
        "perspectives": perspectives,
        "conflicts": conflicts,
        "synthesis": synthesis,
        "evaluation": evaluation,
        "method": "multi_disciplinary_dialectical_reasoning"
    }

    # Invoke dialectical hooks if any
    for hook in self.dialectical_hooks:
        hook(task, [result])

    # Store in memory if memory integration is provided
    if memory_integration:
        memory_integration.store_dialectical_result(task, result)

    return result


def _gather_disciplinary_perspectives(self: WSDETeam, solution: Dict[str, Any], 
                                     task: Dict[str, Any],
                                     disciplinary_agents: List[Any],
                                     disciplinary_knowledge: Dict[str, Any]):
    """
    Gather perspectives from different disciplines on a solution.

    Args:
        solution: The solution to be analyzed
        task: The task being worked on
        disciplinary_agents: List of agents with different disciplinary expertise
        disciplinary_knowledge: Knowledge base for different disciplines

    Returns:
        List of dictionaries containing disciplinary perspectives
    """
    perspectives = []

    # Determine relevant disciplines for the task
    relevant_disciplines = set()

    # Extract disciplines from task description
    if "description" in task and isinstance(task["description"], str):
        description = task["description"].lower()
        for discipline in disciplinary_knowledge.keys():
            if discipline.lower() in description:
                relevant_disciplines.add(discipline)

    # Extract disciplines from task requirements
    if "requirements" in task:
        requirements = task["requirements"]
        if isinstance(requirements, list):
            for req in requirements:
                if isinstance(req, str):
                    req_text = req.lower()
                    for discipline in disciplinary_knowledge.keys():
                        if discipline.lower() in req_text:
                            relevant_disciplines.add(discipline)
                elif isinstance(req, dict) and "description" in req:
                    req_text = req["description"].lower()
                    for discipline in disciplinary_knowledge.keys():
                        if discipline.lower() in req_text:
                            relevant_disciplines.add(discipline)
        elif isinstance(requirements, str):
            req_text = requirements.lower()
            for discipline in disciplinary_knowledge.keys():
                if discipline.lower() in req_text:
                    relevant_disciplines.add(discipline)

    # If no relevant disciplines found, use all available
    if not relevant_disciplines:
        relevant_disciplines = set(disciplinary_knowledge.keys())

    # Gather perspectives from each disciplinary agent
    for agent in disciplinary_agents:
        # Determine agent's discipline
        discipline = self._determine_agent_discipline(agent)

        if discipline in relevant_disciplines:
            # In a real implementation, this would call agent.analyze() or similar
            # For now, we'll generate a simulated perspective

            perspective = {
                "id": str(uuid4()),
                "timestamp": datetime.now(),
                "agent": agent.name if hasattr(agent, 'name') else "unknown",
                "discipline": discipline,
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "discipline_specific_insights": []
            }

            # Get discipline-specific knowledge
            discipline_knowledge = disciplinary_knowledge.get(discipline, {})

            # Generate strengths based on discipline
            if "strengths_criteria" in discipline_knowledge:
                for criterion in discipline_knowledge["strengths_criteria"]:
                    if self._solution_addresses_item(solution, criterion):
                        perspective["strengths"].append(f"Solution addresses {criterion}")

            # Generate weaknesses based on discipline
            if "weaknesses_criteria" in discipline_knowledge:
                for criterion in discipline_knowledge["weaknesses_criteria"]:
                    if not self._solution_addresses_item(solution, criterion):
                        perspective["weaknesses"].append(f"Solution does not adequately address {criterion}")

            # Generate recommendations based on discipline
            if "best_practices" in discipline_knowledge:
                for practice in discipline_knowledge["best_practices"]:
                    if not self._solution_addresses_item(solution, practice):
                        perspective["recommendations"].append(f"Incorporate {practice} into the solution")

            # Generate discipline-specific insights
            if "key_insights" in discipline_knowledge:
                for insight in discipline_knowledge["key_insights"]:
                    perspective["discipline_specific_insights"].append(insight)

            # If no specific items were generated, add some generic ones
            if not perspective["strengths"]:
                perspective["strengths"] = [
                    f"The solution demonstrates understanding of basic {discipline} principles",
                    f"The approach is consistent with {discipline} methodologies"
                ]

            if not perspective["weaknesses"]:
                perspective["weaknesses"] = [
                    f"The solution could better incorporate {discipline} best practices",
                    f"The approach lacks depth in {discipline}-specific considerations"
                ]

            if not perspective["recommendations"]:
                perspective["recommendations"] = [
                    f"Enhance the solution with more {discipline}-specific approaches",
                    f"Consider {discipline} standards and guidelines more thoroughly"
                ]

            if not perspective["discipline_specific_insights"]:
                perspective["discipline_specific_insights"] = [
                    f"From a {discipline} perspective, the solution should focus more on domain-specific requirements",
                    f"{discipline} approaches typically emphasize different aspects than what is presented"
                ]

            perspectives.append(perspective)

    return perspectives


def _determine_agent_discipline(self: WSDETeam, agent: Any):
    """
    Determine the discipline of an agent based on its expertise.

    Args:
        agent: The agent to analyze

    Returns:
        String representing the agent's discipline
    """
    # Define discipline keywords
    discipline_keywords = {
        "software_engineering": ["software engineering", "programming", "coding", "development", "software design"],
        "security": ["security", "cybersecurity", "information security", "secure coding", "vulnerability"],
        "ux_design": ["user experience", "ux", "ui", "interface design", "usability"],
        "data_science": ["data science", "machine learning", "statistics", "data analysis", "analytics"],
        "devops": ["devops", "deployment", "infrastructure", "ci/cd", "operations"],
        "architecture": ["architecture", "system design", "distributed systems", "scalability"],
        "quality_assurance": ["quality assurance", "testing", "qa", "quality control", "verification"],
        "product_management": ["product management", "requirements", "user stories", "roadmap"]
    }

    # Check agent's expertise against discipline keywords
    if hasattr(agent, 'expertise') and agent.expertise:
        discipline_scores = {}

        for discipline, keywords in discipline_keywords.items():
            score = 0
            for expertise in agent.expertise:
                expertise_lower = expertise.lower()
                for keyword in keywords:
                    if keyword in expertise_lower:
                        score += 1
            discipline_scores[discipline] = score

        # Return discipline with highest score, or "general" if no matches
        max_score = max(discipline_scores.values())
        if max_score > 0:
            best_disciplines = [d for d, s in discipline_scores.items() if s == max_score]
            return best_disciplines[0]

    # Default to "general" if no specific discipline is found
    return "general"


def _solution_addresses_item(self: WSDETeam, solution: Dict[str, Any], item: str):
    """
    Check if a solution addresses a specific item.

    Args:
        solution: The solution to check
        item: The item to look for

    Returns:
        Boolean indicating whether the solution addresses the item
    """
    item_lower = item.lower()

    # Check in solution content
    if "content" in solution and isinstance(solution["content"], str):
        if item_lower in solution["content"].lower():
            return True

    # Check in solution code
    if "code" in solution and isinstance(solution["code"], str):
        if item_lower in solution["code"].lower():
            return True

    # Check in solution description
    if "description" in solution and isinstance(solution["description"], str):
        if item_lower in solution["description"].lower():
            return True

    # Check in solution approach
    if "approach" in solution and isinstance(solution["approach"], str):
        if item_lower in solution["approach"].lower():
            return True

    return False


def _identify_perspective_conflicts(self: WSDETeam, perspectives: List[Dict[str, Any]]):
    """
    Identify conflicts between perspectives from different disciplines.

    Args:
        perspectives: List of disciplinary perspectives

    Returns:
        List of dictionaries describing perspective conflicts
    """
    conflicts = []

    # Define known conflicting discipline pairs
    conflicting_disciplines = [
        ("security", "performance"),
        ("security", "ux_design"),
        ("performance", "quality_assurance"),
        ("software_engineering", "ux_design"),
        ("architecture", "devops")
    ]

    # Group perspectives by discipline
    discipline_perspectives = {}
    for perspective in perspectives:
        discipline = perspective.get("discipline")
        if discipline:
            if discipline not in discipline_perspectives:
                discipline_perspectives[discipline] = []
            discipline_perspectives[discipline].append(perspective)

    # Check for conflicts between discipline pairs
    for discipline1, discipline2 in conflicting_disciplines:
        if discipline1 in discipline_perspectives and discipline2 in discipline_perspectives:
            # Get recommendations from each discipline
            discipline1_recommendations = []
            for perspective in discipline_perspectives[discipline1]:
                discipline1_recommendations.extend(perspective.get("recommendations", []))

            discipline2_recommendations = []
            for perspective in discipline_perspectives[discipline2]:
                discipline2_recommendations.extend(perspective.get("recommendations", []))

            # Look for specific conflicting terms
            conflict_found = False
            conflict_details = []

            # Security vs Performance conflicts
            if (discipline1 == "security" and discipline2 == "performance") or (discipline1 == "performance" and discipline2 == "security"):
                security_recs = discipline1_recommendations if discipline1 == "security" else discipline2_recommendations
                performance_recs = discipline1_recommendations if discipline1 == "performance" else discipline2_recommendations

                for sec_rec in security_recs:
                    for perf_rec in performance_recs:
                        if ("encryption" in sec_rec.lower() and "optimization" in perf_rec.lower()) or \
                           ("authentication" in sec_rec.lower() and "latency" in perf_rec.lower()):
                            conflict_found = True
                            conflict_details.append(f"Security recommendation '{sec_rec}' conflicts with performance recommendation '{perf_rec}'")

            # Security vs UX Design conflicts
            elif (discipline1 == "security" and discipline2 == "ux_design") or (discipline1 == "ux_design" and discipline2 == "security"):
                security_recs = discipline1_recommendations if discipline1 == "security" else discipline2_recommendations
                ux_recs = discipline1_recommendations if discipline1 == "ux_design" else discipline2_recommendations

                for sec_rec in security_recs:
                    for ux_rec in ux_recs:
                        if ("authentication" in sec_rec.lower() and "simplify" in ux_rec.lower()) or \
                           ("validation" in sec_rec.lower() and "user experience" in ux_rec.lower()):
                            conflict_found = True
                            conflict_details.append(f"Security recommendation '{sec_rec}' conflicts with UX recommendation '{ux_rec}'")

            # Performance vs Quality Assurance conflicts
            elif (discipline1 == "performance" and discipline2 == "quality_assurance") or (discipline1 == "quality_assurance" and discipline2 == "performance"):
                performance_recs = discipline1_recommendations if discipline1 == "performance" else discipline2_recommendations
                qa_recs = discipline1_recommendations if discipline1 == "quality_assurance" else discipline2_recommendations

                for perf_rec in performance_recs:
                    for qa_rec in qa_recs:
                        if ("optimization" in perf_rec.lower() and "test coverage" in qa_rec.lower()) or \
                           ("efficiency" in perf_rec.lower() and "validation" in qa_rec.lower()):
                            conflict_found = True
                            conflict_details.append(f"Performance recommendation '{perf_rec}' conflicts with QA recommendation '{qa_rec}'")

            # Software Engineering vs UX Design conflicts
            elif (discipline1 == "software_engineering" and discipline2 == "ux_design") or (discipline1 == "ux_design" and discipline2 == "software_engineering"):
                se_recs = discipline1_recommendations if discipline1 == "software_engineering" else discipline2_recommendations
                ux_recs = discipline1_recommendations if discipline1 == "ux_design" else discipline2_recommendations

                for se_rec in se_recs:
                    for ux_rec in ux_recs:
                        if ("architecture" in se_rec.lower() and "user flow" in ux_rec.lower()) or \
                           ("pattern" in se_rec.lower() and "interface" in ux_rec.lower()):
                            conflict_found = True
                            conflict_details.append(f"Software Engineering recommendation '{se_rec}' conflicts with UX recommendation '{ux_rec}'")

            # Architecture vs DevOps conflicts
            elif (discipline1 == "architecture" and discipline2 == "devops") or (discipline1 == "devops" and discipline2 == "architecture"):
                arch_recs = discipline1_recommendations if discipline1 == "architecture" else discipline2_recommendations
                devops_recs = discipline1_recommendations if discipline1 == "devops" else discipline2_recommendations

                for arch_rec in arch_recs:
                    for devops_rec in devops_recs:
                        if ("monolithic" in arch_rec.lower() and "containerization" in devops_rec.lower()) or \
                           ("coupling" in arch_rec.lower() and "deployment" in devops_rec.lower()):
                            conflict_found = True
                            conflict_details.append(f"Architecture recommendation '{arch_rec}' conflicts with DevOps recommendation '{devops_rec}'")

            # If conflict found, add to list
            if conflict_found:
                conflicts.append({
                    "discipline1": discipline1,
                    "discipline2": discipline2,
                    "details": conflict_details
                })

    return conflicts


def _generate_multi_disciplinary_synthesis(self: WSDETeam, thesis: Dict[str, Any], 
                                          perspectives: List[Dict[str, Any]], 
                                          conflicts: List[Dict[str, Any]],
                                          critic_agent: Any):
    """
    Generate a synthesis incorporating multiple disciplinary perspectives.

    Args:
        thesis: The original thesis solution
        perspectives: List of disciplinary perspectives
        conflicts: List of identified conflicts between perspectives
        critic_agent: The agent that will critique the synthesis

    Returns:
        Dictionary containing the multi-disciplinary synthesis
    """
    synthesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "integrated_perspectives": [],
        "resolved_conflicts": [],
        "improvements": [],
        "reasoning": "",
        "content": None,
        "code": None
    }

    # Extract content and code from thesis
    original_content = thesis.get("content", "")
    original_code = thesis.get("code", "")

    # Initialize improved content and code
    improved_content = original_content
    improved_code = original_code

    # Group perspectives by discipline
    discipline_perspectives = {}
    for perspective in perspectives:
        discipline = perspective.get("discipline")
        if discipline:
            if discipline not in discipline_perspectives:
                discipline_perspectives[discipline] = []
            discipline_perspectives[discipline].append(perspective)

    # Track integrated perspectives
    integrated_perspective_ids = set()

    # Process each discipline's perspectives
    for discipline, discipline_perspectives_list in discipline_perspectives.items():
        # Combine recommendations from all perspectives in this discipline
        discipline_recommendations = []
        for perspective in discipline_perspectives_list:
            discipline_recommendations.extend(perspective.get("recommendations", []))

        # Apply discipline-specific improvements
        if discipline == "software_engineering" and original_code:
            # Apply software engineering improvements to code
            for recommendation in discipline_recommendations:
                if "modular" in recommendation.lower() or "refactor" in recommendation.lower():
                    # Simulate improving modularity
                    improved_code = "# Improved modularity based on software engineering principles\n" + improved_code
                    synthesis["improvements"].append(f"Enhanced code modularity ({discipline})")
                elif "pattern" in recommendation.lower() or "design" in recommendation.lower():
                    # Simulate applying design patterns
                    improved_code = "# Applied appropriate design patterns\n" + improved_code
                    synthesis["improvements"].append(f"Applied design patterns ({discipline})")

            # Mark perspectives as integrated
            for perspective in discipline_perspectives_list:
                integrated_perspective_ids.add(perspective["id"])

        elif discipline == "security" and original_code:
            # Apply security improvements to code
            for recommendation in discipline_recommendations:
                if "authentication" in recommendation.lower() or "authorization" in recommendation.lower():
                    # Simulate improving authentication
                    improved_code = "# Enhanced authentication and authorization\n" + improved_code
                    synthesis["improvements"].append(f"Strengthened authentication mechanisms ({discipline})")
                elif "validation" in recommendation.lower() or "sanitization" in recommendation.lower():
                    # Simulate improving input validation
                    improved_code = "# Added input validation and sanitization\n" + improved_code
                    synthesis["improvements"].append(f"Added comprehensive input validation ({discipline})")

            # Mark perspectives as integrated
            for perspective in discipline_perspectives_list:
                integrated_perspective_ids.add(perspective["id"])

        elif discipline == "ux_design" and original_content:
            # Apply UX improvements to content
            for recommendation in discipline_recommendations:
                if "user flow" in recommendation.lower() or "experience" in recommendation.lower():
                    # Simulate improving user flow descriptions
                    improved_content = "# Enhanced user flow descriptions\n\n" + improved_content
                    synthesis["improvements"].append(f"Improved user flow documentation ({discipline})")
                elif "interface" in recommendation.lower() or "design" in recommendation.lower():
                    # Simulate improving interface descriptions
                    improved_content = "# Added detailed interface design considerations\n\n" + improved_content
                    synthesis["improvements"].append(f"Added interface design details ({discipline})")

            # Mark perspectives as integrated
            for perspective in discipline_perspectives_list:
                integrated_perspective_ids.add(perspective["id"])

        elif discipline == "data_science" and (original_code or original_content):
            # Apply data science improvements
            for recommendation in discipline_recommendations:
                if "algorithm" in recommendation.lower() or "model" in recommendation.lower():
                    # Simulate improving algorithms
                    if original_code:
                        improved_code = "# Optimized algorithms based on data science principles\n" + improved_code
                    if original_content:
                        improved_content = "# Added data model explanations\n\n" + improved_content
                    synthesis["improvements"].append(f"Enhanced data processing algorithms ({discipline})")

            # Mark perspectives as integrated
            for perspective in discipline_perspectives_list:
                integrated_perspective_ids.add(perspective["id"])

        # Add more discipline-specific improvements as needed

    # Resolve conflicts
    resolved_conflicts = []
    for conflict in conflicts:
        discipline1 = conflict["discipline1"]
        discipline2 = conflict["discipline2"]

        # Create resolution
        resolution = {
            "disciplines": [discipline1, discipline2],
            "details": conflict.get("details", []),
            "resolution_approach": f"Balanced {discipline1} and {discipline2} considerations",
            "resolution_details": []
        }

        # Apply specific conflict resolutions
        if (discipline1 == "security" and discipline2 == "performance") or (discipline1 == "performance" and discipline2 == "security"):
            # Resolve security vs performance conflict
            resolution["resolution_details"].append("Prioritized security for critical operations while optimizing non-critical paths")
            resolution["resolution_details"].append("Implemented selective encryption for sensitive data only")
            resolution["resolution_details"].append("Used caching for frequently accessed, non-sensitive data")

        elif (discipline1 == "security" and discipline2 == "ux_design") or (discipline1 == "ux_design" and discipline2 == "security"):
            # Resolve security vs UX conflict
            resolution["resolution_details"].append("Implemented progressive security that scales with sensitivity of operations")
            resolution["resolution_details"].append("Used secure defaults with clear override options")
            resolution["resolution_details"].append("Added clear security-related feedback for users")

        elif (discipline1 == "performance" and discipline2 == "quality_assurance") or (discipline1 == "quality_assurance" and discipline2 == "performance"):
            # Resolve performance vs QA conflict
            resolution["resolution_details"].append("Focused performance optimization on measured bottlenecks only")
            resolution["resolution_details"].append("Maintained comprehensive tests for critical paths")
            resolution["resolution_details"].append("Implemented performance tests as part of the test suite")

        elif (discipline1 == "software_engineering" and discipline2 == "ux_design") or (discipline1 == "ux_design" and discipline2 == "software_engineering"):
            # Resolve software engineering vs UX conflict
            resolution["resolution_details"].append("Designed architecture to support key user flows")
            resolution["resolution_details"].append("Created abstraction layers to separate UI concerns from business logic")
            resolution["resolution_details"].append("Documented UX considerations in architectural decisions")

        elif (discipline1 == "architecture" and discipline2 == "devops") or (discipline1 == "devops" and discipline2 == "architecture"):
            # Resolve architecture vs DevOps conflict
            resolution["resolution_details"].append("Designed for deployability from the start")
            resolution["resolution_details"].append("Used microservices where appropriate for deployment flexibility")
            resolution["resolution_details"].append("Incorporated infrastructure as code principles in architecture")

        resolved_conflicts.append(resolution)

    # Update synthesis with resolved conflicts
    synthesis["resolved_conflicts"] = resolved_conflicts

    # Set improved content and code
    if improved_content != original_content:
        synthesis["content"] = improved_content

    if improved_code != original_code:
        synthesis["code"] = improved_code

    # Record integrated perspectives
    synthesis["integrated_perspectives"] = list(integrated_perspective_ids)

    # Generate disciplinary integrity descriptions
    synthesis["disciplinary_integrity"] = {}
    for discipline in discipline_perspectives.keys():
        if discipline == "software_engineering":
            synthesis["disciplinary_integrity"][discipline] = f"Ensures core software engineering principles are maintained while integrating perspectives from other disciplines."
        elif discipline == "security":
            synthesis["disciplinary_integrity"][discipline] = f"Preserves essential security principles and practices while balancing requirements from other disciplines."
        elif discipline == "ux_design":
            synthesis["disciplinary_integrity"][discipline] = f"Maintains core user experience principles while ensuring compatibility with security and performance requirements."
        elif discipline == "data_science":
            synthesis["disciplinary_integrity"][discipline] = f"Ensures essential data science methodologies are preserved while integrating with software engineering practices."
        elif discipline == "performance":
            synthesis["disciplinary_integrity"][discipline] = f"Maintains core performance principles while balancing requirements from security and accessibility."
        elif discipline == "accessibility":
            synthesis["disciplinary_integrity"][discipline] = f"Preserves essential accessibility standards while ensuring compatibility with performance requirements."
        elif discipline == "user_experience":
            synthesis["disciplinary_integrity"][discipline] = f"Ensures core user experience principles are maintained while integrating security requirements."
        else:
            synthesis["disciplinary_integrity"][discipline] = f"Maintains core principles of {discipline.replace('_', ' ')} while integrating with other disciplinary requirements."

    # Generate reasoning
    reasoning_parts = []

    # Summarize integrated perspectives
    reasoning_parts.append("## Integrated Disciplinary Perspectives")
    for discipline, discipline_perspectives_list in discipline_perspectives.items():
        reasoning_parts.append(f"\n### {discipline.replace('_', ' ').title()} Perspective")

        # Summarize strengths
        strengths = []
        for perspective in discipline_perspectives_list:
            strengths.extend(perspective.get("strengths", []))

        if strengths:
            reasoning_parts.append("\n#### Strengths")
            for strength in strengths[:3]:  # Limit to top 3 for brevity
                reasoning_parts.append(f"- {strength}")

        # Summarize recommendations
        recommendations = []
        for perspective in discipline_perspectives_list:
            recommendations.extend(perspective.get("recommendations", []))

        if recommendations:
            reasoning_parts.append("\n#### Recommendations")
            for recommendation in recommendations[:3]:  # Limit to top 3 for brevity
                reasoning_parts.append(f"- {recommendation}")

    # Summarize conflict resolutions
    if resolved_conflicts:
        reasoning_parts.append("\n## Conflict Resolutions")
        for resolution in resolved_conflicts:
            discipline1 = resolution["disciplines"][0].replace('_', ' ').title()
            discipline2 = resolution["disciplines"][1].replace('_', ' ').title()
            reasoning_parts.append(f"\n### {discipline1} vs {discipline2}")
            reasoning_parts.append(f"- Approach: {resolution['resolution_approach']}")

            if resolution["resolution_details"]:
                reasoning_parts.append("- Details:")
                for detail in resolution["resolution_details"]:
                    reasoning_parts.append(f"  - {detail}")

    # Summarize improvements
    if synthesis["improvements"]:
        reasoning_parts.append("\n## Improvements Applied")
        for improvement in synthesis["improvements"]:
            reasoning_parts.append(f"- {improvement}")

    # Combine all parts
    synthesis["reasoning"] = "\n".join(reasoning_parts)

    return synthesis


def _generate_multi_disciplinary_evaluation(self: WSDETeam, synthesis: Dict[str, Any], 
                                           perspectives: List[Dict[str, Any]], 
                                           task: Dict[str, Any]):
    """
    Generate an evaluation of the multi-disciplinary synthesis.

    Args:
        synthesis: The multi-disciplinary synthesis
        perspectives: List of disciplinary perspectives
        task: The original task

    Returns:
        Dictionary containing the evaluation
    """
    evaluation = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "overall_assessment": "",
        "discipline_assessments": {},
        "strengths": [],
        "limitations": [],
        "future_work": []
    }

    # Group perspectives by discipline
    discipline_perspectives = {}
    for perspective in perspectives:
        discipline = perspective.get("discipline")
        if discipline:
            if discipline not in discipline_perspectives:
                discipline_perspectives[discipline] = []
            discipline_perspectives[discipline].append(perspective)

    # Generate discipline-specific assessments
    for discipline, discipline_perspectives_list in discipline_perspectives.items():
        # Initialize discipline assessment
        discipline_assessment = {
            "score": 0,  # 0-10 scale
            "strengths": [],
            "limitations": []
        }

        # Check if discipline's recommendations were integrated
        integrated_count = 0
        total_recommendations = 0

        for perspective in discipline_perspectives_list:
            perspective_id = perspective.get("id")
            if perspective_id in synthesis.get("integrated_perspectives", []):
                integrated_count += 1

            total_recommendations += len(perspective.get("recommendations", []))

            # Add strengths from this perspective
            for strength in perspective.get("strengths", [])[:2]:  # Limit to top 2
                if strength not in discipline_assessment["strengths"]:
                    discipline_assessment["strengths"].append(strength)

            # Add weaknesses from this perspective as limitations
            for weakness in perspective.get("weaknesses", [])[:2]:  # Limit to top 2
                if weakness not in discipline_assessment["limitations"]:
                    discipline_assessment["limitations"].append(weakness)

        # Calculate integration score (0-10)
        if total_recommendations > 0:
            integration_ratio = integrated_count / len(discipline_perspectives_list)
            discipline_assessment["score"] = min(10, int(integration_ratio * 10))
        else:
            discipline_assessment["score"] = 5  # Neutral score if no recommendations

        # Add discipline assessment
        evaluation["discipline_assessments"][discipline] = discipline_assessment

        # Add top strengths to overall evaluation
        for strength in discipline_assessment["strengths"][:1]:  # Take top 1 from each discipline
            if strength not in evaluation["strengths"]:
                evaluation["strengths"].append(strength)

        # Add top limitations to overall evaluation
        for limitation in discipline_assessment["limitations"][:1]:  # Take top 1 from each discipline
            if limitation not in evaluation["limitations"]:
                evaluation["limitations"].append(limitation)

    # Calculate overall score (average of discipline scores)
    discipline_scores = [assessment["score"] for assessment in evaluation["discipline_assessments"].values()]
    overall_score = sum(discipline_scores) / max(1, len(discipline_scores))

    # Generate overall assessment based on score
    if overall_score >= 8:
        assessment = "Excellent multi-disciplinary synthesis that effectively integrates perspectives from all relevant disciplines."
    elif overall_score >= 6:
        assessment = "Good multi-disciplinary synthesis with successful integration of most disciplinary perspectives, though some areas could be improved."
    elif overall_score >= 4:
        assessment = "Adequate multi-disciplinary synthesis with partial integration of disciplinary perspectives, but significant room for improvement."
    else:
        assessment = "Limited multi-disciplinary synthesis that fails to adequately integrate perspectives from multiple disciplines."

    evaluation["overall_assessment"] = f"{assessment} (Score: {overall_score:.1f}/10)"

    # Generate future work recommendations
    for discipline, assessment in evaluation["discipline_assessments"].items():
        if assessment["score"] < 7:  # Only suggest future work for lower-scoring disciplines
            discipline_name = discipline.replace('_', ' ').title()
            evaluation["future_work"].append(f"Further integrate {discipline_name} perspectives, particularly addressing: {', '.join(assessment['limitations'][:1])}")

    # Add general future work recommendation if none specific
    if not evaluation["future_work"]:
        evaluation["future_work"].append("Continue to refine the integration of disciplinary perspectives as the solution evolves")

    return evaluation
