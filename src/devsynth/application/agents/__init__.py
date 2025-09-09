"""
Agent module for the DevSynth system.
"""

from devsynth.logging_setup import DevSynthLogger

from .agent_memory_integration import AgentMemoryIntegration
from .base import BaseAgent
from .code import CodeAgent
from .critic import CriticAgent
from .diagram import DiagramAgent
from .documentation import DocumentationAgent
from .multi_language_code import MultiLanguageCodeAgent
from .planner import PlannerAgent
from .refactor import RefactorAgent
from .specification import SpecificationAgent
from .test import TestAgent
from .validation import ValidationAgent
from .wsde_memory_integration import WSDEMemoryIntegration

# Module logger
logger = DevSynthLogger(__name__)

__all__ = [
    "BaseAgent",
    "PlannerAgent",
    "SpecificationAgent",
    "TestAgent",
    "CodeAgent",
    "MultiLanguageCodeAgent",
    "ValidationAgent",
    "RefactorAgent",
    "DocumentationAgent",
    "DiagramAgent",
    "CriticAgent",
    "AgentMemoryIntegration",
    "WSDEMemoryIntegration",
]
