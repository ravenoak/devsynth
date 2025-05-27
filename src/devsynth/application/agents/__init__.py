
"""
Agent module for the DevSynth system.
"""

from .base import BaseAgent
from .planner import PlannerAgent
from .specification import SpecificationAgent
from .test import TestAgent
from .code import CodeAgent
from .validation import ValidationAgent
from .refactor import RefactorAgent
from .documentation import DocumentationAgent
from .diagram import DiagramAgent
from .critic import CriticAgent
from .agent_memory_integration import AgentMemoryIntegration
from .wsde_memory_integration import WSDEMemoryIntegration

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

__all__ = [
    'BaseAgent',
    'PlannerAgent',
    'SpecificationAgent',
    'TestAgent',
    'CodeAgent',
    'ValidationAgent',
    'RefactorAgent',
    'DocumentationAgent',
    'DiagramAgent',
    'CriticAgent',
    'AgentMemoryIntegration',
    'WSDEMemoryIntegration'
]
