"""
Examples of using the Promise System in DevSynth.

This module provides concrete examples of how to use the Promise System
for capability declaration, discovery, and fulfillment between agents.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from devsynth.application.promises import (
    CapabilityNotFoundError,
    Promise,
    PromiseAgent,
    PromiseBroker,
    UnauthorizedAccessError,
)
from devsynth.logging_setup import DevSynthLogger

# Setup logger
logger = DevSynthLogger(__name__)


class MathAgent(PromiseAgent):
    """
    Example agent that provides math capabilities.
    """

    def __init__(
        self, agent_id: str = "math_agent", broker: Optional[PromiseBroker] = None
    ):
        """Initialize the Math Agent."""
        super().__init__(agent_id, broker)

        # Register capabilities
        self.register_capability(
            name="add",
            handler_func=self.add_numbers,
            description="Add two numbers together",
            parameters={"a": "float", "b": "float"},
        )

        self.register_capability(
            name="subtract",
            handler_func=self.subtract_numbers,
            description="Subtract one number from another",
            parameters={"a": "float", "b": "float"},
        )

        self.register_capability(
            name="multiply",
            handler_func=self.multiply_numbers,
            description="Multiply two numbers together",
            parameters={"a": "float", "b": "float"},
        )

        self.register_capability(
            name="divide",
            handler_func=self.divide_numbers,
            description="Divide one number by another",
            parameters={"a": "float", "b": "float"},
        )

        logger.info(
            f"Math Agent initialized with {len(self.get_own_capabilities())} capabilities"
        )

    def add_numbers(self, a: float, b: float) -> float:
        """Add two numbers together."""
        result = a + b
        logger.debug(f"Adding {a} + {b} = {result}")
        return result

    def subtract_numbers(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = a - b
        logger.debug(f"Subtracting {a} - {b} = {result}")
        return result

    def multiply_numbers(self, a: float, b: float) -> float:
        """Multiply two numbers together."""
        result = a * b
        logger.debug(f"Multiplying {a} * {b} = {result}")
        return result

    def divide_numbers(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            logger.error("Division by zero attempted")
            raise ZeroDivisionError("Cannot divide by zero")
        result = a / b
        logger.debug(f"Dividing {a} / {b} = {result}")
        return result


class TextAgent(PromiseAgent):
    """
    Example agent that provides text processing capabilities.
    """

    def __init__(
        self, agent_id: str = "text_agent", broker: Optional[PromiseBroker] = None
    ):
        """Initialize the Text Agent."""
        super().__init__(agent_id, broker)

        # Register capabilities
        self.register_capability(
            name="concatenate",
            handler_func=self.concatenate_texts,
            description="Concatenate multiple strings",
            parameters={"texts": "List[str]", "separator": "str"},
        )

        self.register_capability(
            name="reverse",
            handler_func=self.reverse_text,
            description="Reverse a string",
            parameters={"text": "str"},
        )

        self.register_capability(
            name="tokenize",
            handler_func=self.tokenize_text,
            description="Split text into tokens",
            parameters={"text": "str", "delimiter": "str"},
        )

        logger.info(
            f"Text Agent initialized with {len(self.get_own_capabilities())} capabilities"
        )

    def concatenate_texts(self, texts: List[str], separator: str = " ") -> str:
        """Concatenate multiple strings with a separator."""
        result = separator.join(texts)
        logger.debug(f"Concatenated {len(texts)} texts with separator '{separator}'")
        return result

    def reverse_text(self, text: str) -> str:
        """Reverse a string."""
        result = text[::-1]
        logger.debug(f"Reversed text: '{text}' -> '{result}'")
        return result

    def tokenize_text(self, text: str, delimiter: str = " ") -> List[str]:
        """Split text into tokens using the delimiter."""
        tokens = text.split(delimiter)
        logger.debug(
            f"Tokenized text into {len(tokens)} tokens using delimiter '{delimiter}'"
        )
        return tokens


class ProjectAgent(PromiseAgent):
    """
    Example agent that manages a project and orchestrates other agents.
    """

    def __init__(
        self, agent_id: str = "project_agent", broker: Optional[PromiseBroker] = None
    ):
        """Initialize the Project Agent."""
        super().__init__(agent_id, broker)

        # Register capabilities
        self.register_capability(
            name="create_project",
            handler_func=self.create_project,
            description="Create a new project",
            parameters={"name": "str", "description": "str"},
        )

        self.register_capability(
            name="analyze_requirements",
            handler_func=self.analyze_requirements,
            description="Analyze project requirements",
            parameters={"requirements": "str"},
        )

        logger.info(
            f"Project Agent initialized with {len(self.get_own_capabilities())} capabilities"
        )

    def create_project(self, name: str, description: str) -> Dict[str, Any]:
        """Create a new project."""
        logger.info(f"Creating project: {name}")

        # Simulate project creation
        project = {
            "name": name,
            "description": description,
            "created_at": time.time(),
            "status": "active",
        }

        return project

    def analyze_requirements(self, requirements: str) -> Dict[str, Any]:
        """Analyze project requirements using other agents' capabilities."""
        logger.info("Analyzing requirements")

        # Get available capabilities
        available_capabilities = self.get_available_capabilities()
        capability_names = [cap["name"] for cap in available_capabilities]
        logger.debug(f"Available capabilities: {capability_names}")

        # Use text agent to tokenize requirements
        try:
            tokenize_promise = self.request_capability(
                name="tokenize", text=requirements, delimiter="\n"
            )
            req_lines = self.wait_for_capability(tokenize_promise)
            logger.debug(f"Tokenized requirements into {len(req_lines)} lines")
        except CapabilityNotFoundError:
            logger.warning("Tokenize capability not available, using fallback")
            req_lines = requirements.split("\n")

        # Count requirements
        count = len([line for line in req_lines if line.strip()])

        # Create analysis result
        analysis = {
            "total_requirements": count,
            "lines": req_lines,
            "analyzed_at": time.time(),
        }

        return analysis


def run_example():
    """Run an example workflow using the Promise System."""
    # Create a shared broker for all agents
    broker = PromiseBroker()

    # Create the agents
    math_agent = MathAgent(broker=broker)
    text_agent = TextAgent(broker=broker)
    project_agent = ProjectAgent(broker=broker)

    # Start agent processing (in a real system, these would run in separate threads or processes)
    logger.info("Starting example workflow")

    # Have each agent handle pending capabilities
    def process_all_agents():
        """Process pending capabilities for all agents."""
        math_handled = math_agent.handle_pending_capabilities()
        text_handled = text_agent.handle_pending_capabilities()
        project_handled = project_agent.handle_pending_capabilities()
        return math_handled + text_handled + project_handled

    # Step 1: Create a new project
    create_promise = project_agent.request_capability(
        name="create_project", description="A demonstration of the Promise System"
    )
    process_all_agents()

    project_info = create_promise.value
    logger.info(f"Created project: {project_info['name']}")

    # Step 2: Use math capabilities
    add_promise = math_agent.request_capability(name="add", a=5, b=7)
    multiply_promise = math_agent.request_capability(name="multiply", a=3, b=4)
    process_all_agents()

    add_result = add_promise.value
    multiply_result = multiply_promise.value
    logger.info(f"Math results: 5 + 7 = {add_result}, 3 * 4 = {multiply_result}")

    # Step 3: Use text capabilities
    concat_promise = text_agent.request_capability(
        name="concatenate", texts=["Hello", "Promise", "System"], separator=", "
    )
    process_all_agents()

    concat_result = concat_promise.value
    logger.info(f"Concatenation result: {concat_result}")

    # Step 4: Analyze project requirements
    requirements = """
    Requirement 1: The system shall provide math capabilities.
    Requirement 2: The system shall provide text processing capabilities.
    Requirement 3: The system shall support capability discovery.
    Requirement 4: The system shall handle errors gracefully.
    """

    analyze_promise = project_agent.request_capability(
        name="analyze_requirements", requirements=requirements
    )
    process_all_agents()

    analysis = analyze_promise.value
    logger.info(f"Analyzed {analysis['total_requirements']} requirements")

    # All done!
    logger.info("Example workflow completed successfully!")
    return {
        "project": project_info,
        "math_results": {"addition": add_result, "multiplication": multiply_result},
        "text_results": {"concatenation": concat_result},
        "requirements_analysis": analysis,
    }


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the example
    result = run_example()
    logger.info("Example Result:")
    logger.info("Project: %s", result["project"]["name"])
    logger.info("Math Results: %s", result["math_results"])
    logger.info("Text Results: %s", result["text_results"])
    logger.info(
        "Requirements Analysis: %s requirements",
        result["requirements_analysis"]["total_requirements"],
    )
