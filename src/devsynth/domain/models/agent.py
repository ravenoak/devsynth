
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class AgentType(Enum):
    """Types of agents in the DevSynth system."""
    # MVP agent type
    ORCHESTRATOR = "orchestrator"  # Single unified agent for MVP
    
    # Future agent types (retained for future multi-agent implementation)
    # These are commented in the enum definition but kept as values for backward compatibility
    PLANNER = "planner"
    CODER = "coder"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DOCUMENTER = "documenter"
    
    # Original types (retained for backward compatibility)
    SPECIFICATION = "specification"
    TEST = "test"
    CODE = "code"
    VALIDATION = "validation"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    DIAGRAM = "diagram"
    CRITIC = "critic"

@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    agent_type: AgentType
    description: str
    capabilities: List[str]
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

# Define MVP capabilities
MVP_CAPABILITIES = [
    "initialize_project",
    "parse_requirements",
    "generate_specification",
    "generate_tests",
    "generate_code",
    "validate_implementation",
    "track_token_usage"
]

# Define future capabilities
FUTURE_CAPABILITIES = [
    "refactor_code",
    "optimize_code",
    "security_analysis",
    "generate_diagrams",
    "generate_comprehensive_documentation",
    "code_review",
    "style_checking",
    "best_practice_enforcement",
    "multi_agent_collaboration"
]
