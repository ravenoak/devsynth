"""
Unified agent for the DevSynth system MVP.

This agent combines the essential capabilities from specialized agents
into a single agent that can handle all MVP tasks.
"""

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
import os
from typing import Any, Dict, List, Union

from devsynth.exceptions import DevSynthError

from ...domain.models.agent import AgentConfig, AgentType
from ..prompts.auto_tuning import BasicPromptTuner
from .base import BaseAgent

# Define MVP capabilities
MVP_CAPABILITIES = [
    "initialize_project",
    "parse_requirements",
    "generate_specification",
    "generate_tests",
    "generate_code",
    "validate_implementation",
    "track_token_usage",
]


class UnifiedAgent(BaseAgent):
    """
    Unified agent that handles all core MVP capabilities.

    This agent combines functionality from specialized agents (Specification, Test, Code, etc.)
    into a single agent for the MVP. It preserves extension points for future multi-agent capabilities.
    """

    def __init__(
        self,
        name: str | None = None,
        agent_type: AgentType = AgentType.ORCHESTRATOR,
        config: AgentConfig | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.prompt_tuner = BasicPromptTuner()

        if config is None:
            config = AgentConfig(
                name=name or self.__class__.__name__,
                agent_type=agent_type,
                description="",
                capabilities=[],
            )
        else:
            if name is not None:
                config.name = name
            config.agent_type = agent_type

        self.initialize(config)

    def record_prompt_feedback(
        self,
        success: bool | None = None,
        feedback_score: float | None = None,
    ) -> None:
        """Record feedback used for tuning future prompts."""
        self.prompt_tuner.adjust(success, feedback_score)

    def generate_text(
        self, prompt: str, parameters: dict[str, Any] | None = None
    ) -> str:
        params = self.prompt_tuner.parameters()
        if parameters:
            params.update(parameters)
        return super().generate_text(prompt, params)

    def generate_text_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] | None = None,
    ) -> str:
        params = self.prompt_tuner.parameters()
        if parameters:
            params.update(parameters)
        return super().generate_text_with_context(prompt, context, params)

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and produce outputs based on the requested task."""
        # Get the task type from inputs
        task_type = inputs.get("task_type", "")

        # Process the task based on its type
        if task_type == "specification":
            return self._process_specification_task(inputs)
        elif task_type == "test":
            return self._process_test_task(inputs)
        elif task_type == "code":
            return self._process_code_task(inputs)
        elif task_type == "validation":
            return self._process_validation_task(inputs)
        elif task_type == "documentation":
            return self._process_documentation_task(inputs)
        elif task_type == "project_initialization":
            return self._process_project_initialization_task(inputs)
        elif task_type == "analyze" or task_type == "requirement_analyzer":
            return self._process_analyze_task(inputs)
        else:
            # Default processing if task type is not specified
            return self._process_generic_task(inputs)

    def _process_specification_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process a specification generation task."""
        # Create a prompt for the LLM
        prompt = f"""
        You are a specification expert. Your task is to generate a detailed specification
        based on the provided requirements.

        Requirements:
        {inputs.get('requirements', '')}

        Project context:
        {inputs.get('context', '')}

        Generate a detailed specification document that includes:
        1. Overview
        2. Functional requirements
        3. Non-functional requirements
        4. API definitions
        5. Data models
        6. Constraints and assumptions
        """

        # Generate the specification using the LLM
        specification = self.generate_text(prompt)

        # If the LLM is not available, generate a simple specification
        if specification.startswith("Placeholder text") or specification.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback specification generation")
            specification = f"Specification (created by {self.name})"

        # Create a WSDE with the specification
        spec_wsde = self.create_wsde(
            content=specification,
            content_type="text",
            metadata={"agent": self.name, "type": "specification"},
        )

        return {"specification": specification, "wsde": spec_wsde, "agent": self.name}

    def _process_test_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process a test generation task."""
        # Extract test framework from inputs or default to pytest
        test_framework = inputs.get("test_framework", "pytest").lower()

        # Extract programming language from inputs or default to Python
        language = inputs.get("language", "python").lower()

        # Create a prompt for the LLM with enhanced guidance
        prompt = f"""
        You are an expert in software testing with deep knowledge of test-driven development and
        comprehensive test strategies. Your task is to generate high-quality tests based on the
        provided specification.

        Specification:
        {inputs.get('specification', '')}

        Project context:
        {inputs.get('context', '')}

        Testing framework: {test_framework}
        Programming language: {language}

        Please follow these guidelines when creating tests:

        1. Test Structure and Organization:
           - Organize tests logically with clear test class/module structure
           - Use descriptive test names that explain what is being tested
           - Group related tests together
           - Follow the Arrange-Act-Assert (AAA) pattern for test clarity

        2. Test Coverage:
           - Unit tests for individual components/functions
           - Integration tests for component interactions
           - Functional tests for end-to-end behavior
           - Edge case tests for boundary conditions
           - Negative tests for error handling and invalid inputs

        3. Test Quality:
           - Each test should have a single, clear assertion/purpose
           - Tests should be independent and not rely on other tests
           - Use appropriate assertions for different types of checks
           - Include setup and teardown code where necessary
           - Add clear comments explaining complex test scenarios

        4. Advanced Testing Techniques:
           - Parameterized tests for testing multiple inputs
           - Property-based tests where appropriate
           - Mocking and stubbing for isolating components
           - Fixtures for reusable test setup
           - Test data generators for comprehensive input coverage

        5. Test Documentation:
           - Include docstrings explaining the purpose of test classes/functions
           - Document test assumptions and prerequisites
           - Explain the rationale behind complex test scenarios
           - Use type hints where appropriate

        Specific guidance for {test_framework}:
        """

        # Add framework-specific guidance
        if test_framework == "pytest":
            prompt += """
           - Use pytest fixtures for setup and teardown
           - Leverage pytest's parameterize decorator for multiple test cases
           - Use pytest.mark for categorizing tests
           - Utilize pytest's built-in assertions for readable tests
           - Implement conftest.py for shared fixtures when appropriate
        """
        elif test_framework == "unittest":
            prompt += """
           - Use setUp and tearDown methods for test preparation and cleanup
           - Extend unittest.TestCase for test classes
           - Use the various assert* methods provided by unittest
           - Group related tests in test suites
           - Use subTest for parameterized testing
        """
        elif test_framework == "behave" or test_framework == "cucumber":
            prompt += """
           - Write tests in Gherkin syntax (Given-When-Then)
           - Create clear, reusable step definitions
           - Organize features by business functionality
           - Use scenario outlines for parameterized tests
           - Include descriptive feature and scenario descriptions
        """

        prompt += f"""
        Generate comprehensive tests that thoroughly validate the specification, catch potential bugs,
        and serve as documentation for how the code should behave. The tests should be production-ready,
        maintainable, and follow best practices for {test_framework} and {language}.
        """

        # Generate the tests using the LLM
        tests = self.generate_text(prompt)

        # If the LLM is not available, generate simple tests
        if tests.startswith("Placeholder text") or tests.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback test generation")
            tests = f"Tests (created by {self.name})"

        # Create a WSDE with the tests
        tests_wsde = self.create_wsde(
            content=tests,
            content_type="code",
            metadata={
                "agent": self.name,
                "type": "tests",
                "test_framework": test_framework,
                "language": language,
            },
        )

        return {"tests": tests, "wsde": tests_wsde, "agent": self.name}

    def _process_code_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process a code generation task."""
        # Extract programming language from inputs or default to Python
        language = inputs.get("language", "python").lower()

        # Determine the programming paradigm (OOP, functional, etc.)
        paradigm = inputs.get("paradigm", "object_oriented").lower()

        # Create a prompt for the LLM with enhanced guidance
        prompt = f"""
        You are an expert software engineer specializing in clean, maintainable, and robust code.
        Your task is to implement high-quality code based on the provided tests and specifications.

        Specification:
        {inputs.get('specification', '')}

        Tests:
        {inputs.get('tests', '')}

        Project context:
        {inputs.get('context', '')}

        Programming language: {language}
        Programming paradigm: {paradigm}

        Please follow these guidelines when implementing the code:

        1. Code Structure and Organization:
           - Use clear, descriptive names for classes, methods, and variables
           - Follow the single responsibility principle for classes and functions
           - Organize code logically with related functionality grouped together
           - Use appropriate design patterns when applicable

        2. Error Handling and Edge Cases:
           - Implement comprehensive error handling for all operations
           - Validate inputs and handle edge cases gracefully
           - Use appropriate exception types and provide informative error messages
           - Consider boundary conditions and handle them appropriately

        3. Performance and Efficiency:
           - Write efficient code that avoids unnecessary operations
           - Consider time and space complexity for algorithms
           - Avoid redundant computations and optimize where appropriate
           - Use appropriate data structures for the task

        4. Documentation and Readability:
           - Include clear docstrings for all classes and methods
           - Add inline comments for complex logic
           - Use type hints where appropriate
           - Ensure the code is readable and follows language conventions

        5. Testing and Maintainability:
           - Ensure the code passes all the provided tests
           - Make the code easily testable and maintainable
           - Consider future extensions and make the code flexible
           - Follow SOLID principles for object-oriented code

        Implement code that not only passes the tests and meets the specifications but is also
        production-ready, maintainable, and follows best practices for {language} development.
        """

        # Generate the code using the LLM
        code = self.generate_text(prompt)

        # If the LLM is not available, generate simple code
        if code.startswith("Placeholder text") or code.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback code generation")
            code = f"Code (created by {self.name})"

        # Create a WSDE with the code
        code_wsde = self.create_wsde(
            content=code,
            content_type="code",
            metadata={
                "agent": self.name,
                "type": "code",
                "language": language,
                "paradigm": paradigm,
            },
        )

        return {"code": code, "wsde": code_wsde, "agent": self.name}

    def _process_validation_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process a validation task."""
        # Create a prompt for the LLM
        prompt = f"""
        You are a validation expert. Your task is to validate the implementation against
        the requirements and specifications.

        Requirements:
        {inputs.get('requirements', '')}

        Specification:
        {inputs.get('specification', '')}

        Implementation:
        {inputs.get('implementation', '')}

        Tests:
        {inputs.get('tests', '')}

        Validate that the implementation meets the requirements and specifications.
        """

        # Generate the validation using the LLM
        validation = self.generate_text(prompt)

        # If the LLM is not available, generate a simple validation
        if validation.startswith("Placeholder text") or validation.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback validation generation")
            validation = f"Validation (created by {self.name})"

        # Create a WSDE with the validation
        validation_wsde = self.create_wsde(
            content=validation,
            content_type="text",
            metadata={"agent": self.name, "type": "validation"},
        )

        return {"validation": validation, "wsde": validation_wsde, "agent": self.name}

    def _process_documentation_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process a documentation generation task."""
        # Extract documentation format from inputs or default to Markdown
        doc_format = inputs.get("doc_format", "markdown").lower()

        # Extract documentation type from inputs or default to comprehensive
        doc_type = inputs.get("doc_type", "comprehensive").lower()

        # Extract programming language from inputs or default to Python
        language = inputs.get("language", "python").lower()

        # Create a prompt for the LLM with enhanced guidance
        prompt = f"""
        You are an expert technical writer with deep knowledge of software documentation best practices.
        Your task is to generate high-quality documentation for the provided code and specifications.

        Specification:
        {inputs.get('specification', '')}

        Code:
        {inputs.get('code', '')}

        Project context:
        {inputs.get('context', '')}

        Documentation format: {doc_format}
        Documentation type: {doc_type}
        Programming language: {language}

        Please follow these guidelines when creating documentation:

        1. Documentation Structure and Organization:
           - Use clear, logical organization with appropriate headings and sections
           - Start with a concise overview that explains the purpose and scope
           - Use consistent formatting and style throughout
           - Include a table of contents for longer documents
           - Organize content from general to specific

        2. Content Quality:
           - Write clear, concise explanations avoiding jargon when possible
           - Use examples to illustrate concepts and usage
           - Include diagrams or visual aids where appropriate
           - Address both beginner and advanced users' needs
           - Provide troubleshooting information for common issues

        3. API Documentation:
           - Document all public classes, methods, functions, and parameters
           - Include return types and possible exceptions/errors
           - Provide example usage for each API element
           - Explain the purpose and behavior of each component
           - Document any side effects or important considerations

        4. User-Focused Content:
           - Include step-by-step tutorials for common tasks
           - Provide installation and setup instructions
           - Document configuration options and customization
           - Include a quick start guide for new users
           - Add a FAQ section addressing common questions

        5. Documentation Maintenance:
           - Include version information and change history
           - Note any deprecated features or upcoming changes
           - Provide links to related resources or further reading
           - Ensure documentation is consistent with the current code
           - Include contact information or contribution guidelines
        """

        # Add format-specific guidance
        if doc_format == "markdown":
            prompt += """
        Markdown-Specific Guidelines:
           - Use # for main headings, ## for subheadings, etc.
           - Use backticks for inline code and triple backticks for code blocks
           - Use > for blockquotes and notes
           - Use * or - for unordered lists and 1. 2. for ordered lists
           - Use [text](url) for links and ![alt text](url) for images
           - Use tables with | and - for structured data
           - Use --- for horizontal rules to separate sections
           - Use appropriate syntax highlighting for code blocks
        """
        elif doc_format == "restructuredtext" or doc_format == "rst":
            prompt += """
        reStructuredText-Specific Guidelines:
           - Use === for main headings, --- for subheadings, etc.
           - Use :: for code blocks with appropriate indentation
           - Use `` for inline code
           - Use * for unordered lists and 1. for ordered lists
           - Use `text <url>`_ for links
           - Use .. image:: url for images
           - Use .. note:: and .. warning:: for admonitions
           - Use .. code-block:: language for syntax highlighting
           - Use proper directives for tables and other elements
        """
        elif doc_format == "html":
            prompt += """
        HTML-Specific Guidelines:
           - Use proper HTML5 semantic elements (<header>, <section>, <nav>, etc.)
           - Use <h1> for main headings, <h2> for subheadings, etc.
           - Use <pre> and <code> for code blocks with appropriate CSS
           - Use <ul> and <ol> for lists
           - Use <a href="url"> for links and <img src="url"> for images
           - Use <table> for structured data
           - Use CSS classes for consistent styling
           - Ensure the HTML is valid and accessible
        """

        # Add type-specific guidance
        if doc_type == "user_guide":
            prompt += """
        User Guide-Specific Guidelines:
           - Focus on how to use the software from a user's perspective
           - Include screenshots or illustrations of the user interface
           - Provide step-by-step instructions for common tasks
           - Explain concepts in non-technical terms
           - Include troubleshooting information and FAQs
           - Organize content based on user workflows
        """
        elif doc_type == "api_reference":
            prompt += """
        API Reference-Specific Guidelines:
           - Focus on comprehensive coverage of all API elements
           - Organize by modules, classes, and functions
           - Include signature, parameters, return values, and exceptions
           - Provide code examples for each API element
           - Document type information and constraints
           - Include cross-references between related API elements
           - Note any performance considerations or limitations
        """
        elif doc_type == "developer_guide":
            prompt += """
        Developer Guide-Specific Guidelines:
           - Focus on how to extend or modify the software
           - Explain the architecture and design patterns
           - Document the build system and development environment
           - Include contribution guidelines and coding standards
           - Provide examples of extending the software
           - Explain internal APIs and implementation details
           - Include testing and debugging information
        """

        prompt += f"""
        Generate comprehensive, well-structured documentation that serves as a valuable resource for users
        and developers. The documentation should be clear, accurate, and follow best practices for
        {doc_format} format and {language} documentation.
        """

        # Generate the documentation using the LLM
        documentation = self.generate_text(prompt)

        # If the LLM is not available, generate simple documentation
        if documentation.startswith("Placeholder text") or documentation.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback documentation generation")
            documentation = f"Documentation (created by {self.name})"

        # Create a WSDE with the documentation
        doc_wsde = self.create_wsde(
            content=documentation,
            content_type="text",
            metadata={
                "agent": self.name,
                "type": "documentation",
                "doc_format": doc_format,
                "doc_type": doc_type,
                "language": language,
            },
        )

        return {"documentation": documentation, "wsde": doc_wsde, "agent": self.name}

    def _process_project_initialization_task(
        self, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a project initialization task."""
        # Create a prompt for the LLM
        prompt = f"""
        You are a project initialization expert. Your task is to set up the initial
        project structure and configuration.

        Project name:
        {inputs.get('project_name', '')}

        Project type:
        {inputs.get('project_type', 'python')}

        Project context:
        {inputs.get('context', '')}

        Generate the initial project structure and configuration files.
        """

        # Generate the project structure using the LLM
        project_structure = self.generate_text(prompt)

        # If the LLM is not available, generate a simple project structure
        if project_structure.startswith(
            "Placeholder text"
        ) or project_structure.startswith("Error generating text"):
            logger.warning("Using fallback project structure generation")
            project_structure = f"Project structure (created by {self.name})"

        # Create a WSDE with the project structure
        structure_wsde = self.create_wsde(
            content=project_structure,
            content_type="text",
            metadata={"agent": self.name, "type": "project_structure"},
        )

        return {
            "project_structure": project_structure,
            "wsde": structure_wsde,
            "agent": self.name,
        }

    def _process_generic_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process a generic task without a specific type."""
        # Create a prompt for the LLM
        prompt = f"""
        You are a DevSynth agent. Your task is to process the provided inputs and
        generate appropriate outputs.

        Inputs:
        {inputs}

        Process the inputs and generate appropriate outputs.
        """

        # Generate the result using the LLM
        result = self.generate_text(prompt)

        # If the LLM is not available, generate a simple result
        if result.startswith("Placeholder text") or result.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback result generation")
            result = f"Result (created by {self.name})"

        # Create a WSDE with the result
        result_wsde = self.create_wsde(
            content=result,
            content_type="text",
            metadata={"agent": self.name, "type": "generic"},
        )

        return {"result": result, "wsde": result_wsde, "agent": self.name}

    def _process_analyze_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process a requirements analysis task."""
        # Get the requirements from the input file or interactive session
        requirements = ""
        if "input" in inputs:
            try:
                with open(inputs["input"]) as f:
                    requirements = f.read()
                logger.info(f"Read requirements from {inputs['input']}")
            except Exception as e:
                logger.error(f"Failed to read requirements file: {str(e)}")
                requirements = "Failed to read requirements file."
        else:
            # In a real implementation, this would be gathered from an interactive session
            requirements = "Sample requirements for analysis."

        # Create a prompt for the LLM
        prompt = f"""
        You are a requirements analyst. Your task is to analyze the provided requirements
        and generate a summary.

        Requirements:
        {requirements}

        Project context:
        {inputs.get('context', '')}

        Generate a comprehensive requirements summary that includes:
        1. Overview
        2. Key requirements
        3. Potential issues or ambiguities
        4. Recommendations
        """

        # Generate the summary using the LLM
        summary = self.generate_text(prompt)

        # If the LLM is not available, generate a simple summary
        if summary.startswith("Placeholder text") or summary.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback summary generation")
            summary = f"""# Requirements Summary

## Overview

This is a summary of the requirements.

## Key Requirements

{requirements[:200]}...

## Potential Issues

- Requirement clarity: Some requirements may need further clarification.
- Scope definition: The scope of the project may need to be better defined.

## Recommendations

- Implement the requirements as specified.
- Consider adding more detailed acceptance criteria.
- Review the requirements with stakeholders.
"""

        # Write the summary to a file
        project_root = inputs.get("project_root", ".")
        logger.info(f"Project root for summary file: {project_root}")
        summary_file = os.path.join(project_root, "requirements_summary.md")
        logger.info(f"Attempting to write requirements summary to {summary_file}")
        try:
            with open(summary_file, "w") as f:
                f.write(summary)
            logger.info(f"Requirements summary written to {summary_file}")
        except Exception as e:
            logger.error(f"Failed to write requirements summary: {str(e)}", error=e)

        # Create a WSDE with the summary
        summary_wsde = self.create_wsde(
            content=summary,
            content_type="text",
            metadata={"agent": self.name, "type": "requirements_summary"},
        )

        return {
            "summary": summary,
            "summary_file": summary_file,
            "wsde": summary_wsde,
            "agent": self.name,
        }

    def _process_feedback_task(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process feedback on generated artifacts to improve future generations.

        This method implements continuous learning by analyzing user modifications
        to generated artifacts and storing patterns for future use.
        """
        # Extract the original artifact and the modified version
        original_artifact = inputs.get("original_artifact", "")
        modified_artifact = inputs.get("modified_artifact", "")
        artifact_type = inputs.get(
            "artifact_type", "code"
        )  # code, tests, documentation, etc.

        # Create a prompt for the LLM to analyze the differences
        prompt = f"""
        You are an expert in continuous learning and improvement. Your task is to analyze
        the differences between an original AI-generated artifact and the human-modified version.

        Original {artifact_type}:
        {original_artifact}

        Human-modified {artifact_type}:
        {modified_artifact}

        Please analyze the differences and identify:
        1. What patterns or improvements did the human make?
        2. What mistakes or issues in the original were corrected?
        3. What stylistic preferences are evident in the modifications?
        4. What can be learned from these changes to improve future generations?

        Provide a structured analysis that can be used to improve future generations.
        Include specific patterns that can be stored and reused.
        """

        # Generate the analysis using the LLM
        analysis = self.generate_text(prompt)

        # If the LLM is not available, generate a simple analysis
        if analysis.startswith("Placeholder text") or analysis.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback analysis generation")
            analysis = f"Feedback analysis (created by {self.name})"

        # Extract learnings and patterns from the analysis
        extract_prompt = f"""
        Based on the following analysis of differences between AI-generated and human-modified artifacts,
        extract specific patterns, rules, or templates that can be stored and reused for future generations.

        Analysis:
        {analysis}

        For each pattern, provide:
        1. A name/identifier for the pattern
        2. A description of when and how to apply it
        3. A template or example showing the pattern in use
        4. The context in which this pattern is applicable

        Format the patterns as a structured JSON object that can be stored in a pattern library.
        """

        # Generate the patterns using the LLM
        patterns_json = self.generate_text(extract_prompt)

        # If the LLM is not available, generate simple patterns
        if patterns_json.startswith("Placeholder text") or patterns_json.startswith(
            "Error generating text"
        ):
            logger.warning("Using fallback patterns generation")
            patterns_json = "{}"

        # Create a WSDE with the analysis and patterns
        feedback_wsde = self.create_wsde(
            content=analysis,
            content_type="text",
            metadata={
                "agent": self.name,
                "type": "feedback_analysis",
                "artifact_type": artifact_type,
                "patterns": patterns_json,
            },
        )

        # Store the patterns for future use (in a real implementation, this would save to a database or file)
        # For now, we'll just log that we would store these patterns
        logger.info(
            f"Learned {len(patterns_json)} patterns from user feedback on {artifact_type}"
        )

        return {
            "analysis": analysis,
            "patterns": patterns_json,
            "wsde": feedback_wsde,
            "agent": self.name,
        }

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = MVP_CAPABILITIES + [
                "process_feedback",
                "continuous_learning",
            ]
        return capabilities
