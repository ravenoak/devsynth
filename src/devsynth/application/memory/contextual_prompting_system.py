"""
Contextual Prompting System for Intelligent Agent Development

This module implements context prompting engineering to provide DevSynth
agents with clear behavioral directives and comprehensive environmental
constraints, transforming agent development into a structured engineering
discipline.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .execution_learning_integration import ExecutionLearningIntegration
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class BehavioralDirective:
    """Represents a behavioral directive for agent operation."""
    directive_id: str
    category: str  # "reasoning", "communication", "decision_making", "error_handling"
    description: str
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    priority: int = 1  # 1-5 scale, 5 being highest


@dataclass
class EnvironmentalConstraint:
    """Represents an environmental constraint for agent operation."""
    constraint_id: str
    constraint_type: str  # "resource", "security", "performance", "quality", "compliance"
    description: str
    limits: Dict[str, Any] = field(default_factory=dict)
    enforcement: str = "strict"  # "strict", "warning", "guidance"
    monitoring: bool = True


@dataclass
class ContextualPrompt:
    """Represents a contextual prompt with integrated directives and constraints."""
    prompt_id: str
    base_prompt: str
    behavioral_directives: List[BehavioralDirective] = field(default_factory=list)
    environmental_constraints: List[EnvironmentalConstraint] = field(default_factory=list)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    personalization_rules: Dict[str, Any] = field(default_factory=dict)
    validation_criteria: List[str] = field(default_factory=list)


@dataclass
class PromptEngineeringResult:
    """Result from contextual prompt engineering."""
    engineered_prompt: str
    directive_coverage: float
    constraint_compliance: float
    context_relevance: float
    estimated_effectiveness: float
    suggestions: List[str] = field(default_factory=list)


class ContextualPromptingSystem:
    """System for contextual prompting engineering."""

    def __init__(self, execution_learning: ExecutionLearningIntegration):
        """Initialize the contextual prompting system."""
        self.execution_learning = execution_learning
        self.behavioral_directives: Dict[str, BehavioralDirective] = {}
        self.environmental_constraints: Dict[str, EnvironmentalConstraint] = {}
        self.contextual_prompts: Dict[str, ContextualPrompt] = {}
        self.prompt_performance_history: List[Dict[str, Any]] = []

        # Initialize with default directives and constraints
        self._initialize_default_framework()

        logger.info("Contextual prompting system initialized")

    def _initialize_default_framework(self) -> None:
        """Initialize default behavioral directives and environmental constraints."""
        # Default behavioral directives
        self.behavioral_directives["reasoning_systematic"] = BehavioralDirective(
            directive_id="reasoning_systematic",
            category="reasoning",
            description="Apply systematic, step-by-step reasoning to all problems",
            requirements=[
                "Break down complex problems into manageable steps",
                "Evaluate each step for logical consistency",
                "Document reasoning process and assumptions"
            ],
            constraints=[
                "Avoid jumping to conclusions without evidence",
                "Consider alternative approaches before finalizing"
            ],
            examples=[
                "Step 1: Analyze problem requirements",
                "Step 2: Identify key variables and constraints",
                "Step 3: Evaluate multiple solution approaches"
            ],
            priority=5
        )

        self.behavioral_directives["communication_clear"] = BehavioralDirective(
            directive_id="communication_clear",
            category="communication",
            description="Communicate clearly and precisely in all interactions",
            requirements=[
                "Use precise technical language when appropriate",
                "Provide concrete examples for abstract concepts",
                "Structure responses logically"
            ],
            constraints=[
                "Avoid ambiguity in technical explanations",
                "Maintain professional tone"
            ],
            examples=[
                "Instead of 'it works', explain 'the algorithm processes input X to produce output Y'"
            ],
            priority=4
        )

        self.behavioral_directives["decision_evidence_based"] = BehavioralDirective(
            directive_id="decision_evidence_based",
            category="decision_making",
            description="Base all decisions on evidence and logical reasoning",
            requirements=[
                "Gather sufficient evidence before making decisions",
                "Consider multiple perspectives",
                "Document decision rationale"
            ],
            constraints=[
                "Avoid decisions based on incomplete information",
                "Consider long-term implications"
            ],
            examples=[
                "Decision: Use algorithm X because benchmark Y shows 15% better performance"
            ],
            priority=5
        )

        # Default environmental constraints
        self.environmental_constraints["resource_memory"] = EnvironmentalConstraint(
            constraint_id="resource_memory",
            constraint_type="resource",
            description="Memory usage must remain within acceptable limits",
            limits={"max_memory_mb": 2048, "max_context_tokens": 8192},
            enforcement="strict"
        )

        self.environmental_constraints["performance_response_time"] = EnvironmentalConstraint(
            constraint_id="performance_response_time",
            constraint_type="performance",
            description="Response time must meet performance requirements",
            limits={"max_response_seconds": 30, "preferred_response_seconds": 10},
            enforcement="warning"
        )

        self.environmental_constraints["quality_accuracy"] = EnvironmentalConstraint(
            constraint_id="quality_accuracy",
            constraint_type="quality",
            description="Maintain high accuracy in all responses",
            limits={"min_accuracy_score": 0.85, "target_accuracy_score": 0.95},
            enforcement="strict"
        )

    def create_contextual_prompt(self, base_prompt: str, context: Dict[str, Any] = None) -> ContextualPrompt:
        """Create a contextual prompt with integrated directives and constraints."""
        context = context or {}

        # Select relevant directives based on context
        relevant_directives = self._select_relevant_directives(context)

        # Select relevant constraints based on context
        relevant_constraints = self._select_relevant_constraints(context)

        # Generate context variables
        context_variables = self._generate_context_variables(context)

        # Apply personalization rules
        personalization = self._apply_personalization_rules(context)

        # Define validation criteria
        validation_criteria = self._define_validation_criteria(relevant_directives, relevant_constraints)

        prompt = ContextualPrompt(
            prompt_id=f"prompt_{len(self.contextual_prompts)}",
            base_prompt=base_prompt,
            behavioral_directives=relevant_directives,
            environmental_constraints=relevant_constraints,
            context_variables=context_variables,
            personalization_rules=personalization,
            validation_criteria=validation_criteria
        )

        self.contextual_prompts[prompt.prompt_id] = prompt
        return prompt

    def _select_relevant_directives(self, context: Dict[str, Any]) -> List[BehavioralDirective]:
        """Select behavioral directives relevant to the context."""
        relevant = []

        # Context-based selection
        if "reasoning_task" in context:
            relevant.append(self.behavioral_directives["reasoning_systematic"])

        if "communication_task" in context:
            relevant.append(self.behavioral_directives["communication_clear"])

        if "decision_task" in context:
            relevant.append(self.behavioral_directives["decision_evidence_based"])

        # Priority-based selection for high-priority contexts
        if context.get("priority") == "critical":
            # Add all high-priority directives
            for directive in self.behavioral_directives.values():
                if directive.priority >= 4:
                    if directive not in relevant:
                        relevant.append(directive)

        return relevant

    def _select_relevant_constraints(self, context: Dict[str, Any]) -> List[EnvironmentalConstraint]:
        """Select environmental constraints relevant to the context."""
        relevant = []

        # Resource constraints for long-running tasks
        if context.get("estimated_duration", 0) > 60:  # More than 1 minute
            relevant.append(self.environmental_constraints["resource_memory"])

        # Performance constraints for interactive tasks
        if context.get("interactive", False):
            relevant.append(self.environmental_constraints["performance_response_time"])

        # Quality constraints for critical tasks
        if context.get("critical", False):
            relevant.append(self.environmental_constraints["quality_accuracy"])

        return relevant

    def _generate_context_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate context variables for prompt personalization."""
        variables = {
            "current_time": self._get_current_time(),
            "session_context": context.get("session", "general"),
            "task_complexity": self._assess_task_complexity(context),
            "user_expertise": context.get("user_expertise", "intermediate")
        }

        # Add task-specific variables
        if "task_type" in context:
            variables["task_type"] = context["task_type"]

        if "domain" in context:
            variables["domain"] = context["domain"]

        return variables

    def _apply_personalization_rules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply personalization rules based on context."""
        personalization = {}

        # User expertise-based personalization
        user_expertise = context.get("user_expertise", "intermediate")

        if user_expertise == "beginner":
            personalization["detail_level"] = "basic"
            personalization["examples"] = "extensive"
            personalization["technical_depth"] = "low"
        elif user_expertise == "expert":
            personalization["detail_level"] = "comprehensive"
            personalization["examples"] = "concise"
            personalization["technical_depth"] = "high"
        else:
            personalization["detail_level"] = "moderate"
            personalization["examples"] = "balanced"
            personalization["technical_depth"] = "moderate"

        # Task type-based personalization
        task_type = context.get("task_type", "")
        if "code_generation" in task_type:
            personalization["focus"] = "implementation_details"
        elif "analysis" in task_type:
            personalization["focus"] = "analytical_depth"
        elif "documentation" in task_type:
            personalization["focus"] = "clarity_and_structure"

        return personalization

    def _define_validation_criteria(self, directives: List[BehavioralDirective], constraints: List[EnvironmentalConstraint]) -> List[str]:
        """Define validation criteria for the prompt."""
        criteria = []

        # Directive-based criteria
        for directive in directives:
            criteria.append(f"Response must follow {directive.category} directive: {directive.description}")

        # Constraint-based criteria
        for constraint in constraints:
            criteria.append(f"Response must comply with {constraint.constraint_type} constraint: {constraint.description}")

        # General criteria
        criteria.extend([
            "Response must be clear and well-structured",
            "Response must be relevant to the query",
            "Response must be accurate and evidence-based"
        ])

        return criteria

    def engineer_contextual_prompt(self, contextual_prompt: ContextualPrompt) -> PromptEngineeringResult:
        """Engineer a contextual prompt with integrated directives and constraints."""
        # Build the engineered prompt
        prompt_parts = []

        # Add behavioral directives
        if contextual_prompt.behavioral_directives:
            prompt_parts.append("BEHAVIORAL DIRECTIVES:")
            for directive in contextual_prompt.behavioral_directives:
                prompt_parts.append(f"- {directive.category.upper()}: {directive.description}")
                if directive.requirements:
                    for req in directive.requirements:
                        prompt_parts.append(f"  * {req}")

        # Add environmental constraints
        if contextual_prompt.environmental_constraints:
            prompt_parts.append("\nENVIRONMENTAL CONSTRAINTS:")
            for constraint in contextual_prompt.environmental_constraints:
                prompt_parts.append(f"- {constraint.constraint_type.upper()}: {constraint.description}")
                if constraint.limits:
                    prompt_parts.append(f"  Limits: {constraint.limits}")

        # Add context variables
        if contextual_prompt.context_variables:
            prompt_parts.append("\nCONTEXT:")
            for key, value in contextual_prompt.context_variables.items():
                prompt_parts.append(f"- {key}: {value}")

        # Add the base prompt
        prompt_parts.append(f"\nTASK: {contextual_prompt.base_prompt}")

        # Add validation criteria
        if contextual_prompt.validation_criteria:
            prompt_parts.append("\nVALIDATION CRITERIA:")
            for criterion in contextual_prompt.validation_criteria:
                prompt_parts.append(f"- {criterion}")

        engineered_prompt = "\n".join(prompt_parts)

        # Calculate engineering metrics
        directive_coverage = len(contextual_prompt.behavioral_directives) / len(self.behavioral_directives) if self.behavioral_directives else 0.0
        constraint_compliance = len(contextual_prompt.environmental_constraints) / len(self.environmental_constraints) if self.environmental_constraints else 0.0

        # Estimate effectiveness based on coverage and personalization
        context_relevance = self._calculate_context_relevance(contextual_prompt)
        estimated_effectiveness = (directive_coverage * 0.3 + constraint_compliance * 0.3 + context_relevance * 0.4)

        # Generate suggestions
        suggestions = self._generate_engineering_suggestions(contextual_prompt, estimated_effectiveness)

        return PromptEngineeringResult(
            engineered_prompt=engineered_prompt,
            directive_coverage=directive_coverage,
            constraint_compliance=constraint_compliance,
            context_relevance=context_relevance,
            estimated_effectiveness=estimated_effectiveness,
            suggestions=suggestions
        )

    def _calculate_context_relevance(self, contextual_prompt: ContextualPrompt) -> float:
        """Calculate how relevant the prompt is to its intended context."""
        relevance_score = 0.0

        # Check personalization alignment
        personalization = contextual_prompt.personalization_rules
        if personalization:
            relevance_score += 0.3

        # Check context variable completeness
        if contextual_prompt.context_variables:
            relevance_score += 0.3

        # Check validation criteria specificity
        if len(contextual_prompt.validation_criteria) > 3:
            relevance_score += 0.2

        # Check directive-constraint balance
        directive_count = len(contextual_prompt.behavioral_directives)
        constraint_count = len(contextual_prompt.environmental_constraints)

        if 0.5 <= directive_count / max(constraint_count, 1) <= 2.0:
            relevance_score += 0.2

        return min(1.0, relevance_score)

    def _generate_engineering_suggestions(self, contextual_prompt: ContextualPrompt, effectiveness: float) -> List[str]:
        """Generate suggestions for improving the prompt engineering."""
        suggestions = []

        # Low effectiveness suggestions
        if effectiveness < 0.6:
            suggestions.append("Consider adding more specific behavioral directives")

        if len(contextual_prompt.behavioral_directives) == 0:
            suggestions.append("Add behavioral directives to guide agent behavior")

        if len(contextual_prompt.environmental_constraints) == 0:
            suggestions.append("Add environmental constraints to ensure operational compliance")

        # Balance suggestions
        directive_count = len(contextual_prompt.behavioral_directives)
        constraint_count = len(contextual_prompt.environmental_constraints)

        if directive_count > constraint_count * 2:
            suggestions.append("Balance directives with more environmental constraints")

        if constraint_count > directive_count * 2:
            suggestions.append("Balance constraints with more behavioral directives")

        # Context suggestions
        if not contextual_prompt.context_variables:
            suggestions.append("Add context variables for better personalization")

        return suggestions

    def add_behavioral_directive(self, directive: BehavioralDirective) -> None:
        """Add a new behavioral directive."""
        self.behavioral_directives[directive.directive_id] = directive
        logger.info(f"Added behavioral directive: {directive.directive_id}")

    def add_environmental_constraint(self, constraint: EnvironmentalConstraint) -> None:
        """Add a new environmental constraint."""
        self.environmental_constraints[constraint.constraint_id] = constraint
        logger.info(f"Added environmental constraint: {constraint.constraint_id}")

    def get_prompt_performance_analytics(self) -> Dict[str, Any]:
        """Get analytics on prompt engineering performance."""
        if not self.prompt_performance_history:
            return {"error": "No performance data available"}

        # Calculate average metrics
        total_prompts = len(self.prompt_performance_history)

        avg_directive_coverage = sum(p["directive_coverage"] for p in self.prompt_performance_history) / total_prompts
        avg_constraint_compliance = sum(p["constraint_compliance"] for p in self.prompt_performance_history) / total_prompts
        avg_context_relevance = sum(p["context_relevance"] for p in self.prompt_performance_history) / total_prompts
        avg_effectiveness = sum(p["estimated_effectiveness"] for p in self.prompt_performance_history) / total_prompts

        # Identify trends
        recent_performance = self.prompt_performance_history[-10:] if len(self.prompt_performance_history) >= 10 else self.prompt_performance_history
        recent_effectiveness = sum(p["estimated_effectiveness"] for p in recent_performance) / len(recent_performance)

        trend = "improving" if recent_effectiveness > avg_effectiveness else "declining" if recent_effectiveness < avg_effectiveness else "stable"

        return {
            "total_prompts_engineered": total_prompts,
            "average_metrics": {
                "directive_coverage": avg_directive_coverage,
                "constraint_compliance": avg_constraint_compliance,
                "context_relevance": avg_context_relevance,
                "estimated_effectiveness": avg_effectiveness
            },
            "performance_trend": trend,
            "recent_effectiveness": recent_effectiveness,
            "improvement_suggestions": self._generate_system_improvements()
        }

    def _generate_system_improvements(self) -> List[str]:
        """Generate suggestions for improving the prompting system."""
        suggestions = []

        if not self.prompt_performance_history:
            return ["Collect performance data to enable improvement suggestions"]

        # Analyze performance patterns
        low_performers = [p for p in self.prompt_performance_history if p["estimated_effectiveness"] < 0.6]

        if len(low_performers) > len(self.prompt_performance_history) * 0.3:
            suggestions.append("Review directive and constraint selection logic")

        # Check for missing directive categories
        used_categories = set()
        for p in self.prompt_performance_history:
            for directive in p.get("directives_used", []):
                used_categories.add(directive.get("category", ""))

        missing_categories = set(["reasoning", "communication", "decision_making", "error_handling"]) - used_categories

        if missing_categories:
            suggestions.append(f"Consider adding directives for missing categories: {', '.join(missing_categories)}")

        return suggestions

    def _get_current_time(self) -> str:
        """Get current time formatted."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _assess_task_complexity(self, context: Dict[str, Any]) -> str:
        """Assess task complexity from context."""
        complexity_indicators = context.get("complexity_indicators", {})

        # Simple complexity assessment
        if complexity_indicators.get("steps", 0) > 5:
            return "high"
        elif complexity_indicators.get("dependencies", 0) > 3:
            return "medium"
        else:
            return "low"

    def validate_prompt_effectiveness(self, engineered_prompt: str, expected_outcomes: List[str]) -> Dict[str, Any]:
        """Validate the effectiveness of an engineered prompt."""
        validation = {
            "prompt_length": len(engineered_prompt),
            "directive_count": engineered_prompt.count("- "),
            "constraint_count": engineered_prompt.count("CONSTRAINTS:"),
            "context_variables": len(re.findall(r'-\s+\w+:', engineered_prompt)),
            "validation_criteria": len(expected_outcomes),
            "completeness_score": 0.0,
            "effectiveness_assessment": "unknown"
        }

        # Calculate completeness based on expected components
        expected_components = ["BEHAVIORAL DIRECTIVES", "ENVIRONMENTAL CONSTRAINTS", "CONTEXT", "TASK", "VALIDATION CRITERIA"]
        present_components = sum(1 for component in expected_components if component in engineered_prompt)

        validation["completeness_score"] = present_components / len(expected_components)

        # Assess effectiveness
        if validation["completeness_score"] >= 0.8:
            validation["effectiveness_assessment"] = "high"
        elif validation["completeness_score"] >= 0.6:
            validation["effectiveness_assessment"] = "medium"
        else:
            validation["effectiveness_assessment"] = "low"

        return validation

    def export_prompt_framework(self) -> Dict[str, Any]:
        """Export the current prompt engineering framework."""
        return {
            "behavioral_directives": {
                did: {
                    "category": directive.category,
                    "description": directive.description,
                    "priority": directive.priority
                }
                for did, directive in self.behavioral_directives.items()
            },
            "environmental_constraints": {
                cid: {
                    "constraint_type": constraint.constraint_type,
                    "description": constraint.description,
                    "enforcement": constraint.enforcement
                }
                for cid, constraint in self.environmental_constraints.items()
            },
            "framework_metadata": {
                "total_directives": len(self.behavioral_directives),
                "total_constraints": len(self.environmental_constraints),
                "export_timestamp": self._get_current_time()
            }
        }

    def import_prompt_framework(self, framework_data: Dict[str, Any]) -> None:
        """Import prompt engineering framework from external source."""
        # Import behavioral directives
        directives_data = framework_data.get("behavioral_directives", {})
        for directive_id, directive_info in directives_data.items():
            directive = BehavioralDirective(
                directive_id=directive_id,
                category=directive_info["category"],
                description=directive_info["description"],
                priority=directive_info["priority"]
            )
            self.behavioral_directives[directive_id] = directive

        # Import environmental constraints
        constraints_data = framework_data.get("environmental_constraints", {})
        for constraint_id, constraint_info in constraints_data.items():
            constraint = EnvironmentalConstraint(
                constraint_id=constraint_id,
                constraint_type=constraint_info["constraint_type"],
                description=constraint_info["description"],
                enforcement=constraint_info["enforcement"]
            )
            self.environmental_constraints[constraint_id] = constraint

        logger.info(f"Imported framework: {len(directives_data)} directives, {len(constraints_data)} constraints")

    def create_agent_specific_prompt(self, agent_type: str, task_context: Dict[str, Any]) -> ContextualPrompt:
        """Create a prompt specifically tailored for a particular agent type."""
        # Base prompt for agent-specific context
        base_prompt = f"You are a {agent_type} agent. {task_context.get('task_description', 'Please perform the requested task.')}"

        # Agent-specific context
        agent_context = {
            "agent_type": agent_type,
            "specialization": self._get_agent_specialization(agent_type),
            "communication_style": self._get_agent_communication_style(agent_type),
            "reasoning_approach": self._get_agent_reasoning_approach(agent_type)
        }

        # Merge with task context
        full_context = {**agent_context, **task_context}

        return self.create_contextual_prompt(base_prompt, full_context)

    def _get_agent_specialization(self, agent_type: str) -> str:
        """Get specialization for agent type."""
        specializations = {
            "code_generator": "software_development",
            "tester": "quality_assurance",
            "documenter": "technical_writing",
            "analyzer": "system_analysis",
            "debugger": "problem_solving"
        }

        return specializations.get(agent_type, "general_assistance")

    def _get_agent_communication_style(self, agent_type: str) -> str:
        """Get communication style for agent type."""
        styles = {
            "code_generator": "technical_detailed",
            "tester": "precise_systematic",
            "documenter": "clear_structured",
            "analyzer": "analytical_comprehensive",
            "debugger": "diagnostic_methodical"
        }

        return styles.get(agent_type, "balanced_professional")

    def _get_agent_reasoning_approach(self, agent_type: str) -> str:
        """Get reasoning approach for agent type."""
        approaches = {
            "code_generator": "implementation_focused",
            "tester": "verification_centered",
            "documenter": "clarity_driven",
            "analyzer": "evidence_based",
            "debugger": "diagnostic_systematic"
        }

        return approaches.get(agent_type, "balanced_reasoning")
