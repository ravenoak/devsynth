
# DevSynth System Pseudocode

## Table of Contents

1. [Introduction](#introduction)
2. [How to Use This Document](#how-to-use-this-document)
3. [Architecture Overview](#architecture-overview)
4. [Domain Layer](#domain-layer)
   - [4.1 Core Entities](#41-core-entities)
   - [4.2 Value Objects](#42-value-objects)
   - [4.3 Domain Services](#43-domain-services)
   - [4.4 Domain Events](#44-domain-events)
5. [Application Layer](#application-layer)
   - [5.1 Use Cases](#51-use-cases)
   - [5.2 Orchestration](#52-orchestration)
   - [5.3 Agent System](#53-agent-system)
   - [5.4 Core Values Subsystem](#54-core-values-subsystem)
   - [5.5 Token Management](#55-token-management)
6. [Adapter Layer](#adapter-layer)
   - [6.1 CLI Interface](#61-cli-interface)
   - [6.2 LLM Provider Interfaces](#62-llm-provider-interfaces)
   - [6.3 File System Interface](#63-file-system-interface)
   - [6.4 Memory Interface](#64-memory-interface)
7. [Infrastructure Layer](#infrastructure-layer)
   - [7.1 CLI Implementation](#71-cli-implementation)
   - [7.2 LM Studio Adapter](#72-lm-studio-adapter)
   - [7.3 File System Implementation](#73-file-system-implementation)
   - [7.4 Memory Implementation](#74-memory-implementation)
8. [Cross-Cutting Concerns](#cross-cutting-concerns)
   - [8.1 Logging](#81-logging)
   - [8.2 Error Handling](#82-error-handling)
   - [8.3 Configuration](#83-configuration)
   - [8.4 Security](#84-security)
9. [Workflow Examples](#workflow-examples)
   - [9.1 Project Initialization](#91-project-initialization)
   - [9.2 Specification Generation](#92-specification-generation)
   - [9.3 Test Generation](#93-test-generation)
   - [9.4 Code Generation](#94-code-generation)
   - [9.5 Token Usage Reporting](#95-token-usage-reporting)
10. [References](#references)

## 1. Introduction

This document provides comprehensive pseudocode for the DevSynth system, an AI-assisted software development tool that helps a single developer accelerate the software development lifecycle. The pseudocode is organized according to the Hexagonal Architecture pattern (also known as Ports and Adapters) with clear separation between domain, application, adapter, and infrastructure layers.

DevSynth is designed as a CLI application that runs entirely on a developer's local machine, using LM Studio as the local LLM provider. It focuses on minimal resource usage, token optimization, and appropriate security for a single-developer proof of concept.

The pseudocode is designed to be language-agnostic but follows Python-like syntax for readability. It includes all major components and functionalities described in the DevSynth specifications and diagrams, with cross-references to the original documentation.

## 2. How to Use This Document

This pseudocode document is intended to be used alongside the DevSynth specifications and diagrams. To get the most out of this document:

1. **Cross-References**: Throughout the document, you'll find references to the original specifications and diagrams in the format `[Spec §X.Y.Z]` or `[Diagram: Name]`. These references point to specific sections in the specification documents or specific diagrams.

2. **Navigation**: Use the Table of Contents to navigate to specific sections. Each major component of the system has its own section with detailed pseudocode.

3. **Implementation Guidance**: The pseudocode includes comments that provide implementation guidance, explain design decisions, and highlight important considerations.

4. **Layered Organization**: The pseudocode is organized according to the Hexagonal Architecture pattern:
   - **Domain Layer**: Core business logic and entities
   - **Application Layer**: Use cases and orchestration
   - **Adapter Layer**: Interfaces to external systems
   - **Infrastructure Layer**: Implementations of adapters

5. **Workflow Examples**: The document includes examples of key workflows to illustrate how the components work together to accomplish tasks.

6. **Token Management**: Special attention is given to token management and optimization throughout the pseudocode, reflecting the importance of efficient resource usage.

## 3. Architecture Overview

DevSynth follows a Hexagonal Architecture pattern with Event-Driven Architecture and CQRS principles. The system is organized into the following layers:

```
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                           │
│  Core Entities, Value Objects, Domain Services, Events      │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Application Layer                         │
│  Use Cases, Orchestration, Agent System, Core Values        │
└─┬─────────────┬─────────────┬────────────────┬──────────────┘
  │             │             │                │
┌─▼───────────┐┌▼───────────┐┌▼───────────────┐┌▼──────────────┐
│  CLI        ││  LLM       ││  File System   ││  Memory       │
│  Interface  ││  Interface ││  Interface     ││  Interface    │
└─────────────┘└────────────┘└────────────────┘└───────────────┘
       │             │             │                │
┌──────▼──────┐┌─────▼──────┐┌─────▼──────┐┌───────▼─────────┐
│  CLI        ││  LM Studio ││  File      ││  Memory         │
│  Impl       ││  Adapter   ││  System    ││  Impl           │
└─────────────┘└────────────┘└────────────┘└─────────────────┘
```

This architecture provides:
- Clear separation of concerns
- Testability through dependency inversion
- Flexibility to swap implementations
- Protection of the domain logic from external changes
- Local-first operation with all components on the developer's machine
- Efficient resource usage with token optimization at every level

[Diagram: System Architecture Diagram]

## 4. Domain Layer

The Domain Layer contains the core business logic and entities of the system, independent of external concerns.

### 4.1 Core Entities

#### 4.1.1 Project

```python
# [Spec §8.1] Project Model
class Project:
    """Representation of a software project."""
    
    def __init__(self, id, name, description=None, template="default"):
        self.id = id                      # UUID
        self.name = name                  # string
        self.description = description    # string or None
        self.created_at = current_time()  # datetime
        self.updated_at = current_time()  # datetime
        self.template = template          # string
        self.config = {}                  # Dictionary
        self.path = None                  # Path
        self.requirements = []            # List of Requirement objects
        self.tests = []                   # List of Test objects
        self.workflows = []               # List of Workflow objects
        self.token_usage = TokenUsage()   # Token usage tracking
    
    def add_requirement(self, requirement):
        """Add a requirement to the project."""
        self.requirements.append(requirement)
        self.updated_at = current_time()
    
    def add_test(self, test):
        """Add a test to the project."""
        self.tests.append(test)
        self.updated_at = current_time()
    
    def add_workflow(self, workflow):
        """Add a workflow to the project."""
        self.workflows.append(workflow)
        self.updated_at = current_time()
    
    def update_config(self, key, value):
        """Update a configuration value."""
        self.config[key] = value
        self.updated_at = current_time()
    
    def get_requirements_by_status(self, status):
        """Get requirements by status."""
        return [req for req in self.requirements if req.status == status]
    
    def get_tests_by_status(self, status):
        """Get tests by status."""
        return [test for test in self.tests if test.status == status]
    
    def get_workflows_by_status(self, status):
        """Get workflows by status."""
        return [workflow for workflow in self.workflows if workflow.status == status]
    
    def get_token_usage_report(self):
        """Get a report of token usage for this project."""
        return self.token_usage.get_report()
    
    def add_token_usage(self, prompt_tokens, completion_tokens):
        """Add token usage to the project's total."""
        self.token_usage.add_usage(prompt_tokens, completion_tokens)
```

#### 4.1.2 Requirement

```python
# [Spec §8.2] Requirement Model
class Requirement:
    """Representation of a software requirement."""
    
    def __init__(self, id, project_id, title, description, type, priority="medium"):
        self.id = id                      # UUID
        self.project_id = project_id      # UUID
        self.title = title                # string
        self.description = description    # string
        self.type = type                  # RequirementType enum
        self.priority = priority          # Priority enum
        self.status = "draft"             # Status enum
        self.created_at = current_time()  # datetime
        self.updated_at = current_time()  # datetime
        self.related_tests = []           # List of Test IDs
        self.token_count = estimate_tokens(description)  # int
    
    def update_status(self, status):
        """Update the status of the requirement."""
        self.status = status
        self.updated_at = current_time()
    
    def link_test(self, test_id):
        """Link a test to this requirement."""
        if test_id not in self.related_tests:
            self.related_tests.append(test_id)
            self.updated_at = current_time()
    
    def validate(self):
        """Validate the requirement for completeness and consistency."""
        # Check for required fields
        if not self.title or not self.description:
            return False, "Title and description are required"
        
        # Check for minimum description length
        if len(self.description) < 10:
            return False, "Description is too short"
        
        return True, "Requirement is valid"
    
    def optimize_tokens(self, max_tokens=None):
        """Optimize the requirement description to reduce token usage."""
        if not max_tokens or self.token_count <= max_tokens:
            return self.description
        
        # Simple optimization: truncate to fit max_tokens
        # In a real implementation, this would use more sophisticated techniques
        words = self.description.split()
        optimized_description = ""
        current_tokens = 0
        
        for word in words:
            word_tokens = estimate_tokens(word + " ")
            if current_tokens + word_tokens <= max_tokens:
                optimized_description += word + " "
                current_tokens += word_tokens
            else:
                break
        
        self.description = optimized_description.strip()
        self.token_count = current_tokens
        self.updated_at = current_time()
        
        return self.description
```

#### 4.1.3 Test

```python
# [Spec §8.3] Test Model
class Test:
    """Representation of a test case."""
    
    def __init__(self, id, project_id, title, type, path=None, description=None):
        self.id = id                      # UUID
        self.project_id = project_id      # UUID
        self.title = title                # string
        self.description = description    # string or None
        self.type = type                  # TestType enum
        self.status = "pending"           # TestStatus enum
        self.path = path                  # Path or None
        self.requirements = []            # List of Requirement IDs
        self.created_at = current_time()  # datetime
        self.updated_at = current_time()  # datetime
        self.token_count = estimate_tokens(description or "")  # int
    
    def update_status(self, status):
        """Update the status of the test."""
        self.status = status
        self.updated_at = current_time()
    
    def link_requirement(self, requirement_id):
        """Link a requirement to this test."""
        if requirement_id not in self.requirements:
            self.requirements.append(requirement_id)
            self.updated_at = current_time()
    
    def validate(self):
        """Validate the test for completeness and consistency."""
        # Check for required fields
        if not self.title:
            return False, "Title is required"
        
        # Check that the test is linked to at least one requirement
        if not self.requirements:
            return False, "Test must be linked to at least one requirement"
        
        return True, "Test is valid"
    
    def optimize_tokens(self, max_tokens=None):
        """Optimize the test description to reduce token usage."""
        if not self.description or not max_tokens or self.token_count <= max_tokens:
            return self.description
        
        # Simple optimization: truncate to fit max_tokens
        # In a real implementation, this would use more sophisticated techniques
        words = self.description.split()
        optimized_description = ""
        current_tokens = 0
        
        for word in words:
            word_tokens = estimate_tokens(word + " ")
            if current_tokens + word_tokens <= max_tokens:
                optimized_description += word + " "
                current_tokens += word_tokens
            else:
                break
        
        self.description = optimized_description.strip()
        self.token_count = current_tokens
        self.updated_at = current_time()
        
        return self.description
```

#### 4.1.4 UnitTest

```python
# [Spec §8.3] Unit Test Model
class UnitTest(Test):
    """Representation of a unit test."""
    
    def __init__(self, id, project_id, title, path=None, description=None):
        super().__init__(id, project_id, title, "unit", path, description)
        self.function_name = ""          # string
        self.test_cases = []             # List of TestCase objects
        self.setup_code = ""             # string
        self.teardown_code = ""          # string
    
    def add_test_case(self, test_case):
        """Add a test case to the unit test."""
        self.test_cases.append(test_case)
        self.token_count += test_case.token_count
        self.updated_at = current_time()
    
    def generate_test_code(self):
        """Generate pytest code for this unit test."""
        code = f"def test_{self.function_name}():\n"
        
        # Add setup code if present
        if self.setup_code:
            code += f"    # Setup\n    {self.setup_code}\n\n"
        
        # Add test cases
        for i, test_case in enumerate(self.test_cases):
            code += f"    # Test case {i+1}\n"
            code += f"    inputs = {test_case.inputs}\n"
            code += f"    expected = {test_case.expected_output}\n"
            code += f"    result = {self.function_name}(**inputs)\n"
            
            # Add assertions
            for assertion in test_case.assertions:
                code += f"    {assertion}\n"
            
            code += "\n"
        
        # Add teardown code if present
        if self.teardown_code:
            code += f"    # Teardown\n    {self.teardown_code}\n"
        
        return code
    
    def optimize_tokens(self, max_tokens=None):
        """Optimize the unit test to reduce token usage."""
        # First optimize the description
        super().optimize_tokens(max_tokens // 4 if max_tokens else None)
        
        if not max_tokens or self.token_count <= max_tokens:
            return
        
        # Optimize test cases
        remaining_tokens = max_tokens - self.token_count
        tokens_per_case = remaining_tokens // len(self.test_cases) if self.test_cases else 0
        
        for test_case in self.test_cases:
            test_case.optimize_tokens(tokens_per_case)
        
        # Recalculate total token count
        self.token_count = estimate_tokens(self.description or "")
        for test_case in self.test_cases:
            self.token_count += test_case.token_count
```

#### 4.1.5 Agent

```python
# [Spec §8.4] Agent Model
class Agent:
    """Representation of an AI agent."""
    
    def __init__(self, id, name, role):
        self.id = id                      # UUID
        self.name = name                  # string
        self.role = role                  # string
        self.capabilities = []            # List of strings
        self.status = "idle"              # AgentStatus enum
        self.created_at = current_time()  # datetime
        self.updated_at = current_time()  # datetime
        self.system_prompt = ""           # string
        self.tasks = []                   # List of Task objects
        self.token_usage = TokenUsage()   # Token usage tracking
    
    def add_capability(self, capability):
        """Add a capability to the agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.updated_at = current_time()
    
    def update_status(self, status):
        """Update the status of the agent."""
        self.status = status
        self.updated_at = current_time()
    
    def set_system_prompt(self, prompt):
        """Set the system prompt for the agent."""
        self.system_prompt = prompt
        self.updated_at = current_time()
    
    def can_handle(self, task_type):
        """Check if the agent can handle a specific task type."""
        return task_type in self.capabilities
    
    def assign_task(self, task):
        """Assign a task to the agent."""
        self.tasks.append(task)
        self.update_status("working")
        return True
    
    def optimize_prompt(self, prompt, max_tokens=None):
        """Optimize a prompt to reduce token usage."""
        prompt_tokens = estimate_tokens(prompt)
        
        if not max_tokens or prompt_tokens <= max_tokens:
            return prompt
        
        # Simple optimization: truncate to fit max_tokens
        # In a real implementation, this would use more sophisticated techniques
        words = prompt.split()
        optimized_prompt = ""
        current_tokens = 0
        
        for word in words:
            word_tokens = estimate_tokens(word + " ")
            if current_tokens + word_tokens <= max_tokens:
                optimized_prompt += word + " "
                current_tokens += word_tokens
            else:
                break
        
        return optimized_prompt.strip()
    
    def get_token_usage_report(self):
        """Get a report of token usage for this agent."""
        return self.token_usage.get_report()
    
    def add_token_usage(self, prompt_tokens, completion_tokens):
        """Add token usage to the agent's total."""
        self.token_usage.add_usage(prompt_tokens, completion_tokens)
```

#### 4.1.6 Task

```python
# [Spec §8.4] Task Model
class Task:
    """Representation of a task assigned to an agent."""
    
    def __init__(self, id, agent_id, task_type, inputs=None):
        self.id = id                      # UUID
        self.agent_id = agent_id          # UUID
        self.task_type = task_type        # string
        self.inputs = inputs or {}        # Dictionary
        self.outputs = {}                 # Dictionary
        self.status = "pending"           # TaskStatus enum
        self.created_at = current_time()  # datetime
        self.completed_at = None          # datetime or None
        self.error = None                 # string or None
        self.token_usage = TokenUsage()   # Token usage tracking
    
    def update_status(self, status):
        """Update the status of the task."""
        self.status = status
        if status == "completed":
            self.completed_at = current_time()
    
    def set_output(self, key, value):
        """Set an output value."""
        self.outputs[key] = value
    
    def set_error(self, error):
        """Set an error message."""
        self.error = error
        self.update_status("failed")
    
    def is_complete(self):
        """Check if the task is complete."""
        return self.status == "completed"
    
    def duration(self):
        """Get the duration of the task."""
        if not self.completed_at:
            return None
        return self.completed_at - self.created_at
    
    def get_token_usage(self):
        """Get the token usage for this task."""
        return self.token_usage
    
    def add_token_usage(self, prompt_tokens, completion_tokens):
        """Add token usage to the task's total."""
        self.token_usage.add_usage(prompt_tokens, completion_tokens)
```

#### 4.1.7 Workflow

```python
# [Spec §8.5] Workflow Model
class Workflow:
    """Representation of a workflow."""
    
    def __init__(self, id, project_id, name, description=None):
        self.id = id                      # UUID
        self.project_id = project_id      # UUID
        self.name = name                  # string
        self.description = description    # string or None
        self.status = "pending"           # WorkflowStatus enum
        self.steps = []                   # List of WorkflowStep objects
        self.current_step = 0             # int
        self.created_at = current_time()  # datetime
        self.updated_at = current_time()  # datetime
        self.token_usage = TokenUsage()   # Token usage tracking
    
    def add_step(self, step):
        """Add a step to the workflow."""
        self.steps.append(step)
        self.updated_at = current_time()
    
    def update_status(self, status):
        """Update the status of the workflow."""
        self.status = status
        self.updated_at = current_time()
    
    def advance(self):
        """Advance to the next step in the workflow."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.updated_at = current_time()
            return True
        return False
    
    def current_step_object(self):
        """Get the current step object."""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def is_complete(self):
        """Check if the workflow is complete."""
        return self.status == "completed"
    
    def progress(self):
        """Get the progress of the workflow as a percentage."""
        if not self.steps:
            return 0
        return (self.current_step + 1) / len(self.steps) * 100
    
    def get_token_usage_report(self):
        """Get a report of token usage for this workflow."""
        return self.token_usage.get_report()
    
    def add_token_usage(self, prompt_tokens, completion_tokens):
        """Add token usage to the workflow's total."""
        self.token_usage.add_usage(prompt_tokens, completion_tokens)
```

### 4.2 Value Objects

#### 4.2.1 TestCase

```python
# [Spec §8.3] TestCase Model
class TestCase:
    """Representation of a unit test case."""
    
    def __init__(self, id, inputs, expected_output):
        self.id = id                      # UUID
        self.inputs = inputs              # Dictionary
        self.expected_output = expected_output  # Any
        self.assertions = []              # List of strings
        self.token_count = estimate_tokens(str(inputs) + str(expected_output))  # int
    
    def add_assertion(self, assertion):
        """Add an assertion to the test case."""
        self.assertions.append(assertion)
        self.token_count += estimate_tokens(assertion)
    
    def to_pytest(self, function_name):
        """Convert the test case to pytest format."""
        code = f"def test_{function_name}_case_{self.id}():\n"
        code += f"    inputs = {self.inputs}\n"
        code += f"    expected = {self.expected_output}\n"
        code += f"    result = {function_name}(**inputs)\n"
        
        for assertion in self.assertions:
            code += f"    {assertion}\n"
        
        return code
    
    def optimize_tokens(self, max_tokens=None):
        """Optimize the test case to reduce token usage."""
        if not max_tokens or self.token_count <= max_tokens:
            return
        
        # Reduce the number of assertions to fit within token budget
        if self.assertions:
            tokens_per_assertion = max_tokens // len(self.assertions)
            optimized_assertions = []
            
            for assertion in self.assertions:
                if estimate_tokens(assertion) <= tokens_per_assertion:
                    optimized_assertions.append(assertion)
            
            # Keep at least one assertion
            if not optimized_assertions and self.assertions:
                optimized_assertions = [self.assertions[0]]
            
            self.assertions = optimized_assertions
            
            # Recalculate token count
            self.token_count = estimate_tokens(str(self.inputs) + str(self.expected_output))
            for assertion in self.assertions:
                self.token_count += estimate_tokens(assertion)
```

#### 4.2.2 WorkflowStep

```python
# [Spec §8.5] WorkflowStep Model
class WorkflowStep:
    """Representation of a workflow step."""
    
    def __init__(self, id, workflow_id, name, agent_id, task_type, inputs=None):
        self.id = id                      # UUID
        self.workflow_id = workflow_id    # UUID
        self.name = name                  # string
        self.description = ""             # string
        self.agent_id = agent_id          # UUID
        self.task_type = task_type        # string
        self.inputs = inputs or {}        # Dictionary
        self.outputs = {}                 # Dictionary
        self.status = "pending"           # StepStatus enum
        self.token_budget = None          # int or None
    
    def update_status(self, status):
        """Update the status of the step."""
        self.status = status
    
    def set_output(self, key, value):
        """Set an output value."""
        self.outputs[key] = value
    
    def is_complete(self):
        """Check if the step is complete."""
        return self.status == "completed"
    
    def set_description(self, description):
        """Set the description of the step."""
        self.description = description
    
    def set_token_budget(self, budget):
        """Set the token budget for this step."""
        self.token_budget = budget
```

#### 4.2.3 TokenUsage

```python
# [Spec §8.1] Token Usage Model
class TokenUsage:
    """Representation of token usage statistics."""
    
    def __init__(self):
        self.total_tokens = 0            # int
        self.prompt_tokens = 0           # int
        self.completion_tokens = 0       # int
        self.estimated_cost = 0.0        # float
        self.last_reset = current_time() # datetime
    
    def add_usage(self, prompt_tokens, completion_tokens):
        """Add token usage to the total."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        
        # Update estimated cost (simplified calculation)
        # In a real implementation, this would use provider-specific pricing
        prompt_cost = prompt_tokens * 0.00001  # $0.01 per 1000 tokens
        completion_cost = completion_tokens * 0.00002  # $0.02 per 1000 tokens
        self.estimated_cost += prompt_cost + completion_cost
    
    def reset(self):
        """Reset token usage statistics."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.estimated_cost = 0.0
        self.last_reset = current_time()
    
    def get_report(self):
        """Get a report of token usage."""
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "estimated_cost": self.estimated_cost,
            "last_reset": self.last_reset.isoformat()
        }
```

#### 4.2.4 TokenBudget

```python
# Token Budget Model
class TokenBudget:
    """Representation of a token budget for an operation."""
    
    def __init__(self, total_budget):
        self.total_budget = total_budget  # int
        self.used_budget = 0              # int
        self.remaining_budget = total_budget  # int
    
    def use_tokens(self, tokens):
        """Use tokens from the budget."""
        self.used_budget += tokens
        self.remaining_budget = max(0, self.total_budget - self.used_budget)
        return self.remaining_budget
    
    def check_budget(self, required_tokens):
        """Check if there is enough budget for the required tokens."""
        return self.remaining_budget >= required_tokens
    
    def get_remaining_percentage(self):
        """Get the remaining budget as a percentage."""
        if self.total_budget == 0:
            return 0
        return (self.remaining_budget / self.total_budget) * 100
```

### 4.3 Domain Services

#### 4.3.1 ProjectService

```python
# [Spec §4.1] Project Initialization and Management
class ProjectService:
    """Domain service for project operations."""
    
    def __init__(self, project_repository, template_service):
        self.project_repository = project_repository
        self.template_service = template_service
    
    def create_project(self, name, template="default", description=None):
        """Create a new project."""
        # Generate a new UUID for the project
        project_id = generate_uuid()
        
        # Create the project object
        project = Project(project_id, name, description, template)
        
        # Apply the template
        template_config = self.template_service.get_template(template)
        project.config = template_config
        
        # Save the project
        self.project_repository.save(project)
        
        return project, "Project created successfully"
    
    def update_project(self, project_id, updates):
        """Update a project."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Apply updates
        if "name" in updates:
            project.name = updates["name"]
        
        if "description" in updates:
            project.description = updates["description"]
        
        if "config" in updates:
            for key, value in updates["config"].items():
                project.update_config(key, value)
        
        project.updated_at = current_time()
        
        # Save the updated project
        self.project_repository.save(project)
        
        return project, "Project updated successfully"
    
    def delete_project(self, project_id):
        """Delete a project."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return False, "Project not found"
        
        # Delete the project
        self.project_repository.delete(project_id)
        
        return True, "Project deleted successfully"
    
    def get_token_usage_report(self, project_id):
        """Get a token usage report for a project."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Get the token usage report
        report = project.get_token_usage_report()
        
        return report, "Token usage report retrieved successfully"
    
    def reset_token_usage(self, project_id):
        """Reset token usage for a project."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return False, "Project not found"
        
        # Reset token usage
        project.token_usage.reset()
        
        # Save the updated project
        self.project_repository.save(project)
        
        return True, "Token usage reset successfully"
```

#### 4.3.2 RequirementService

```python
# [Spec §4.2] Requirement Analysis and Specification
class RequirementService:
    """Domain service for requirement operations."""
    
    def __init__(self, requirement_repository, project_repository, token_optimizer):
        self.requirement_repository = requirement_repository
        self.project_repository = project_repository
        self.token_optimizer = token_optimizer
    
    def create_requirement(self, project_id, title, description, type, priority="medium"):
        """Create a new requirement."""
        # Check if the project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Generate a new UUID for the requirement
        requirement_id = generate_uuid()
        
        # Create the requirement object
        requirement = Requirement(requirement_id, project_id, title, description, type, priority)
        
        # Validate the requirement
        valid, message = requirement.validate()
        if not valid:
            return None, message
        
        # Save the requirement
        self.requirement_repository.save(requirement)
        
        # Update the project
        project.add_requirement(requirement)
        self.project_repository.save(project)
        
        return requirement, "Requirement created successfully"
    
    def update_requirement(self, requirement_id, updates):
        """Update a requirement."""
        # Get the requirement
        requirement = self.requirement_repository.get_by_id(requirement_id)
        if not requirement:
            return None, "Requirement not found"
        
        # Apply updates
        if "title" in updates:
            requirement.title = updates["title"]
        
        if "description" in updates:
            requirement.description = updates["description"]
            requirement.token_count = estimate_tokens(requirement.description)
        
        if "type" in updates:
            requirement.type = updates["type"]
        
        if "priority" in updates:
            requirement.priority = updates["priority"]
        
        if "status" in updates:
            requirement.update_status(updates["status"])
        
        # Validate the requirement
        valid, message = requirement.validate()
        if not valid:
            return None, message
        
        # Save the updated requirement
        self.requirement_repository.save(requirement)
        
        return requirement, "Requirement updated successfully"
    
    def delete_requirement(self, requirement_id):
        """Delete a requirement."""
        # Get the requirement
        requirement = self.requirement_repository.get_by_id(requirement_id)
        if not requirement:
            return False, "Requirement not found"
        
        # Delete the requirement
        self.requirement_repository.delete(requirement_id)
        
        return True, "Requirement deleted successfully"
    
    def generate_specification(self, project_id, token_budget=None):
        """Generate a specification from requirements."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Get all approved requirements for the project
        requirements = self.requirement_repository.get_by_project_id_and_status(project_id, "approved")
        if not requirements:
            return None, "No approved requirements found"
        
        # Optimize requirements if token budget is provided
        if token_budget:
            # Calculate tokens per requirement
            total_tokens = sum(req.token_count for req in requirements)
            if total_tokens > token_budget:
                # Need to optimize
                tokens_per_req = token_budget // len(requirements)
                for req in requirements:
                    req.optimize_tokens(tokens_per_req)
        
        # Generate specification (this would be handled by an agent in the real implementation)
        specification = {
            "project_name": project.name,
            "project_description": project.description,
            "sections": []
        }
        
        # Group requirements by type
        grouped_requirements = {}
        for req in requirements:
            if req.type not in grouped_requirements:
                grouped_requirements[req.type] = []
            grouped_requirements[req.type].append(req)
        
        # Create sections for each requirement type
        for req_type, reqs in grouped_requirements.items():
            section = {
                "title": f"{req_type.capitalize()} Requirements",
                "requirements": []
            }
            
            for req in reqs:
                section["requirements"].append({
                    "id": req.id,
                    "title": req.title,
                    "description": req.description,
                    "priority": req.priority
                })
            
            specification["sections"].append(section)
        
        return specification, "Specification generated successfully"
    
    def optimize_requirements(self, project_id, token_budget):
        """Optimize requirements to fit within a token budget."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Get all requirements for the project
        requirements = self.requirement_repository.get_by_project_id(project_id)
        if not requirements:
            return None, "No requirements found"
        
        # Calculate total tokens
        total_tokens = sum(req.token_count for req in requirements)
        
        # If already within budget, no optimization needed
        if total_tokens <= token_budget:
            return requirements, "Requirements already within token budget"
        
        # Calculate tokens per requirement
        tokens_per_req = token_budget // len(requirements)
        
        # Optimize each requirement
        optimized_requirements = []
        for req in requirements:
            optimized_req = req.optimize_tokens(tokens_per_req)
            optimized_requirements.append(req)
            self.requirement_repository.save(req)
        
        return optimized_requirements, "Requirements optimized successfully"
```

#### 4.3.3 TestService

```python
# [Spec §4.3] Test-Driven Development
class TestService:
    """Domain service for test operations."""
    
    def __init__(self, test_repository, requirement_repository, project_repository, token_optimizer):
        self.test_repository = test_repository
        self.requirement_repository = requirement_repository
        self.project_repository = project_repository
        self.token_optimizer = token_optimizer
    
    def create_unit_test(self, project_id, title, function_name, description=None):
        """Create a new unit test."""
        # Check if the project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Generate a new UUID for the test
        test_id = generate_uuid()
        
        # Create the unit test object
        test = UnitTest(test_id, project_id, title, description=description)
        test.function_name = function_name
        
        # Save the test
        self.test_repository.save(test)
        
        # Update the project
        project.add_test(test)
        self.project_repository.save(project)
        
        return test, "Unit test created successfully"
    
    def add_test_case_to_unit_test(self, test_id, inputs, expected_output, assertions):
        """Add a test case to a unit test."""
        # Get the test
        test = self.test_repository.get_by_id(test_id)
        if not test:
            return None, "Test not found"
        
        if not isinstance(test, UnitTest):
            return None, "Test is not a unit test"
        
        # Generate a new UUID for the test case
        test_case_id = generate_uuid()
        
        # Create the test case
        test_case = TestCase(test_case_id, inputs, expected_output)
        
        # Add assertions
        for assertion in assertions:
            test_case.add_assertion(assertion)
        
        # Add the test case to the test
        test.add_test_case(test_case)
        
        # Save the updated test
        self.test_repository.save(test)
        
        return test_case, "Test case added successfully"
    
    def link_test_to_requirement(self, test_id, requirement_id):
        """Link a test to a requirement."""
        # Get the test
        test = self.test_repository.get_by_id(test_id)
        if not test:
            return False, "Test not found"
        
        # Get the requirement
        requirement = self.requirement_repository.get_by_id(requirement_id)
        if not requirement:
            return False, "Requirement not found"
        
        # Link the test to the requirement
        test.link_requirement(requirement_id)
        requirement.link_test(test_id)
        
        # Save the updated test and requirement
        self.test_repository.save(test)
        self.requirement_repository.save(requirement)
        
        return True, "Test linked to requirement successfully"
    
    def generate_tests_from_specification(self, specification, token_budget=None):
        """Generate tests from a specification."""
        # This would be handled by an agent in the real implementation
        tests = []
        
        # Process each section in the specification
        for section in specification["sections"]:
            for req in section["requirements"]:
                # Generate a unit test for each requirement
                test_id = generate_uuid()
                test = UnitTest(
                    test_id,
                    specification["project_id"],
                    f"Test for {req['title']}",
                    description=f"Verify {req['description']}"
                )
                
                # Set function name based on requirement title
                function_name = req['title'].lower().replace(' ', '_')
                test.function_name = function_name
                
                # Generate a test case
                test_case_id = generate_uuid()
                test_case = TestCase(
                    test_case_id,
                    {"input": "test_input"},
                    "expected_output"
                )
                
                # Add assertions
                test_case.add_assertion("assert result == expected")
                
                # Add the test case to the test
                test.add_test_case(test_case)
                
                # Link the test to the requirement
                test.link_requirement(req["id"])
                
                tests.append(test)
        
        # Optimize tests if token budget is provided
        if token_budget and tests:
            # Calculate tokens per test
            total_tokens = sum(test.token_count for test in tests)
            if total_tokens > token_budget:
                # Need to optimize
                tokens_per_test = token_budget // len(tests)
                for test in tests:
                    test.optimize_tokens(tokens_per_test)
        
        return tests, "Tests generated successfully"
    
    def run_tests(self, project_id, test_type="all"):
        """Run tests for a project."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Get the tests for the project
        if test_type == "all":
            tests = self.test_repository.get_by_project_id(project_id)
        else:
            tests = self.test_repository.get_by_project_id_and_type(project_id, test_type)
        
        if not tests:
            return None, "No tests found"
        
        # Run the tests (simplified for pseudocode)
        results = {}
        for test in tests:
            # Simulate running the test
            success = random.random() > 0.2  # 80% success rate
            
            # Update test status
            test.update_status("passing" if success else "failing")
            self.test_repository.save(test)
            
            results[test.id] = {
                "success": success,
                "message": "Test passed" if success else "Test failed"
            }
        
        return results, "Tests run successfully"
    
    def optimize_tests(self, project_id, token_budget):
        """Optimize tests to fit within a token budget."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Get all tests for the project
        tests = self.test_repository.get_by_project_id(project_id)
        if not tests:
            return None, "No tests found"
        
        # Calculate total tokens
        total_tokens = sum(test.token_count for test in tests)
        
        # If already within budget, no optimization needed
        if total_tokens <= token_budget:
            return tests, "Tests already within token budget"
        
        # Calculate tokens per test
        tokens_per_test = token_budget // len(tests)
        
        # Optimize each test
        optimized_tests = []
        for test in tests:
            test.optimize_tokens(tokens_per_test)
            optimized_tests.append(test)
            self.test_repository.save(test)
        
        return optimized_tests, "Tests optimized successfully"
```

#### 4.3.4 CodeService

```python
# [Spec §4.4] Code Generation and Implementation
class CodeService:
    """Domain service for code operations."""
    
    def __init__(self, test_repository, file_system_port, token_optimizer):
        self.test_repository = test_repository
        self.file_system_port = file_system_port
        self.token_optimizer = token_optimizer
    
    def generate_code_from_tests(self, test_ids, output_path, token_budget=None):
        """Generate code from tests."""
        # Get the tests
        tests = [self.test_repository.get_by_id(test_id) for test_id in test_ids]
        tests = [test for test in tests if test]  # Filter out None values
        
        if not tests:
            return None, "No tests found"
        
        # Optimize tests if token budget is provided
        if token_budget:
            # Calculate tokens per test
            total_tokens = sum(test.token_count for test in tests)
            if total_tokens > token_budget:
                # Need to optimize
                tokens_per_test = token_budget // len(tests)
                for test in tests:
                    test.optimize_tokens(tokens_per_test)
        
        # This would be handled by an agent in the real implementation
        generated_code = {}
        
        for test in tests:
            if isinstance(test, UnitTest):
                # Generate function code from unit test
                function_name = test.function_name
                function_code = self._generate_function_from_unit_test(test)
                generated_code[function_name] = function_code
        
        # Write the generated code to files
        for name, code in generated_code.items():
            file_path = f"{output_path}/{name}.py"
            self.file_system_port.write_file(file_path, code)
        
        return generated_code, "Code generated successfully"
    
    def _generate_function_from_unit_test(self, test):
        """Generate a function from a unit test."""
        # Extract function signature from test cases
        if not test.test_cases:
            return "def {}():\n    pass".format(test.function_name)
        
        # Get the first test case to determine parameters
        first_case = test.test_cases[0]
        params = ", ".join([f"{param}" for param in first_case.inputs.keys()])
        
        # Generate function code
        code = f"def {test.function_name}({params}):\n"
        code += f"    \"\"\"{test.description}\n\n"
        
        # Add parameter documentation
        for param in first_case.inputs.keys():
            code += f"    Args:\n        {param}: Description of {param}\n"
        
        code += f"\n    Returns:\n        Description of return value\n    \"\"\"\n"
        
        # Add implementation (placeholder for real implementation)
        code += "    # TODO: Implement function\n"
        code += "    pass\n"
        
        return code
    
    def optimize_code_generation(self, test_ids, token_budget):
        """Optimize code generation to fit within a token budget."""
        # Get the tests
        tests = [self.test_repository.get_by_id(test_id) for test_id in test_ids]
        tests = [test for test in tests if test]  # Filter out None values
        
        if not tests:
            return None, "No tests found"
        
        # Calculate total tokens
        total_tokens = sum(test.token_count for test in tests)
        
        # If already within budget, no optimization needed
        if total_tokens
