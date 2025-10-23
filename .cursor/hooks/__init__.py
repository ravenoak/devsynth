"""
Cursor Hooks System for Self-Improvement

This package provides comprehensive self-improvement capabilities for Cursor IDE,
including dynamic rule management, automated improvement detection, and
learning systems that evolve based on usage patterns.

Main Components:
- hook_manager: Core hook system and improvement suggestions
- auto_rule_generator: Automated rule generation from codebase analysis
- pattern_learner: Pattern detection and learning from development sessions
- rule_validator: Rule validation and quality improvement
- analytics_monitor: Usage analytics and performance monitoring
- self_improvement_orchestrator: Main orchestrator coordinating all systems

Usage:
    from hook_manager import get_hook_manager, trigger_hook
    from self_improvement_orchestrator import run_full_improvement_analysis

    # Trigger a hook
    trigger_hook(HookEvent.CODE_GENERATED, code_snippet=code, file_path=path)

    # Run improvement analysis
    results = run_full_improvement_analysis()
"""

from hook_manager import (
    HookManager, HookEvent, HookContext, ImprovementSuggestion,
    get_hook_manager, trigger_hook, create_hook_context
)

from auto_rule_generator import (
    analyze_and_suggest_rules, CodebaseAnalyzer, RuleGenerator
)

from pattern_learner import (
    LearningEngine, trigger_learning_event, get_learning_insights
)

from rule_validator import (
    generate_health_report, validate_all_rules, RuleValidationResult
)

from analytics_monitor import (
    get_system_analytics, record_rule_usage, record_command_usage
)

from self_improvement_orchestrator import (
    SelfImprovementOrchestrator, run_full_improvement_analysis,
    get_improvement_dashboard, trigger_continuous_improvement
)

__version__ = "1.0.0"
__all__ = [
    # Hook management
    "HookManager", "HookEvent", "HookContext", "ImprovementSuggestion",
    "get_hook_manager", "trigger_hook", "create_hook_context",

    # Rule generation
    "analyze_and_suggest_rules", "CodebaseAnalyzer", "RuleGenerator",

    # Learning
    "LearningEngine", "trigger_learning_event", "get_learning_insights",

    # Validation
    "generate_health_report", "validate_all_rules", "RuleValidationResult",

    # Analytics
    "get_system_analytics", "record_rule_usage", "record_command_usage",

    # Orchestration
    "SelfImprovementOrchestrator", "run_full_improvement_analysis",
    "get_improvement_dashboard", "trigger_continuous_improvement"
]
