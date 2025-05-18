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
   - [5.5 Promise System](#55-promise-system)
6. [Adapter Layer](#adapter-layer)
   - [6.1 CLI Interface](#61-cli-interface)
   - [6.2 LLM Provider Interfaces](#62-llm-provider-interfaces)
   - [6.3 File System Interface](#63-file-system-interface)
   - [6.4 Memory Interface](#64-memory-interface)
7. [Infrastructure Layer](#infrastructure-layer)
   - [7.1 CLI Implementation](#71-cli-implementation)
   - [7.2 LLM Provider Implementations](#72-llm-provider-implementations)
   - [7.3 File System Implementation](#73-file-system-implementation)
   - [7.4 Memory Implementation](#74-memory-implementation)
8. [Cross-Cutting Concerns](#cross-cutting-concerns)
   - [8.1 Logging](#81-logging)
   - [8.2 Error Handling](#82-error-handling)
   - [8.3 Configuration](#83-configuration)
9. [Workflow Examples](#workflow-examples)
   - [9.1 Project Initialization](#91-project-initialization)
   - [9.2 Specification Generation](#92-specification-generation)
   - [9.3 Test Generation](#93-test-generation)
   - [9.4 Code Generation](#94-code-generation)
10. [References](#references)

## 1. Introduction

This document provides comprehensive pseudocode for the DevSynth system, an AI-assisted software development tool that helps developers accelerate the software development lifecycle. The pseudocode is organized according to the Hexagonal Architecture pattern (also known as Ports and Adapters) with clear separation between domain, application, adapter, and infrastructure layers.

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
│  CLI        ││  LLM       ││  File      ││  Memory         │
│  Impl       ││  Impl      ││  System    ││  Impl           │
└─────────────┘└────────────┘└────────────┘└─────────────────┘
```

This architecture provides:
- Clear separation of concerns
- Testability through dependency inversion
- Flexibility to swap implementations
- Protection of the domain logic from external changes

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
```

#### 4.1.4 BDDTest

```python
# [Spec §8.3] BDD Test Model
class BDDTest(Test):
    """Representation of a behavior-driven test."""
    
    def __init__(self, id, project_id, title, path=None, description=None):
        super().__init__(id, project_id, title, "bdd", path, description)
        self.feature = ""                # string
        self.scenarios = []              # List of Scenario objects
    
    def add_scenario(self, scenario):
        """Add a scenario to the test."""
        self.scenarios.append(scenario)
        self.updated_at = current_time()
    
    def generate_step_definitions(self):
        """Generate step definitions from scenarios."""
        step_definitions = []
        
        # Collect all unique steps
        all_steps = set()
        for scenario in self.scenarios:
            all_steps.update(scenario.given)
            all_steps.update(scenario.when)
            all_steps.update(scenario.then)
        
        # Generate step definition for each unique step
        for step in all_steps:
            step_def = {
                "step": step,
                "implementation": f"def step_{sanitize(step)}():\n    # TODO: Implement step\n    pass"
            }
            step_definitions.append(step_def)
        
        return step_definitions
```

#### 4.1.5 UnitTest

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
```

#### 4.1.6 Agent

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
```

#### 4.1.7 Task

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
```

#### 4.1.8 Workflow

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
```

### 4.2 Value Objects

#### 4.2.1 Scenario

```python
# [Spec §8.3] Scenario Model
class Scenario:
    """Representation of a BDD scenario."""
    
    def __init__(self, id, title):
        self.id = id                # UUID
        self.title = title          # string
        self.given = []             # List of strings
        self.when = []              # List of strings
        self.then = []              # List of strings
    
    def add_given(self, given):
        """Add a Given step to the scenario."""
        self.given.append(given)
    
    def add_when(self, when):
        """Add a When step to the scenario."""
        self.when.append(when)
    
    def add_then(self, then):
        """Add a Then step to the scenario."""
        self.then.append(then)
    
    def to_gherkin(self):
        """Convert the scenario to Gherkin format."""
        gherkin = f"Scenario: {self.title}\n"
        
        for given in self.given:
            gherkin += f"  Given {given}\n"
        
        for when in self.when:
            gherkin += f"  When {when}\n"
        
        for then in self.then:
            gherkin += f"  Then {then}\n"
        
        return gherkin
```

#### 4.2.2 TestCase

```python
# [Spec §8.3] TestCase Model
class TestCase:
    """Representation of a unit test case."""
    
    def __init__(self, id, inputs, expected_output):
        self.id = id                      # UUID
        self.inputs = inputs              # Dictionary
        self.expected_output = expected_output  # Any
        self.assertions = []              # List of strings
    
    def add_assertion(self, assertion):
        """Add an assertion to the test case."""
        self.assertions.append(assertion)
    
    def to_pytest(self, function_name):
        """Convert the test case to pytest format."""
        code = f"def test_{function_name}_case_{self.id}():\n"
        code += f"    inputs = {self.inputs}\n"
        code += f"    expected = {self.expected_output}\n"
        code += f"    result = {function_name}(**inputs)\n"
        
        for assertion in self.assertions:
            code += f"    {assertion}\n"
        
        return code
```

#### 4.2.3 WorkflowStep

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
```

#### 4.2.4 Promise

```python
# [Spec §3.2.5] Promise System
class Promise:
    """Representation of a capability promise."""
    
    def __init__(self, id, name, description):
        self.id = id                      # UUID
        self.name = name                  # string
        self.description = description    # string
        self.capabilities = []            # List of strings
        self.constraints = []             # List of strings
    
    def add_capability(self, capability):
        """Add a capability to the promise."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def add_constraint(self, constraint):
        """Add a constraint to the promise."""
        if constraint not in self.constraints:
            self.constraints.append(constraint)
    
    def validate(self, agent):
        """Validate that an agent can fulfill this promise."""
        for capability in self.capabilities:
            if capability not in agent.capabilities:
                return False, f"Agent lacks capability: {capability}"
        
        return True, "Agent can fulfill promise"
    
    def authorize(self, agent, capability):
        """Authorize an agent to use a capability."""
        if capability not in self.capabilities:
            return False, f"Capability not in promise: {capability}"
        
        if capability not in agent.capabilities:
            return False, f"Agent lacks capability: {capability}"
        
        return True, "Agent authorized to use capability"
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
        
        return project
    
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
```

#### 4.3.2 RequirementService

```python
# [Spec §4.2] Requirement Analysis and Specification
class RequirementService:
    """Domain service for requirement operations."""
    
    def __init__(self, requirement_repository, project_repository):
        self.requirement_repository = requirement_repository
        self.project_repository = project_repository
    
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
    
    def generate_specification(self, project_id):
        """Generate a specification from requirements."""
        # Get the project
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Get all approved requirements for the project
        requirements = self.requirement_repository.get_by_project_id_and_status(project_id, "approved")
        if not requirements:
            return None, "No approved requirements found"
        
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
```

#### 4.3.3 TestService

```python
# [Spec §4.3] Test-Driven Development
class TestService:
    """Domain service for test operations."""
    
    def __init__(self, test_repository, requirement_repository, project_repository):
        self.test_repository = test_repository
        self.requirement_repository = requirement_repository
        self.project_repository = project_repository
    
    def create_bdd_test(self, project_id, title, feature, description=None):
        """Create a new BDD test."""
        # Check if the project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Generate a new UUID for the test
        test_id = generate_uuid()
        
        # Create the BDD test object
        test = BDDTest(test_id, project_id, title, description=description)
        test.feature = feature
        
        # Save the test
        self.test_repository.save(test)
        
        # Update the project
        project.add_test(test)
        self.project_repository.save(project)
        
        return test, "BDD test created successfully"
    
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
    
    def add_scenario_to_bdd_test(self, test_id, title, given, when, then):
        """Add a scenario to a BDD test."""
        # Get the test
        test = self.test_repository.get_by_id(test_id)
        if not test:
            return None, "Test not found"
        
        if not isinstance(test, BDDTest):
            return None, "Test is not a BDD test"
        
        # Generate a new UUID for the scenario
        scenario_id = generate_uuid()
        
        # Create the scenario
        scenario = Scenario(scenario_id, title)
        
        # Add steps
        for g in given:
            scenario.add_given(g)
        
        for w in when:
            scenario.add_when(w)
        
        for t in then:
            scenario.add_then(t)
        
        # Add the scenario to the test
        test.add_scenario(scenario)
        
        # Save the updated test
        self.test_repository.save(test)
        
        return scenario, "Scenario added successfully"
    
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
    
    def generate_tests_from_specification(self, specification):
        """Generate tests from a specification."""
        # This would be handled by an agent in the real implementation
        tests = []
        
        # Process each section in the specification
        for section in specification["sections"]:
            for req in section["requirements"]:
                # Generate a BDD test for each requirement
                test_id = generate_uuid()
                test = BDDTest(
                    test_id,
                    specification["project_id"],
                    f"Test for {req['title']}",
                    description=f"Verify {req['description']}"
                )
                test.feature = f"Feature: {req['title']}"
                
                # Generate a scenario
                scenario_id = generate_uuid()
                scenario = Scenario(scenario_id, f"Verify {req['title']}")
                
                # Add steps (simplified for pseudocode)
                scenario.add_given("the system is initialized")
                scenario.add_when(f"the user performs the action related to {req['title']}")
                scenario.add_then(f"the system should behave according to {req['description']}")
                
                # Add the scenario to the test
                test.add_scenario(scenario)
                
                # Link the test to the requirement
                test.link_requirement(req["id"])
                
                tests.append(test)
        
        return tests, "Tests generated successfully"
```

#### 4.3.4 CodeService

```python
# [Spec §4.4] Code Generation and Implementation
class CodeService:
    """Domain service for code operations."""
    
    def __init__(self, test_repository, file_system_port):
        self.test_repository = test_repository
        self.file_system_port = file_system_port
    
    def generate_code_from_tests(self, test_ids, output_path):
        """Generate code from tests."""
        # Get the tests
        tests = [self.test_repository.get_by_id(test_id) for test_id in test_ids]
        tests = [test for test in tests if test]  # Filter out None values
        
        if not tests:
            return None, "No tests found"
        
        # This would be handled by an agent in the real implementation
        generated_code = {}
        
        for test in tests:
            if isinstance(test, UnitTest):
                # Generate function code from unit test
                function_name = test.function_name
                function_code = self._generate_function_from_unit_test(test)
                generated_code[function_name] = function_code
            
            elif isinstance(test, BDDTest):
                # Generate class/module code from BDD test
                module_name = test.feature.split(":")[1].strip().lower().replace(" ", "_")
                module_code = self._generate_module_from_bdd_test(test)
                generated_code[module_name] = module_code
        
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
    
    def _generate_module_from_bdd_test(self, test):
        """Generate a module from a BDD test."""
        # Extract module name from feature
        module_name = test.feature.split(":")[1].strip().lower().replace(" ", "_")
        
        # Generate module code
        code = f"\"\"\"\n{test.feature}\n\n{test.description}\n\"\"\"\n\n"
        
        # Add class definition
        class_name = "".join([word.capitalize() for word in module_name.split("_")])
        code += f"class {class_name}:\n"
        code += f"    \"\"\"{test.feature}\n    \"\"\"\n\n"
        
        # Add methods based on scenarios
        for scenario in test.scenarios:
            method_name = "_".join([word.lower() for word in scenario.title.split()])
            code += f"    def {method_name}(self):\n"
            code += f"        \"\"\"{scenario.title}\n        \"\"\"\n"
            code += "        # TODO: Implement method\n"
            code += "        pass\n\n"
        
        return code
```

#### 4.3.5 DocumentationService

```python
# [Spec §4.5] Documentation Generation
class DocumentationService:
    """Domain service for documentation operations."""
    
    def __init__(self, project_repository, requirement_repository, test_repository, file_system_port):
        self.project_repository = project_repository
        self.requirement_repository = requirement_repository
        self.test_repository = test_repository
        self.file_system_port = file_system_port
    
    def generate_api_documentation(self, project_id, source_path, output_path):
        """Generate API documentation from code."""
        # Check if the project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # This would be handled by an agent in the real implementation
        # For pseudocode, we'll just create a simple structure
        
        # Read Python files from the source path
        python_files = self.file_system_port.list_files(source_path, "*.py")
        
        api_docs = {
            "project_name": project.name,
            "project_description": project.description,
            "modules": []
        }
        
        for file_path in python_files:
            # Read the file content
            content = self.file_system_port.read_file(file_path)
            
            # Extract module name from file path
            module_name = file_path.split("/")[-1].replace(".py", "")
            
            # Parse the content to extract classes and functions
            # This is simplified for pseudocode
            module_doc = self._extract_module_doc(content)
            classes = self._extract_classes(content)
            functions = self._extract_functions(content)
            
            module_info = {
                "name": module_name,
                "description": module_doc,
                "classes": classes,
                "functions": functions
            }
            
            api_docs["modules"].append(module_info)
        
        # Generate markdown documentation
        markdown = self._generate_markdown_api_docs(api_docs)
        
        # Write the documentation to a file
        output_file = f"{output_path}/api_documentation.md"
        self.file_system_port.write_file(output_file, markdown)
        
        return output_file, "API documentation generated successfully"
    
    def generate_user_documentation(self, project_id, output_path):
        """Generate user documentation from specifications and requirements."""
        # Check if the project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None, "Project not found"
        
        # Get all approved requirements for the project
        requirements = self.requirement_repository.get_by_project_id_and_status(project_id, "approved")
        
        # This would be handled by an agent in the real implementation
        # For pseudocode, we'll just create a simple structure
        
        user_docs = {
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
                "title": f"{req_type.capitalize()} Features",
                "features": []
            }
            
            for req in reqs:
                # Get tests linked to this requirement
                tests = self.test_repository.get_by_requirement_id(req.id)
                
                # Extract scenarios from BDD tests
                scenarios = []
                for test in tests:
                    if isinstance(test, BDDTest):
                        for scenario in test.scenarios:
                            scenarios.append({
                                "title": scenario.title,
                                "steps": scenario.to_gherkin()
                            })
                
                feature = {
                    "title": req.title,
                    "description": req.description,
                    "scenarios": scenarios
                }
                
                section["features"].append(feature)
            
            user_docs["sections"].append(section)
        
        # Generate markdown documentation
        markdown = self._generate_markdown_user_docs(user_docs)
        
        # Write the documentation to a file
        output_file = f"{output_path}/user_documentation.md"
        self.file_system_port.write_file(output_file, markdown)
        
        return output_file, "User documentation generated successfully"
    
    def _extract_module_doc(self, content):
        """Extract module documentation from content."""
        # Simplified for pseudocode
        if '"""' in content:
            start = content.find('"""') + 3
            end = content.find('"""', start)
            if end > start:
                return content[start:end].strip()
        return ""
    
    def _extract_classes(self, content):
        """Extract classes from content."""
        # Simplified for pseudocode
        classes = []
        lines = content.split("\n")
        
        current_class = None
        for line in lines:
            if line.startswith("class "):
                if current_class:
                    classes.append(current_class)
                
                class_name = line.split("class ")[1].split("(")[0].split(":")[0].strip()
                current_class = {
                    "name": class_name,
                    "description": "",
                    "methods": []
                }
            
            elif current_class and line.strip().startswith("def "):
                method_name = line.split("def ")[1].split("(")[0].strip()
                current_class["methods"].append({
                    "name": method_name,
                    "description": ""
                })
        
        if current_class:
            classes.append(current_class)
        
        return classes
    
    def _extract_functions(self, content):
        """Extract functions from content."""
        # Simplified for pseudocode
        functions = []
        lines = content.split("\n")
        
        for line in lines:
            if line.startswith("def ") and "class" not in line:
                function_name = line.split("def ")[1].split("(")[0].strip()
                functions.append({
                    "name": function_name,
                    "description": ""
                })
        
        return functions
    
    def _generate_markdown_api_docs(self, api_docs):
        """Generate markdown API documentation."""
        # Simplified for pseudocode
        markdown = f"# {api_docs['project_name']} API Documentation\n\n"
        markdown += f"{api_docs['project_description']}\n\n"
        
        for module in api_docs["modules"]:
            markdown += f"## Module: {module['name']}\n\n"
            markdown += f"{module['description']}\n\n"
            
            if module["classes"]:
                markdown += "### Classes\n\n"
                for cls in module["classes"]:
                    markdown += f"#### {cls['name']}\n\n"
                    markdown += f"{cls['description']}\n\n"
                    
                    if cls["methods"]:
                        markdown += "##### Methods\n\n"
                        for method in cls["methods"]:
                            markdown += f"###### {method['name']}\n\n"
                            markdown += f"{method['description']}\n\n"
            
            if module["functions"]:
                markdown += "### Functions\n\n"
                for func in module["functions"]:
                    markdown += f"#### {func['name']}\n\n"
                    markdown += f"{func['description']}\n\n"
        
        return markdown
    
    def _generate_markdown_user_docs(self, user_docs):
        """Generate markdown user documentation."""
        # Simplified for pseudocode
        markdown = f"# {user_docs['project_name']} User Documentation\n\n"
        markdown += f"{user_docs['project_description']}\n\n"
        
        for section in user_docs["sections"]:
            markdown += f"## {section['title']}\n\n"
            
            for feature in section["features"]:
                markdown += f"### {feature['title']}\n\n"
                markdown += f"{feature['description']}\n\n"
                
                if feature["scenarios"]:
                    markdown += "#### Usage Scenarios\n\n"
                    for scenario in feature["scenarios"]:
                        markdown += f"##### {scenario['title']}\n\n"
                        markdown += f"```gherkin\n{scenario['steps']}\n```\n\n"
        
        return markdown
```

### 4.4 Domain Events

```python
# [Spec §3.2.2] Orchestration Layer - Event-Driven Architecture
class DomainEvent:
    """Base class for domain events."""
    
    def __init__(self, event_type, payload, timestamp=None):
        self.event_type = event_type    # string
        self.payload = payload          # Dictionary
        self.timestamp = timestamp or current_time()  # datetime
    
    def to_dict(self):
        """Convert the event to a dictionary."""
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an event from a dictionary."""
        return cls(
            data["event_type"],
            data["payload"],
            parse_datetime(data["timestamp"])
        )


class ProjectCreatedEvent(DomainEvent):
    """Event raised when a project is created."""
    
    def __init__(self, project_id, project_name, timestamp=None):
        super().__init__(
            "project_created",
            {
                "project_id": project_id,
                "project_name": project_name
            },
            timestamp
        )


class RequirementCreatedEvent(DomainEvent):
    """Event raised when a requirement is created."""
    
    def __init__(self, requirement_id, project_id, requirement_title, timestamp=None):
        super().__init__(
            "requirement_created",
            {
                "requirement_id": requirement_id,
                "project_id": project_id,
                "requirement_title": requirement_title
            },
            timestamp
        )


class TestCreatedEvent(DomainEvent):
    """Event raised when a test is created."""
    
    def __init__(self, test_id, project_id, test_title, test_type, timestamp=None):
        super().__init__(
            "test_created",
            {
                "test_id": test_id,
                "project_id": project_id,
                "test_title": test_title,
                "test_type": test_type
            },
            timestamp
        )


class CodeGeneratedEvent(DomainEvent):
    """Event raised when code is generated."""
    
    def __init__(self, project_id, file_paths, timestamp=None):
        super().__init__(
            "code_generated",
            {
                "project_id": project_id,
                "file_paths": file_paths
            },
            timestamp
        )


class WorkflowCompletedEvent(DomainEvent):
    """Event raised when a workflow is completed."""
    
    def __init__(self, workflow_id, project_id, workflow_name, timestamp=None):
        super().__init__(
            "workflow_completed",
            {
                "workflow_id": workflow_id,
                "project_id": project_id,
                "workflow_name": workflow_name
            },
            timestamp
        )
```

## 5. Application Layer

The Application Layer contains the use cases and orchestration logic that coordinates the domain layer.

### 5.1 Use Cases

#### 5.1.1 InitProjectUseCase

```python
# [Spec §4.1.1] Project Creation
class InitProjectUseCase:
    """Use case for initializing a new project."""
    
    def __init__(self, project_service, file_system_port, event_bus):
        self.project_service = project_service
        self.file_system_port = file_system_port
        self.event_bus = event_bus
    
    def execute(self, name, template="default", path=None, description=None):
        """Execute the use case."""
        # Create the project
        project, message = self.project_service.create_project(name, template, description)
        if not project:
            return None, message
        
        # Set the project path
        if path:
            project.path = path
        else:
            project.path = f"./{name}"
        
        # Create the project directory structure
        self._create_project_structure(project)
        
        # Publish event
        self.event_bus.publish(ProjectCreatedEvent(project.id, project.name))
        
        return project, "Project initialized successfully"
    
    def _create_project_structure(self, project):
        """Create the project directory structure."""
        # Create the project directory
        self.file_system_port.create_directory(project.path)
        
        # Create subdirectories based on template
        if project.template == "library":
            self._create_library_structure(project)
        elif project.template == "application":
            self._create_application_structure(project)
        elif project.template == "cli":
            self._create_cli_structure(project)
        else:
            self._create_default_structure(project)
        
        # Create configuration files
        self._create_config_files(project)
    
    def _create_library_structure(self, project):
        """Create a library project structure."""
        # Create src directory
        src_path = f"{project.path}/src"
        self.file_system_port.create_directory(src_path)
        
        # Create package directory
        package_path = f"{src_path}/{project.name}"
        self.file_system_port.create_directory(package_path)
        
        # Create __init__.py
        init_path = f"{package_path}/__init__.py"
        self.file_system_port.write_file(init_path, f'"""The {project.name} package."""\n\n__version__ = "0.1.0"\n')
        
        # Create tests directory
        tests_path = f"{project.path}/tests"
        self.file_system_port.create_directory(tests_path)
        
        # Create test_init.py
        test_init_path = f"{tests_path}/test_init.py"
        self.file_system_port.write_file(test_init_path, f'"""Tests for the {project.name} package."""\n\nimport {project.name}\n\ndef test_version():\n    assert {project.name}.__version__ == "0.1.0"\n')
        
        # Create docs directory
        docs_path = f"{project.path}/docs"
        self.file_system_port.create_directory(docs_path)
    
    def _create_application_structure(self, project):
        """Create an application project structure."""
        # Create src directory
        src_path = f"{project.path}/src"
        self.file_system_port.create_directory(src_path)
        
        # Create app directory
        app_path = f"{src_path}/{project.name}"
        self.file_system_port.create_directory(app_path)
        
        # Create __init__.py
        init_path = f"{app_path}/__init__.py"
        self.file_system_port.write_file(init_path, f'"""The {project.name} application."""\n\n__version__ = "0.1.0"\n')
        
        # Create main.py
        main_path = f"{app_path}/main.py"
        self.file_system_port.write_file(main_path, f'"""Main module for the {project.name} application."""\n\ndef main():\n    """Run the application."""\n    print("Hello, world!")\n\nif __name__ == "__main__":\n    main()\n')
        
        # Create tests directory
        tests_path = f"{project.path}/tests"
        self.file_system_port.create_directory(tests_path)
        
        # Create test_main.py
        test_main_path = f"{tests_path}/test_main.py"
        self.file_system_port.write_file(test_main_path, f'"""Tests for the main module."""\n\nfrom {project.name}.main import main\n\ndef test_main(capsys):\n    """Test the main function."""\n    main()\n    captured = capsys.readouterr()\n    assert "Hello, world!" in captured.out\n')
        
        # Create docs directory
        docs_path = f"{project.path}/docs"
        self.file_system_port.create_directory(docs_path)
    
    def _create_cli_structure(self, project):
        """Create a CLI project structure."""
        # Create src directory
        src_path = f"{project.path}/src"
        self.file_system_port.create_directory(src_path)
        
        # Create cli directory
        cli_path = f"{src_path}/{project.name}"
        self.file_system_port.create_directory(cli_path)
        
        # Create __init__.py
        init_path = f"{cli_path}/__init__.py"
        self.file_system_port.write_file(init_path, f'"""The {project.name} CLI."""\n\n__version__ = "0.1.0"\n')
        
        # Create cli.py
        cli_path = f"{cli_path}/cli.py"
        self.file_system_port.write_file(cli_path, f'"""Command-line interface for {project.name}."""\n\nimport typer\n\napp = typer.Typer()\n\n@app.command()\ndef hello(name: str = "World"):\n    """Say hello to someone."""\n    typer.echo(f"Hello, {{name}}!")\n\ndef main():\n    """Run the CLI."""\n    app()\n\nif __name__ == "__main__":\n    main()\n')
        
        # Create tests directory
        tests_path = f"{project.path}/tests"
        self.file_system_port.create_directory(tests_path)
        
        # Create test_cli.py
        test_cli_path = f"{tests_path}/test_cli.py"
        self.file_system_port.write_file(test_cli_path, f'"""Tests for the CLI."""\n\nfrom typer.testing import CliRunner\nfrom {project.name}.cli import app\n\nrunner = CliRunner()\n\ndef test_hello():\n    """Test the hello command."""\n    result = runner.invoke(app, ["hello"])\n    assert result.exit_code == 0\n    assert "Hello, World!" in result.stdout\n\n    result = runner.invoke(app, ["hello", "Alice"])\n    assert result.exit_code == 0\n    assert "Hello, Alice!" in result.stdout\n')
        
        # Create docs directory
        docs_path = f"{project.path}/docs"
        self.file_system_port.create_directory(docs_path)
    
    def _create_default_structure(self, project):
        """Create a default project structure."""
        # Create src directory
        src_path = f"{project.path}/src"
        self.file_system_port.create_directory(src_path)
        
        # Create __init__.py
        init_path = f"{src_path}/__init__.py"
        self.file_system_port.write_file(init_path, f'"""The {project.name} package."""\n\n__version__ = "0.1.0"\n')
        
        # Create tests directory
        tests_path = f"{project.path}/tests"
        self.file_system_port.create_directory(tests_path)
        
        # Create docs directory
        docs_path = f"{project.path}/docs"
        self.file_system_port.create_directory(docs_path)
    
    def _create_config_files(self, project):
        """Create configuration files for the project."""
        # Create README.md
        readme_path = f"{project.path}/README.md"
        readme_content = f"# {project.name}\n\n"
        if project.description:
            readme_content += f"{project.description}\n\n"
        readme_content += "## Installation\n\n```bash\npip install .\n```\n\n"
        readme_content += "## Usage\n\n```python\n# Add usage examples here\n```\n\n"
        readme_content += "## License\n\nMIT\n"
        self.file_system_port.write_file(readme_path, readme_content)
        
        # Create pyproject.toml
        pyproject_path = f"{project.path}/pyproject.toml"
        pyproject_content = f'[build-system]\nrequires = ["setuptools>=42", "wheel"]\nbuild-backend = "setuptools.build_meta"\n\n'
        pyproject_content += f'[project]\nname = "{project.name}"\nversion = "0.1.0"\ndescription = "{project.description or ""}"\n'
        pyproject_content += f'authors = [{{"name" = "Your Name", "email" = "your.email@example.com"}}]\n'
        pyproject_content += f'readme = "README.md"\nrequires-python = ">=3.8"\n\n'
        pyproject_content += f'[project.optional-dependencies]\ndev = ["pytest>=6.0", "pytest-cov>=2.12"]\n\n'
        
        if project.template == "cli":
            pyproject_content += f'[project.scripts]\n{project.name} = "{project.name}.cli:main"\n'
        
        self.file_system_port.write_file(pyproject_path, pyproject_content)
        
        # Create .gitignore
        gitignore_path = f"{project.path}/.gitignore"
        gitignore_content = "# Byte-compiled / optimized / DLL files\n__pycache__/\n*.py[cod]\n*$py.class\n\n"
        gitignore_content += "# Distribution / packaging\ndist/\nbuild/\n*.egg-info/\n\n"
        gitignore_content += "# Unit test / coverage reports\n.coverage\nhtmlcov/\n.pytest_cache/\n\n"
        gitignore_content += "# Environments\n.env\n.venv\nenv/\nvenv/\nENV/\nenv.bak/\nvenv.bak/\n\n"
        gitignore_content += "# IDE\n.idea/\n.vscode/\n*.swp\n*.swo\n"
        self.file_system_port.write_file(gitignore_path, gitignore_content)
        
        # Create .DevSynth.yaml
        devsynth_path = f"{project.path}/.DevSynth.yaml"
        devsynth_content = f"project:\n  name: {project.name}\n  template: {project.template}\n\n"
        devsynth_content += "llm:\n  provider: openai\n  model: gpt-4\n\n"
        devsynth_content += "agents:\n  enabled: true\n  dialectical: true\n\n"
        devsynth_content += "memory:\n  persistence: true\n  vector_store: true\n"
        self.file_system_port.write_file(devsynth_path, devsynth_content)
```

#### 5.1.2 GenerateSpecificationUseCase

```python
# [Spec §4.2.2] Specification Generation
class GenerateSpecificationUseCase:
    """Use case for generating a specification from requirements."""
    
    def __init__(self, requirement_service, file_system_port, agent_system, event_bus):
        self.requirement_service = requirement_service
        self.file_system_port = file_system_port
        self.agent_system = agent_system
        self.event_bus = event_bus
    
    def execute(self, project_id, output_path=None):
        """Execute the use case."""
        # Generate specification from requirements
        specification, message = self.requirement_service.generate_specification(project_id)
        if not specification:
            return None, message
        
        # Use the agent system to refine the specification
        task = {
            "type": "refine_specification",
            "inputs": {
                "specification": specification
            }
        }
        
        result = self.agent_system.execute_task(task)
        if not result.success:
            return None, result.error
        
        refined_specification = result.outputs["refined_specification"]
        
        # Write the specification to a file if output_path is provided
        if output_path:
            # Convert specification to markdown
            markdown = self._specification_to_markdown(refined_specification)
            
            # Write to file
            self.file_system_port.write_file(output_path, markdown)
        
        # Publish event
        self.event_bus.publish(DomainEvent("specification_generated", {
            "project_id": project_id,
            "specification": refined_specification
        }))
        
        return refined_specification, "Specification generated successfully"
    
    def _specification_to_markdown(self, specification):
        """Convert a specification to markdown format."""
        markdown = f"# {specification['project_name']} Specification\n\n"
        
        if specification.get('project_description'):
            markdown += f"{specification['project_description']}\n\n"
        
        for section in specification['sections']:
            markdown += f"## {section['title']}\n\n"
            
            for req in section['requirements']:
                markdown += f"### {req['title']}\n\n"
                markdown += f"**Priority:** {req['priority']}\n\n"
                markdown += f"{req['description']}\n\n"
        
        return markdown
```

#### 5.1.3 GenerateTestsUseCase

```python
# [Spec §4.3] Test-Driven Development
class GenerateTestsUseCase:
    """Use case for generating tests from a specification."""
    
    def __init__(self, test_service, file_system_port, agent_system, event_bus):
        self.test_service = test_service
        self.file_system_port = file_system_port
        self.agent_system = agent_system
        self.event_bus = event_bus
    
    def execute(self, specification, output_path=None, test_type="both"):
        """Execute the use case."""
        # Use the agent system to generate tests from the specification
        task = {
            "type": "generate_tests",
            "inputs": {
                "specification": specification,
                "test_type": test_type
            }
        }
        
        result = self.agent_system.execute_task(task)
        if not result.success:
            return None, result.error
        
        tests = result.outputs["tests"]
        
        # Save the tests to the database
        saved_tests = []
        for test in tests:
            if test["type"] == "bdd":
                # Create BDD test
                bdd_test, message = self.test_service.create_bdd_test(
                    specification["project_id"],
                    test["title"],
                    test["feature"],
                    test.get("description")
                )
                
                if bdd_test:
                    # Add scenarios
                    for scenario in test["scenarios"]:
                        self.test_service.add_scenario_to_bdd_test(
                            bdd_test.id,
                            scenario["title"],
                            scenario["given"],
                            scenario["when"],
                            scenario["then"]
                        )
                    
                    # Link to requirements
                    for req_id in test["requirements"]:
                        self.test_service.link_test_to_requirement(bdd_test.id, req_id)
                    
                    saved_tests.append(bdd_test)
            
            elif test["type"] == "unit":
                # Create unit test
                unit_test, message = self.test_service.create_unit_test(
                    specification["project_id"],
                    test["title"],
                    test["function_name"],
                    test.get("description")
                )
                
                if unit_test:
                    # Add test cases
                    for test_case in test["test_cases"]:
                        self.test_service.add_test_case_to_unit_test(
                            unit_test.id,
                            test_case["inputs"],
                            test_case["expected_output"],
                            test_case["assertions"]
                        )
                    
                    # Link to requirements
                    for req_id in test["requirements"]:
                        self.test_service.link_test_to_requirement(unit_test.id, req_id)
                    
                    saved_tests.append(unit_test)
        
        # Write the tests to files if output_path is provided
        if output_path:
            self._write_tests_to_files(saved_tests, output_path)
        
        # Publish event
        self.event_bus.publish(DomainEvent("tests_generated", {
            "project_id": specification["project_id"],
            "test_count": len(saved_tests)
        }))
        
        return saved_tests, "Tests generated successfully"
    
    def _write_tests_to_files(self, tests, output_path):
        """Write tests to files."""
        # Create the output directory if it doesn't exist
        self.file_system_port.create_directory(output_path)
        
        for test in tests:
            if isinstance(test, BDDTest):
                # Write BDD test to a feature file
                feature_path = f"{output_path}/{sanitize(test.title)}.feature"
                feature_content = f"Feature: {test.feature}\n\n"
                
                for scenario in test.scenarios:
                    feature_content += scenario.to_gherkin() + "\n\n"
                
                self.file_system_port.write_file(feature_path, feature_content)
                
                # Write step definitions to a Python file
                steps_path = f"{output_path}/steps_{sanitize(test.title)}.py"
                steps_content = f'"""Step definitions for {test.title}."""\n\n'
                steps_content += 'from pytest_bdd import given, when, then\n\n'
                
                step_definitions = test.generate_step_definitions()
                for step_def in step_definitions:
                    steps_content += f"{step_def['implementation']}\n\n"
                
                self.file_system_port.write_file(steps_path, steps_content)
            
            elif isinstance(test, UnitTest):
                # Write unit test to a Python file
                test_path = f"{output_path}/test_{sanitize(test.function_name)}.py"
                test_content = f'"""Unit tests for {test.function_name}."""\n\n'
                test_content += 'import pytest\n\n'
                test_content += test.generate_test_code()
                
                self.file_system_port.write_file(test_path, test_content)
```

#### 5.1.4 GenerateCodeUseCase

```python
# [Spec §4.4] Code Generation and Implementation
class GenerateCodeUseCase:
    """Use case for generating code from tests."""
    
    def __init__(self, code_service, test_service, file_system_port, agent_system, event_bus):
        self.code_service = code_service
        self.test_service = test_service
        self.file_system_port = file_system_port
        self.agent_system = agent_system
        self.event_bus = event_bus
    
    def execute(self, test_ids, output_path):
        """Execute the use case."""
        # Get the tests
        tests = []
        for test_id in test_ids:
            test = self.test_service.test_repository.get_by_id(test_id)
            if test:
                tests.append(test)
        
        if not tests:
            return None, "No tests found"
        
        # Use the agent system to generate code from the tests
        task = {
            "type": "generate_code",
            "inputs": {
                "tests": tests
            }
        }
        
        result = self.agent_system.execute_task(task)
        if not result.success:
            return None, result.error
        
        generated_code = result.outputs["generated_code"]
        
        # Write the generated code to files
        file_paths = []
        for name, code in generated_code.items():
            file_path = f"{output_path}/{name}.py"
            self.file_system_port.write_file(file_path, code)
            file_paths.append(file_path)
        
        # Publish event
        self.event_bus.publish(CodeGeneratedEvent(
            tests[0].project_id,  # Assuming all tests are from the same project
            file_paths
        ))
        
        return generated_code, "Code generated successfully"
```

#### 5.1.5 RunTestsUseCase

```python
# [Spec §4.3.3] Test Execution
class RunTestsUseCase:
    """Use case for running tests."""
    
    def __init__(self, test_service, file_system_port, event_bus):
        self.test_service = test_service
        self.file_system_port = file_system_port
        self.event_bus = event_bus
    
    def execute(self, project_id, test_type="all", verbose=False):
        """Execute the use case."""
        # Get the tests for the project
        if test_type == "all":
            tests = self.test_service.test_repository.get_by_project_id(project_id)
        else:
            tests = self.test_service.test_repository.get_by_project_id_and_type(project_id, test_type)
        
        if not tests:
            return None, "No tests found"
        
        # Run the tests
        results = self._run_tests(tests, verbose)
        
        # Update test statuses
        for test_id, result in results.items():
            test = self.test_service.test_repository.get_by_id(test_id)
            if test:
                test.update_status("passing" if result["passed"] else "failing")
                self.test_service.test_repository.save(test)
        
        # Publish event
        self.event_bus.publish(DomainEvent("tests_run", {
            "project_id": project_id,
            "test_count": len(tests),
            "passed_count": sum(1 for result in results.values() if result["passed"]),
            "failed_count": sum(1 for result in results.values() if not result["passed"])
        }))
        
        return results, "Tests run successfully"
    
    def _run_tests(self, tests, verbose):
        """Run the tests and return the results."""
        # This would use pytest in the real implementation
        # For pseudocode, we'll just simulate the results
        
        results = {}
        
        for test in tests:
            # Simulate running the test
            if isinstance(test, BDDTest):
                # Run BDD test
                passed = self._run_bdd_test(test, verbose)
            elif isinstance(test, UnitTest):
                # Run unit test
                passed = self._run_unit_test(test, verbose)
            else:
                # Unknown test type
                passed = False
            
            results[test.id] = {
                "passed": passed,
                "output": f"Test {'passed' if passed else 'failed'}"
            }
        
        return results
    
    def _run_bdd_test(self, test, verbose):
        """Run a BDD test and return whether it passed."""
        # This would use pytest-bdd in the real implementation
        # For pseudocode, we'll just simulate the result
        
        # Simulate a 90% pass rate
        return random.random() < 0.9
    
    def _run_unit_test(self, test, verbose):
        """Run a unit test and return whether it passed."""
        # This would use pytest in the real implementation
        # For pseudocode, we'll just simulate the result
        
        # Simulate an 80% pass rate
        return random.random() < 0.8
```

#### 5.1.6 GenerateDocumentationUseCase

```python
# [Spec §4.5] Documentation Generation
class GenerateDocumentationUseCase:
    """Use case for generating documentation."""
    
    def __init__(self, documentation_service, file_system_port, agent_system, event_bus):
        self.documentation_service = documentation_service
        self.file_system_port = file_system_port
        self.agent_system = agent_system
        self.event_bus = event_bus
    
    def execute(self, project_id, doc_type, source_path=None, output_path=None):
        """Execute the use case."""
        if doc_type == "api":
            # Generate API documentation
            if not source_path:
                return None, "Source path is required for API documentation"
            
            if not output_path:
                output_path = "docs/api"
            
            output_file, message = self.documentation_service.generate_api_documentation(
                project_id, source_path, output_path
            )
            
            if not output_file:
                return None, message
            
            # Use the agent system to refine the documentation
            task = {
                "type": "refine_api_documentation",
                "inputs": {
                    "documentation_path": output_file
                }
            }
            
            result = self.agent_system.execute_task(task)
            if not result.success:
                return None, result.error
            
            # Publish event
            self.event_bus.publish(DomainEvent("api_documentation_generated", {
                "project_id": project_id,
                "output_file": output_file
            }))
            
            return output_file, "API documentation generated successfully"
        
        elif doc_type == "user":
            # Generate user documentation
            if not output_path:
                output_path = "docs/user"
            
            output_file, message = self.documentation_service.generate_user_documentation(
                project_id, output_path
            )
            
            if not output_file:
                return None, message
            
            # Use the agent system to refine the documentation
            task = {
                "type": "refine_user_documentation",
                "inputs": {
                    "documentation_path": output_file
                }
            }
            
            result = self.agent_system.execute_task(task)
            if not result.success:
                return None, result.error
            
            # Publish event
            self.event_bus.publish(DomainEvent("user_documentation_generated", {
                "project_id": project_id,
                "output_file": output_file
            }))
            
            return output_file, "User documentation generated successfully"
        
        else:
            return None, f"Unknown documentation type: {doc_type}"
```

### 5.2 Orchestration

#### 5.2.1 WorkflowOrchestrator

```python
# [Spec §3.2.2] Orchestration Layer
class WorkflowOrchestrator:
    """Orchestrates workflows and manages state."""
    
    def __init__(self, agent_system, state_manager, event_bus):
        self.agent_system = agent_system
        self.state_manager = state_manager
        self.event_bus = event_bus
        self.workflows = {}  # Dictionary of active workflows
    
    def create_workflow(self, workflow_id, project_id, name, description=None):
        """Create a new workflow."""
        workflow = Workflow(workflow_id, project_id, name, description)
        self.workflows[workflow_id] = workflow
        return workflow
    
    def add_step(self, workflow_id, step):
        """Add a step to a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False, "Workflow not found"
        
        workflow.add_step(step)
        return True, "Step added successfully"
    
    def execute_workflow(self, workflow_id):
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False, "Workflow not found"
        
        # Update workflow status
        workflow.update_status("running")
        
        # Save initial state
        self.state_manager.save_workflow_state(workflow)
        
        # Execute steps sequentially
        while not workflow.is_complete() and workflow.status != "failed":
            # Get the current step
            step = workflow.current_step_object()
            if not step:
                break
            
            # Update step status
            step.update_status("running")
            self.state_manager.save_workflow_state(workflow)
            
            # Execute the step
            success, message = self._execute_step(step)
            
            if success:
                # Update step status
                step.update_status("completed")
                
                # Advance to the next step
                if not workflow.advance():
                    # No more steps, workflow is complete
                    workflow.update_status("completed")
            else:
                # Step failed
                step.update_status("failed")
                workflow.update_status("failed")
            
            # Save updated state
            self.state_manager.save_workflow_state(workflow)
        
        # Publish workflow completion event
        if workflow.status == "completed":
            self.event_bus.publish(WorkflowCompletedEvent(
                workflow.id, workflow.project_id, workflow.name
            ))
        
        return workflow.status == "completed", f"Workflow {workflow.status}"
    
    def _execute_step(self, step):
        """Execute a workflow step."""
        # Create a task for the agent
        task = Task(
            generate_uuid(),
            step.agent_id,
            step.task_type,
            step.inputs
        )
        
        # Assign the task to the agent
        agent = self.agent_system.get_agent(step.agent_id)
        if not agent:
            return False, f"Agent {step.agent_id} not found"
        
        # Execute the task
        result = self.agent_system.execute_task_with_agent(agent, task)
        
        if result.success:
            # Update step outputs
            for key, value in result.outputs.items():
                step.set_output(key, value)
            
            return True, "Step executed successfully"
        else:
            return False, result.error
    
    def pause_workflow(self, workflow_id):
        """Pause a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False, "Workflow not found"
        
        if workflow.status != "running":
            return False, f"Workflow is not running (status: {workflow.status})"
        
        workflow.update_status("paused")
        self.state_manager.save_workflow_state(workflow)
        
        return True, "Workflow paused successfully"
    
    def resume_workflow(self, workflow_id):
        """Resume a paused workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False, "Workflow not found"
        
        if workflow.status != "paused":
            return False, f"Workflow is not paused (status: {workflow.status})"
        
        workflow.update_status("running")
        self.state_manager.save_workflow_state(workflow)
        
        # Continue execution
        return self.execute_workflow(workflow_id)
    
    def get_workflow_status(self, workflow_id):
        """Get the status of a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None, "Workflow not found"
        
        return {
            "id": workflow.id,
            "project_id": workflow.project_id,
            "name": workflow.name,
            "status": workflow.status,
            "progress": workflow.progress(),
            "current_step": workflow.current_step,
            "step_count": len(workflow.steps)
        }, "Workflow status retrieved successfully"
    
    def load_workflow(self, workflow_id):
        """Load a workflow from the state manager."""
        workflow = self.state_manager.load_workflow_state(workflow_id)
        if workflow:
            self.workflows[workflow_id] = workflow
            return workflow, "Workflow loaded successfully"
        else:
            return None, "Workflow not found"
```

#### 5.2.2 StateManager

```python
# [Spec §3.2.2] Orchestration Layer - State Manager
class StateManager:
    """Manages workflow state and persistence."""
    
    def __init__(self, storage_port):
        self.storage_port = storage_port
    
    def save_workflow_state(self, workflow):
        """Save the state of a workflow."""
        # Serialize the workflow
        serialized = self._serialize_workflow(workflow)
        
        # Save to storage
        self.storage_port.save_workflow(workflow.id, serialized)
        
        return True
    
    def load_workflow_state(self, workflow_id):
        """Load the state of a workflow."""
        # Load from storage
        serialized = self.storage_port.load_workflow(workflow_id)
        if not serialized:
            return None
        
        # Deserialize the workflow
        workflow = self._deserialize_workflow(serialized)
        
        return workflow
    
    def list_workflows(self, project_id=None):
        """List all workflows, optionally filtered by project_id."""
        # Load workflow summaries from storage
        serialized_summaries = self.storage_port.list_workflows(project_id)
        
        # Deserialize the summaries
        summaries = []
        for summary in serialized_summaries:
            summaries.append({
                "id": summary["id"],
                "project_id": summary["project_id"],
                "name": summary["name"],
                "status": summary["status"],
                "created_at": summary["created_at"],
                "updated_at": summary["updated_at"]
            })
        
        return summaries
    
    def delete_workflow_state(self, workflow_id):
        """Delete the state of a workflow."""
        # Delete from storage
        self.storage_port.delete_workflow(workflow_id)
        
        return True
    
    def _serialize_workflow(self, workflow):
        """Serialize a workflow to a dictionary."""
        steps = []
        for step in workflow.steps:
            steps.append({
                "id": step.id,
                "workflow_id": step.workflow_id,
                "name": step.name,
                "description": step.description,
                "agent_id": step.agent_id,
                "task_type": step.task_type,
                "inputs": step.inputs,
                "outputs": step.outputs,
                "status": step.status
            })
        
        return {
            "id": workflow.id,
            "project_id": workflow.project_id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status,
            "steps": steps,
            "current_step": workflow.current_step,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat()
        }
    
    def _deserialize_workflow(self, serialized):
        """Deserialize a workflow from a dictionary."""
        workflow = Workflow(
            serialized["id"],
            serialized["project_id"],
            serialized["name"],
            serialized["description"]
        )
        
        workflow.status = serialized["status"]
        workflow.current_step = serialized["current_step"]
        workflow.created_at = parse_datetime(serialized["created_at"])
        workflow.updated_at = parse_datetime(serialized["updated_at"])
        
        for step_data in serialized["steps"]:
            step = WorkflowStep(
                step_data["id"],
                step_data["workflow_id"],
                step_data["name"],
                step_data["agent_id"],
                step_data["task_type"],
                step_data["inputs"]
            )
            
            step.description = step_data["description"]
            step.outputs = step_data["outputs"]
            step.status = step_data["status"]
            
            workflow.add_step(step)
        
        return workflow
```

#### 5.2.3 HumanInterventionHandler

```python
# [Spec §3.2.2] Orchestration Layer - Human Intervention Handler
class HumanInterventionHandler:
    """Manages points where human input is required."""
    
    def __init__(self, cli_port, event_bus):
        self.cli_port = cli_port
        self.event_bus = event_bus
        self.pending_interventions = {}  # Dictionary of pending interventions
    
    def request_intervention(self, intervention_id, workflow_id, step_id, prompt, options=None):
        """Request human intervention."""
        # Create intervention request
        intervention = {
            "id": intervention_id,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "prompt": prompt,
            "options": options,
            "status": "pending",
            "response": None,
            "created_at": current_time()
        }
        
        # Store the intervention
        self.pending_interventions[intervention_id] = intervention
        
        # Publish event
        self.event_bus.publish(DomainEvent("human_intervention_requested", {
            "intervention_id": intervention_id,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "prompt": prompt,
            "options": options
        }))
        
        # Display the prompt to the user
        self.cli_port.display_intervention_prompt(intervention)
        
        return intervention
    
    def provide_response(self, intervention_id, response):
        """Provide a response to an intervention request."""
        intervention = self.pending_interventions.get(intervention_id)
        if not intervention:
            return False, "Intervention not found"
        
        if intervention["status"] != "pending":
            return False, f"Intervention is not pending (status: {intervention['status']})"
        
        # Update the intervention
        intervention["status"] = "completed"
        intervention["response"] = response
        intervention["completed_at"] = current_time()
        
        # Publish event
        self.event_bus.publish(DomainEvent("human_intervention_completed", {
            "intervention_id": intervention_id,
            "workflow_id": intervention["workflow_id"],
            "step_id": intervention["step_id"],
            "response": response
        }))
        
        return True, "Response provided successfully"
    
    def get_intervention(self, intervention_id):
        """Get an intervention by ID."""
        intervention = self.pending_interventions.get(intervention_id)
        if not intervention:
            return None, "Intervention not found"
        
        return intervention, "Intervention retrieved successfully"
    
    def list_pending_interventions(self, workflow_id=None):
        """List all pending interventions, optionally filtered by workflow_id."""
        pending = []
        for intervention in self.pending_interventions.values():
            if intervention["status"] == "pending":
                if workflow_id is None or intervention["workflow_id"] == workflow_id:
                    pending.append(intervention)
        
        return pending
    
    def cancel_intervention(self, intervention_id):
        """Cancel an intervention request."""
        intervention = self.pending_interventions.get(intervention_id)
        if not intervention:
            return False, "Intervention not found"
        
        if intervention["status"] != "pending":
            return False, f"Intervention is not pending (status: {intervention['status']})"
        
        # Update the intervention
        intervention["status"] = "cancelled"
        
        # Publish event
        self.event_bus.publish(DomainEvent("human_intervention_cancelled", {
            "intervention_id": intervention_id,
            "workflow_id": intervention["workflow_id"],
            "step_id": intervention["step_id"]
        }))
        
        return True, "Intervention cancelled successfully"
```

### 5.3 Agent System

#### 5.3.1 AgentSystem

```python
# [Spec §3.2.3] Agent System
class AgentSystem:
    """Manages AI agents and their tasks."""
    
    def __init__(self, llm_port, memory_port, promise_system, core_values_system, event_bus):
        self.llm_port = llm_port
        self.memory_port = memory_port
        self.promise_system = promise_system
        self.core_values_system = core_values_system
        self.event_bus = event_bus
        self.agents = {}  # Dictionary of agents by ID
        self.primus_manager = PrimusManager(self)
    
    def register_agent(self, agent):
        """Register an agent with the system."""
        self.agents[agent.id] = agent
        return True
    
    def get_agent(self, agent_id):
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agents_by_capability(self, capability):
        """Get all agents with a specific capability."""
        return [agent for agent in self.agents.values() if capability in agent.capabilities]
    
    def execute_task(self, task_data):
        """Execute a task with an appropriate agent."""
        # Create a task
        task_id = generate_uuid()
        task_type = task_data["type"]
        inputs = task_data.get("inputs", {})
        
        task = Task(task_id, None, task_type, inputs)
        
        # Find an agent with the required capability
        agents = self.get_agents_by_capability(task_type)
        if not agents:
            return TaskResult(False, f"No agent found with capability: {task_type}")
        
        # Select the first available agent
        for agent in agents:
            if agent.status == "idle":
                return self.execute_task_with_agent(agent, task)
        
        # No available agent, use the first one anyway
        return self.execute_task_with_agent(agents[0], task)
    
    def execute_task_with_agent(self, agent, task):
        """Execute a task with a specific agent."""
        # Check if the agent can handle the task
        if not agent.can_handle(task.task_type):
            return TaskResult(False, f"Agent {agent.id} cannot handle task type: {task.task_type}")
        
        # Check if the task aligns with core values
        value_check = self.core_values_system.check_task(task)
        if not value_check.aligned:
            return TaskResult(False, f"Task violates core values: {value_check.reason}")
        
        # Assign the task to the agent
        task.agent_id = agent.id
        agent.assign_task(task)
        
        # Publish event
        self.event_bus.publish(DomainEvent("task_assigned", {
            "task_id": task.id,
            "agent_id": agent.id,
            "task_type": task.task_type
        }))
        
        # Execute the task
        try:
            # Update task status
            task.update_status("running")
            
            # Get context from memory
            context = self.memory_port.get_context_for_task(task)
            
            # Prepare the prompt
            prompt = self._prepare_prompt(agent, task, context)
            
            # Call the LLM
            llm_response = self.llm_port.generate_text(prompt)
            
            # Parse the response
            outputs = self._parse_response(llm_response, task.task_type)
            
            # Update task outputs
            for key, value in outputs.items():
                task.set_output(key, value)
            
            # Update task status
            task.update_status("completed")
            
            # Update agent status
            agent.update_status("idle")
            
            # Store the results in memory
            self.memory_port.store_task_result(task, outputs)
            
            # Publish event
            self.event_bus.publish(DomainEvent("task_completed", {
                "task_id": task.id,
                "agent_id": agent.id,
                "task_type": task.task_type
            }))
            
            return TaskResult(True, "Task completed successfully", outputs)
        
        except Exception as e:
            # Update task status
            task.update_status("failed")
            task.set_error(str(e))
            
            # Update agent status
            agent.update_status("idle")
            
            # Publish event
            self.event_bus.publish(DomainEvent("task_failed", {
                "task_id": task.id,
                "agent_id": agent.id,
                "task_type": task.task_type,
                "error": str(e)
            }))
            
            return TaskResult(False, f"Task failed: {str(e)}")
    
    def _prepare_prompt(self, agent, task, context):
        """Prepare a prompt for the LLM."""
        # Start with the agent's system prompt
        prompt = agent.system_prompt
        
        # Add task-specific instructions
        prompt += f"\n\nTask: {task.task_type}\n\n"
        
        # Add inputs
        prompt += "Inputs:\n"
        for key, value in task.inputs.items():
            prompt += f"{key}: {value}\n"
        
        # Add context
        if context:
            prompt += "\nContext:\n"
            for key, value in context.items():
                prompt += f"{key}: {value}\n"
        
        # Add output format instructions
        prompt += "\nPlease provide your response in the following format:\n"
        prompt += "```json\n{\n  \"key1\": \"value1\",\n  \"key2\": \"value2\"\n}\n```\n"
        
        return prompt
    
    def _parse_response(self, response, task_type):
        """Parse the LLM response into structured outputs."""
        # Extract JSON from the response
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # If JSON extraction fails, try to parse based on task type
        if task_type == "generate_tests":
            # Parse test generation response
            return self._parse_test_generation_response(response)
        
        elif task_type == "generate_code":
            # Parse code generation response
            return self._parse_code_generation_response(response)
        
        elif task_type == "refine_specification":
            # Parse specification refinement response
            return self._parse_specification_refinement_response(response)
        
        # Default: return the raw response
        return {"raw_response": response}
    
    def _parse_test_generation_response(self, response):
        """Parse a test generation response."""
        # This would be more sophisticated in the real implementation
        # For pseudocode, we'll just return a simple structure
        
        return {
            "tests": [
                {
                    "type": "bdd",
                    "title": "Sample BDD Test",
                    "feature": "Feature: Sample Feature",
                    "scenarios": [
                        {
                            "title": "Sample Scenario",
                            "given": ["a condition"],
                            "when": ["an action is performed"],
                            "then": ["a result is observed"]
                        }
                    ],
                    "requirements": ["req1", "req2"]
                },
                {
                    "type": "unit",
                    "title": "Sample Unit Test",
                    "function_name": "sample_function",
                    "test_cases": [
                        {
                            "inputs": {"param1": "value1"},
                            "expected_output": "expected result",
                            "assertions": ["assert result == expected"]
                        }
                    ],
                    "requirements": ["req1", "req3"]
                }
            ]
        }
    
    def _parse_code_generation_response(self, response):
        """Parse a code generation response."""
        # This would be more sophisticated in the real implementation
        # For pseudocode, we'll just return a simple structure
        
        return {
            "generated_code": {
                "sample_module": "def sample_function(param1):\n    return f\"Result: {param1}\"\n"
            }
        }
    
    def _parse_specification_refinement_response(self, response):
        """Parse a specification refinement response."""
        # This would be more sophisticated in the real implementation
        # For pseudocode, we'll just return a simple structure
        
        return {
            "refined_specification": {
                "project_name": "Sample Project",
                "project_description": "A sample project",
                "sections": [
                    {
                        "title": "Functional Requirements",
                        "requirements": [
                            {
                                "id": "req1",
                                "title": "Sample Requirement",
                                "description": "A sample requirement",
                                "priority": "high"
                            }
                        ]
                    }
                ]
            }
        }
```

#### 5.3.2 PrimusManager

```python
# [Spec §3.2.3] Agent System - Primus Role Manager
class PrimusManager:
    """Manages the Primus role in the WSDE organization."""
    
    def __init__(self, agent_system):
        self.agent_system = agent_system
        self.primus_agent_id = None
        self.primus_expiry = None
        self.primus_history = []  # List of previous Primus agents
    
    def assign_primus(self, agent_id, duration=3600):
        """Assign the Primus role to an agent."""
        # Check if the agent exists
        agent = self.agent_system.get_agent(agent_id)
        if not agent:
            return False, f"Agent {agent_id} not found"
        
        # Record the previous Primus
        if self.primus_agent_id:
            self.primus_history.append({
                "agent_id": self.primus_agent_id,
                "assigned_at": self.primus_expiry - datetime.timedelta(seconds=duration),
                "expired_at": current_time()
            })
        
        # Assign the new Primus
        self.primus_agent_id = agent_id
        self.primus_expiry = current_time() + datetime.timedelta(seconds=duration)
        
        # Publish event
        self.agent_system.event_bus.publish(DomainEvent("primus_assigned", {
            "agent_id": agent_id,
            "expiry": self.primus_expiry.isoformat()
        }))
        
        return True, f"Primus role assigned to agent {agent_id}"
    
    def get_primus(self):
        """Get the current Primus agent."""
        # Check if the Primus role has expired
        if self.primus_expiry and current_time() > self.primus_expiry:
            # Primus has expired, rotate to a new agent
            self._rotate_primus()
        
        return self.agent_system.get_agent(self.primus_agent_id)
    
    def _rotate_primus(self):
        """Rotate the Primus role to a new agent."""
        # Get all agents
        agents = list(self.agent_system.agents.values())
        if not agents:
            return False, "No agents available"
        
        # Filter out the current Primus
        candidates = [agent for agent in agents if agent.id != self.primus_agent_id]
        if not candidates:
            # Only one agent, keep it as Primus
            self.primus_expiry = current_time() + datetime.timedelta(seconds=3600)
            return True, f"Primus role extended for agent {self.primus_agent_id}"
        
        # Select a new Primus (round-robin)
        if self.primus_history:
            # Try to find an agent that hasn't been Primus recently
            recent_primus = [history["agent_id"] for history in self.primus_history[-len(candidates):]]
            for agent in candidates:
                if agent.id not in recent_primus:
                    return self.assign_primus(agent.id)
        
        # Default: select the first candidate
        return self.assign_primus(candidates[0].id)
    
    def is_primus(self, agent_id):
        """Check if an agent is the current Primus."""
        return agent_id == self.primus_agent_id
```

#### 5.3.3 AgentCommunicationProtocol

```python
# [Spec §3.2.3] Agent System - Agent Communication Protocol
class AgentCommunicationProtocol:
    """Standardizes communication between agents."""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.message_handlers = {}  # Dictionary of message handlers by message type
    
    def register_handler(self, message_type, handler):
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler
        return True
    
    def send_message(self, sender_id, receiver_id, message_type, content):
        """Send a message from one agent to another."""
        # Create the message
        message = {
            "message_id": generate_uuid(),
            "sender": sender_id,
            "receiver": receiver_id,
            "message_type": message_type,
            "content": content,
            "timestamp": current_time().isoformat()
        }
        
        # Publish the message as an event
        self.event_bus.publish(DomainEvent("agent_message", message))
        
        return message["message_id"]
    
    def handle_message(self, message):
        """Handle an incoming message."""
        # Get the handler for this message type
        handler = self.message_handlers.get(message["message_type"])
        if not handler:
            return False, f"No handler for message type: {message['message_type']}"
        
        # Call the handler
        return handler(message)
    
    def broadcast(self, sender_id, message_type, content):
        """Broadcast a message to all agents."""
        # Create the message
        message = {
            "message_id": generate_uuid(),
            "sender": sender_id,
            "receiver": "broadcast",
            "message_type": message_type,
            "content": content,
            "timestamp": current_time().isoformat()
        }
        
        # Publish the message as an event
        self.event_bus.publish(DomainEvent("agent_broadcast", message))
        
        return message["message_id"]
```

#### 5.3.4 TaskResult

```python
# [Spec §3.2.3] Agent System - Task Result
class TaskResult:
    """Represents the result of a task execution."""
    
    def __init__(self, success, message, outputs=None):
        self.success = success    # boolean
        self.message = message    # string
        self.outputs = outputs or {}  # Dictionary
    
    def to_dict(self):
        """Convert the result to a dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "outputs": self.outputs
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a result from a dictionary."""
        return cls(
            data["success"],
            data["message"],
            data.get("outputs", {})
        )
```

### 5.4 Core Values Subsystem

```python
# [Spec §3.2.4] Core Values Subsystem
class CoreValuesSystem:
    """Enforces ethical principles and project values."""
    
    def __init__(self, config_port):
        self.config_port = config_port
        self.values = []  # List of core values
        self.load_values()
    
    def load_values(self):
        """Load core values from configuration."""
        values_config = self.config_port.get_values_config()
        self.values = values_config.get("values", [])
        return True
    
    def check_task(self, task):
        """Check if a task aligns with core values."""
        # This would be more sophisticated in the real implementation
        # For pseudocode, we'll just do a simple check
        
        # Check for prohibited task types
        prohibited_tasks = ["generate_harmful_code", "violate_privacy", "bypass_security"]
        if task.task_type in prohibited_tasks:
            return ValueCheckResult(False, f"Task type '{task.task_type}' violates core values")
        
        # Check for prohibited keywords in inputs
        prohibited_keywords = ["hack", "exploit", "bypass", "steal", "illegal"]
        for key, value in task.inputs.items():
            if isinstance(value, str):
                for keyword in prohibited_keywords:
                    if keyword in value.lower():
                        return ValueCheckResult(False, f"Input contains prohibited keyword: {keyword}")
        
        return ValueCheckResult(True, "Task aligns with core values")
    
    def check_output(self, output, task_type):
        """Check if an output aligns with core values."""
        # This would be more sophisticated in the real implementation
        # For pseudocode, we'll just do a simple check
        
        # Check for prohibited content in code
        if task_type == "generate_code":
            prohibited_code = ["rm -rf /", "sudo", "chmod 777", "eval(", "exec("]
            if isinstance(output, str):
                for code in prohibited_code:
                    if code in output:
                        return ValueCheckResult(False, f"Output contains prohibited code: {code}")
        
        return ValueCheckResult(True, "Output aligns with core values")
    
    def add_value(self, value):
        """Add a core value."""
        if value not in self.values:
            self.values.append(value)
            self.config_port.save_values_config({"values": self.values})
            return True
        return False
    
    def remove_value(self, value):
        """Remove a core value."""
        if value in self.values:
            self.values.remove(value)
            self.config_port.save_values_config({"values": self.values})
            return True
        return False
    
    def get_values(self):
        """Get all core values."""
        return self.values
```

#### 5.4.1 ValueCheckResult

```python
# [Spec §3.2.4] Core Values Subsystem - Value Check Result
class ValueCheckResult:
    """Represents the result of a value check."""
    
    def __init__(self, aligned, reason):
        self.aligned = aligned  # boolean
        self.reason = reason    # string
    
    def to_dict(self):
        """Convert the result to a dictionary."""
        return {
            "aligned": self.aligned,
            "reason": self.reason
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a result from a dictionary."""
        return cls(
            data["aligned"],
            data["reason"]
        )
```

### 5.5 Promise System

```python
# [Spec §3.2.5] Promise System
class PromiseSystem:
    """Defines and enforces agent capabilities and constraints."""
    
    def __init__(self, config_port, event_bus):
        self.config_port = config_port
        self.event_bus = event_bus
        self.promises = {}  # Dictionary of promises by ID
        self.agent_promises = {}  # Dictionary of promise IDs by agent ID
        self.load_promises()
    
    def load_promises(self):
        """Load promises from configuration."""
        promises_config = self.config_port.get_promises_config()
        
        for promise_data in promises_config.get("promises", []):
            promise = Promise(
                promise_data["id"],
                promise_data["name"],
                promise_data["description"]
            )
            
            for capability in promise_data.get("capabilities", []):
                promise.add_capability(capability)
            
            for constraint in promise_data.get("constraints", []):
                promise.add_constraint(constraint)
            
            self.promises[promise.id] = promise
        
        for agent_promise in promises_config.get("agent_promises", []):
            agent_id = agent_promise["agent_id"]
            promise_ids = agent_promise["promise_ids"]
            self.agent_promises[agent_id] = promise_ids
        
        return True
    
    def save_promises(self):
        """Save promises to configuration."""
        promises_data = []
        for promise in self.promises.values():
            promises_data.append({
                "id": promise.id,
                "name": promise.name,
                "description": promise.description,
                "capabilities": promise.capabilities,
                "constraints": promise.constraints
            })
        
        agent_promises_data = []
        for agent_id, promise_ids in self.agent_promises.items():
            agent_promises_data.append({
                "agent_id": agent_id,
                "promise_ids": promise_ids
            })
        
        self.config_port.save_promises_config({
            "promises": promises_data,
            "agent_promises": agent_promises_data
        })
        
        return True
    
    def create_promise(self, name, description):
        """Create a new promise."""
        promise_id = generate_uuid()
        promise = Promise(promise_id, name, description)
        self.promises[promise_id] = promise
        self.save_promises()
        
        # Publish event
        self.event_bus.publish(DomainEvent("promise_created", {
            "promise_id": promise_id,
            "name": name
        }))
        
        return promise
    
    def add_capability_to_promise(self, promise_id, capability):
        """Add a capability to a promise."""
        promise = self.promises.get(promise_id)
        if not promise:
            return False, f"Promise {promise_id} not found"
        
        promise.add_capability(capability)
        self.save_promises()
        
        return True, f"Capability {capability} added to promise {promise_id}"
    
    def add_constraint_to_promise(self, promise_id, constraint):
        """Add a constraint to a promise."""
        promise = self.promises.get(promise_id)
        if not promise:
            return False, f"Promise {promise_id} not found"
        
        promise.add_constraint(constraint)
        self.save_promises()
        
        return True, f"Constraint {constraint} added to promise {promise_id}"
    
    def assign_promise_to_agent(self, agent_id, promise_id):
        """Assign a promise to an agent."""
        promise = self.promises.get(promise_id)
        if not promise:
            return False, f"Promise {promise_id} not found"
        
        if agent_id not in self.agent_promises:
            self.agent_promises[agent_id] = []
        
        if promise_id not in self.agent_promises[agent_id]:
            self.agent_promises[agent_id].append(promise_id)
            self.save_promises()
        
        # Publish event
        self.event_bus.publish(DomainEvent("promise_assigned", {
            "agent_id": agent_id,
            "promise_id": promise_id
        }))
        
        return True, f"Promise {promise_id} assigned to agent {agent_id}"
    
    def get_agent_capabilities(self, agent_id):
        """Get all capabilities of an agent."""
        promise_ids = self.agent_promises.get(agent_id, [])
        capabilities = set()
        
        for promise_id in promise_ids:
            promise = self.promises.get(promise_id)
            if promise:
                capabilities.update(promise.capabilities)
        
        return list(capabilities)
    
    def can_agent_use_capability(self, agent_id, capability):
        """Check if an agent can use a specific capability."""
        promise_ids = self.agent_promises.get(agent_id, [])
        
        for promise_id in promise_ids:
            promise = self.promises.get(promise_id)
            if promise and capability in promise.capabilities:
                return True
        
        return False
    
    def authorize_capability(self, agent_id, capability):
        """Authorize an agent to use a capability."""
        if not self.can_agent_use_capability(agent_id, capability):
            return False, f"Agent {agent_id} is not authorized to use capability: {capability}"
        
        # Publish event
        self.event_bus.publish(DomainEvent("capability_authorized", {
            "agent_id": agent_id,
            "capability": capability
        }))
        
        return True, f"Agent {agent_id} authorized to use capability: {capability}"
```

## 6. Adapter Layer

The Adapter Layer contains interfaces to external systems, following the Ports and Adapters pattern.

### 6.1 CLI Interface

```python
# [Spec §3.2.1] CLI Interface Layer
class CLIPort:
    """Port for the CLI interface."""
    
    def display_message(self, message):
        """Display a message to the user."""
        pass
    
    def display_error(self, error):
        """Display an error message to the user."""
        pass
    
    def display_success(self, message):
        """Display a success message to the user."""
        pass
    
    def display_progress(self, progress, total, message):
        """Display a progress indicator."""
        pass
    
    def display_intervention_prompt(self, intervention):
        """Display an intervention prompt to the user."""
        pass
    
    def get_user_input(self, prompt, options=None):
        """Get input from the user."""
        pass
    
    def get_user_confirmation(self, prompt):
        """Get confirmation from the user."""
        pass
```

### 6.2 LLM Provider Interfaces

```python
# [Spec §3.2.7] LLM Backend Abstraction
class LLMPort:
    """Port for LLM providers."""
    
    def generate_text(self, prompt, model=None, temperature=0.7, max_tokens=None):
        """Generate text from a prompt."""
        pass
    
    def get_embedding(self, text, model=None):
        """Get an embedding for a text."""
        pass
    
    def count_tokens(self, text, model=None):
        """Count the number of tokens in a text."""
        pass
    
    def get_available_models(self):
        """Get a list of available models."""
        pass
```

### 6.3 File System Interface

```python
# [Spec §4.1.1] Project Creation
class FileSystemPort:
    """Port for file system operations."""
    
    def read_file(self, path):
        """Read a file."""
        pass
    
    def write_file(self, path, content):
        """Write to a file."""
        pass
    
    def append_file(self, path, content):
        """Append to a file."""
        pass
    
    def delete_file(self, path):
        """Delete a file."""
        pass
    
    def file_exists(self, path):
        """Check if a file exists."""
        pass
    
    def create_directory(self, path):
        """Create a directory."""
        pass
    
    def delete_directory(self, path):
        """Delete a directory."""
        pass
    
    def directory_exists(self, path):
        """Check if a directory exists."""
        pass
    
    def list_files(self, path, pattern=None):
        """List files in a directory."""
        pass
    
    def list_directories(self, path):
        """List subdirectories in a directory."""
        pass
```

### 6.4 Memory Interface

```python
# [Spec §3.2.6] Memory and Context System
class MemoryPort:
    """Port for memory and context operations."""
    
    def get_context_for_task(self, task):
        """Get context for a task."""
        pass
    
    def store_task_result(self, task, outputs):
        """Store the result of a task."""
        pass
    
    def search_similar(self, text, limit=5):
        """Search for similar texts."""
        pass
    
    def add_to_memory(self, text, metadata=None):
        """Add a text to memory."""
        pass
    
    def get_by_id(self, memory_id):
        """Get a memory item by ID."""
        pass
    
    def delete_by_id(self, memory_id):
        """Delete a memory item by ID."""
        pass
    
    def clear_memory(self):
        """Clear all memory."""
        pass
```

## 7. Infrastructure Layer

The Infrastructure Layer contains implementations of the adapters defined in the Adapter Layer.

### 7.1 CLI Implementation

```python
# [Spec §3.2.1] CLI Interface Layer
class CLIAdapter:
    """Implementation of the CLI port using Typer and Rich."""
    
    def __init__(self):
        self.console = None  # Rich console
    
    def display_message(self, message):
        """Display a message to the user."""
        self.console.print(message)
    
    def display_error(self, error):
        """Display an error message to the user."""
        self.console.print(f"[bold red]Error:[/bold red] {error}")
    
    def display_success(self, message):
        """Display a success message to the user."""
        self.console.print(f"[bold green]Success:[/bold green] {message}")
    
    def display_progress(self, progress, total, message):
        """Display a progress indicator."""
        with self.console.status(message) as status:
            for i in range(progress, total + 1):
                status.update(f"{message} ({i}/{total})")
                time.sleep(0.1)  # Simulated delay
    
    def display_intervention_prompt(self, intervention):
        """Display an intervention prompt to the user."""
        self.console.print(f"[bold yellow]Human intervention required:[/bold yellow]")
        self.console.print(intervention["prompt"])
        
        if intervention["options"]:
            self.console.print("Options:")
            for i, option in enumerate(intervention["options"]):
                self.console.print(f"{i+1}. {option}")
    
    def get_user_input(self, prompt, options=None):
        """Get input from the user."""
        if options:
            self.console.print(prompt)
            for i, option in enumerate(options):
                self.console.print(f"{i+1}. {option}")
            
            while True:
                choice = input("Enter your choice (number): ")
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(options):
                        return options[choice_idx]
                    else:
                        self.console.print("[red]Invalid choice. Please try again.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a number.[/red]")
        else:
            return input(prompt)
    
    def get_user_confirmation(self, prompt):
        """Get confirmation from the user."""
        response = input(f"{prompt} (y/n): ")
        return response.lower() in ["y", "yes"]
```

### 7.2 LLM Provider Implementations

#### 7.2.1 OpenAIAdapter

```python
# [Spec §3.2.7] LLM Backend Abstraction - OpenAI Adapter
class OpenAIAdapter:
    """Implementation of the LLM port using OpenAI API."""
    
    def __init__(self, api_key, default_model="gpt-4"):
        self.api_key = api_key
        self.default_model = default_model
        self.client = None  # OpenAI client
    
    def generate_text(self, prompt, model=None, temperature=0.7, max_tokens=None):
        """Generate text from a prompt using OpenAI API."""
        model = model or self.default_model
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def get_embedding(self, text, model=None):
        """Get an embedding for a text using OpenAI API."""
        model = model or "text-embedding-ada-002"
        
        response = self.client.embeddings.create(
            model=model,
            input=text
        )
        
        return response.data[0].embedding
    
    def count_tokens(self, text, model=None):
        """Count the number of tokens in a text."""
        # This is a simplified implementation
        # In practice, you would use a tokenizer specific to the model
        return len(text.split())
    
    def get_available_models(self):
        """Get a list of available models from OpenAI API."""
        response = self.client.models.list()
        return [model.id for model in response.data]
```

#### 7.2.2 LocalModelAdapter

```python
# [Spec §3.2.7] LLM Backend Abstraction - Local Model Adapter
class LocalModelAdapter:
    """Implementation of the LLM port using local models via LM Studio."""
    
    def __init__(self, host="localhost", port=8000, default_model="llama3"):
        self.host = host
        self.port = port
        self.default_model = default_model
        self.base_url = f"http://{host}:{port}"
    
    def generate_text(self, prompt, model=None, temperature=0.7, max_tokens=None):
        """Generate text from a prompt using a local model."""
        model = model or self.default_model
        
        payload = {
            "messages": [{"role": "system", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or 1024
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error generating text: {response.text}")
    
    def get_embedding(self, text, model=None):
        """Get an embedding for a text using a local model."""
        payload = {
            "input": text,
            "model": model or "all-MiniLM-L6-v2"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/embeddings",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        else:
            raise Exception(f"Error getting embedding: {response.text}")
    
    def count_tokens(self, text, model=None):
        """Count the number of tokens in a text."""
        # This is a simplified implementation
        # In practice, you would use a tokenizer specific to the model
        return len(text.split())
    
    def get_available_models(self):
        """Get a list of available local models."""
        response = requests.get(f"{self.base_url}/v1/models")
        
        if response.status_code == 200:
            return [model["id"] for model in response.json()["data"]]
        else:
            raise Exception(f"Error getting models: {response.text}")
```

### 7.3 File System Implementation

```python
# [Spec §4.1.1] Project Creation - File System Adapter
class FileSystemAdapter:
    """Implementation of the file system port using Python's os and shutil."""
    
    def read_file(self, path):
        """Read a file."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def write_file(self, path, content):
        """Write to a file."""
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return True
    
    def append_file(self, path, content):
        """Append to a file."""
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        
        return True
    
    def delete_file(self, path):
        """Delete a file."""
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def file_exists(self, path):
        """Check if a file exists."""
        return os.path.isfile(path)
    
    def create_directory(self, path):
        """Create a directory."""
        os.makedirs(path, exist_ok=True)
        return True
    
    def delete_directory(self, path):
        """Delete a directory."""
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
        return False
    
    def directory_exists(self, path):
        """Check if a directory exists."""
        return os.path.isdir(path)
    
    def list_files(self, path, pattern=None):
        """List files in a directory."""
        if not os.path.isdir(path):
            return []
        
        if pattern:
            return glob.glob(os.path.join(path, pattern))
        else:
            return [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    
    def list_directories(self, path):
        """List subdirectories in a directory."""
        if not os.path.isdir(path):
            return []
        
        return [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
```

### 7.4 Memory Implementation

#### 7.4.1 SQLiteMemoryAdapter

```python
# [Spec §3.2.6] Memory and Context System - SQLite Adapter
class SQLiteMemoryAdapter:
    """Implementation of the memory port using SQLite for structured data."""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None  # SQLite connection
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize the database."""
        self.conn = sqlite3.connect(self.db_path)
        
        # Create tables if they don't exist
        cursor = self.conn.cursor()
        
        # Create memory table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id TEXT PRIMARY KEY,
            text TEXT,
            metadata TEXT,
            created_at TEXT
        )
        ''')
        
        # Create task table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task (
            id TEXT PRIMARY KEY,
            agent_id TEXT,
            task_type TEXT,
            inputs TEXT,
            outputs TEXT,
            status TEXT,
            created_at TEXT,
            completed_at TEXT
        )
        ''')
        
        self.conn.commit()
    
    def get_context_for_task(self, task):
        """Get context for a task."""
        # Get recent tasks of the same type
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT inputs, outputs FROM task
        WHERE task_type = ? AND status = 'completed'
        ORDER BY created_at DESC
        LIMIT 5
        ''', (task.task_type,))
        
        rows = cursor.fetchall()
        
        context = {
            "recent_tasks": []
        }
        
        for inputs, outputs in rows:
            context["recent_tasks"].append({
                "inputs": json.loads(inputs),
                "outputs": json.loads(outputs)
            })
        
        return context
    
    def store_task_result(self, task, outputs):
        """Store the result of a task."""
        cursor = self.conn.cursor()
        
        # Convert dictionaries to JSON strings
        inputs_json = json.dumps(task.inputs)
        outputs_json = json.dumps(outputs)
        
        # Insert or update the task
        cursor.execute('''
        INSERT OR REPLACE INTO task
        (id, agent_id, task_type, inputs, outputs, status, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id,
            task.agent_id,
            task.task_type,
            inputs_json,
            outputs_json,
            task.status,
            task.created_at.isoformat(),
            task.completed_at.isoformat() if task.completed_at else None
        ))
        
        self.conn.commit()
        
        return True
    
    def add_to_memory(self, text, metadata=None):
        """Add a text to memory."""
        memory_id = generate_uuid()
        
        cursor = self.conn.cursor()
        
        # Convert metadata to JSON string
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Insert the memory
        cursor.execute('''
        INSERT INTO memory
        (id, text, metadata, created_at)
        VALUES (?, ?, ?, ?)
        ''', (
            memory_id,
            text,
            metadata_json,
            current_time().isoformat()
        ))
        
        self.conn.commit()
        
        return memory_id
    
    def get_by_id(self, memory_id):
        """Get a memory item by ID."""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, text, metadata, created_at FROM memory
        WHERE id = ?
        ''', (memory_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        id, text, metadata_json, created_at = row
        
        return {
            "id": id,
            "text": text,
            "metadata": json.loads(metadata_json) if metadata_json else None,
            "created_at": created_at
        }
    
    def delete_by_id(self, memory_id):
        """Delete a memory item by ID."""
        cursor = self.conn.cursor()
        cursor.execute('''
        DELETE FROM memory
        WHERE id = ?
        ''', (memory_id,))
        
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def clear_memory(self):
        """Clear all memory."""
        cursor = self.conn.cursor()
        cursor.execute('''
        DELETE FROM memory
        ''')
        
        self.conn.commit()
        
        return True
    
    def search_similar(self, text, limit=5):
        """Search for similar texts."""
        # This is a simplified implementation
        # In practice, you would use a vector database for semantic search
        
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, text, metadata, created_at FROM memory
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        results = []
        for id, text, metadata_json, created_at in rows:
            results.append({
                "id": id,
                "text": text,
                "metadata": json.loads(metadata_json) if metadata_json else None,
                "created_at": created_at
            })
        
        return results
```

#### 7.4.2 ChromaDBAdapter

```python
# [Spec §3.2.6] Memory and Context System - ChromaDB Adapter
class ChromaDBAdapter:
    """Implementation of the memory port using ChromaDB for vector storage."""
    
    def __init__(self, db_path, llm_port):
        self.db_path = db_path
        self.llm_port = llm_port
        self.client = None  # ChromaDB client
        self.collection = None  # ChromaDB collection
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize the database."""
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name="memory",
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_context_for_task(self, task):
        """Get context for a task."""
        # Convert task inputs to a query string
        query = f"Task type: {task.task_type}\nInputs: {json.dumps(task.inputs)}"
        
        # Get embedding for the query
        embedding = self.llm_port.get_embedding(query)
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=5
        )
        
        context = {
            "similar_tasks": []
        }
        
        for i in range(len(results["ids"][0])):
            context["similar_tasks"].append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            })
        
        return context
    
    def store_task_result(self, task, outputs):
        """Store the result of a task."""
        # Convert task to a document
        document = f"Task type: {task.task_type}\nInputs: {json.dumps(task.inputs)}\nOutputs: {json.dumps(outputs)}"
        
        # Get embedding for the document
        embedding = self.llm_port.get_embedding(document)
        
        # Add to the collection
        self.collection.add(
            ids=[task.id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[{
                "task_type": task.task_type,
                "agent_id": task.agent_id,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }]
        )
        
        return True
    
    def add_to_memory(self, text, metadata=None):
        """Add a text to memory."""
        memory_id = generate_uuid()
        
        # Get embedding for the text
        embedding = self.llm_port.get_embedding(text)
        
        # Add to the collection
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}]
        )
        
        return memory_id
    
    def get_by_id(self, memory_id):
        """Get a memory item by ID."""
        try:
            result = self.collection.get(ids=[memory_id])
            
            if not result["ids"]:
                return None
            
            return {
                "id": result["ids"][0],
                "text": result["documents"][0],
                "metadata": result["metadatas"][0],
                "embedding": result["embeddings"][0]
            }
        except:
            return None
    
    def delete_by_id(self, memory_id):
        """Delete a memory item by ID."""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except:
            return False
    
    def clear_memory(self):
        """Clear all memory."""
        self.collection.delete(ids=self.collection.get()["ids"])
        return True
    
    def search_similar(self, text, limit=5):
        """Search for similar texts."""
        # Get embedding for the text
        embedding = self.llm_port.get_embedding(text)
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit
        )
        
        similar_items = []
        for i in range(len(results["ids"][0])):
            similar_items.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        
        return similar_items
```

## 8. Cross-Cutting Concerns

### 8.1 Logging

```python
# [Spec §5.3] Reliability
class Logger:
    """Handles logging throughout the system."""
    
    def __init__(self, log_level="INFO", log_file=None):
        self.log_level = log_level
        self.log_file = log_file
        self.logger = None  # Python logger
        self.initialize_logger()
    
    def initialize_logger(self):
        """Initialize the logger."""
        self.logger = logging.getLogger("devsynth")
        self.logger.setLevel(getattr(logging, self.log_level))
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler if log_file is specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def info(self, message):
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message):
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message):
        """Log a critical message."""
        self.logger.critical(message)
    
    def log_event(self, event):
        """Log a domain event."""
        self.info(f"Event: {event.event_type} - {json.dumps(event.payload)}")
    
    def log_task(self, task):
        """Log a task."""
        self.info(f"Task: {task.id} - Type: {task.task_type} - Status: {task.status}")
```

### 8.2 Error Handling

```python
# [Spec §5.1] Usability - Error Handling
class ErrorHandler:
    """Handles errors throughout the system."""
    
    def __init__(self, logger):
        self.logger = logger
        self.error_handlers = {}  # Dictionary of error handlers by error type
    
    def register_handler(self, error_type, handler):
        """Register a handler for a specific error type."""
        self.error_handlers[error_type] = handler
        return True
    
    def handle_error(self, error, context=None):
        """Handle an error."""
        error_type = type(error)
        
        # Log the error
        self.logger.error(f"Error: {str(error)} - Type: {error_type.__name__} - Context: {context}")
        
        # Get the handler for this error type
        handler = self.error_handlers.get(error_type)
        if handler:
            return handler(error, context)
        
        # Check for parent error types
        for error_cls, handler in self.error_handlers.items():
            if isinstance(error, error_cls):
                return handler(error, context)
        
        # No specific handler, use default
        return self.default_handler(error, context)
    
    def default_handler(self, error, context=None):
        """Default error handler."""
        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "suggestion": "Please try again or contact support."
        }
    
    def format_error_message(self, error_result):
        """Format an error result into a user-friendly message."""
        message = f"Error: {error_result['error']}"
        
        if error_result.get("suggestion"):
            message += f"\n\nSuggestion: {error_result['suggestion']}"
        
        return message
```

### 8.3 Configuration

```python
# [Spec §4.1.2] Project Configuration
class ConfigManager:
    """Manages configuration throughout the system."""
    
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        if not self.config_path or not os.path.exists(self.config_path):
            # Use default configuration
            self.config = self.get_default_config()
            return
        
        with open(self.config_path, "r") as f:
            self.config = toml.load(f)
    
    def save_config(self):
        """Save configuration to file."""
        if not self.config_path:
            return False
        
        with open(self.config_path, "w") as f:
            toml.dump(self.config, f)
        
        return True
    
    def get(self, key, default=None):
        """Get a configuration value."""
        # Support nested keys with dot notation
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """Set a configuration value."""
        # Support nested keys with dot notation
        keys = key.split(".")
        config = self.config
        
        # Navigate to the innermost dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the configuration
        self.save_config()
        
        return True
    
    def get_default_config(self):
        """Get the default configuration."""
        return {
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7
            },
            "memory": {
                "vector_store": "chroma",
                "db_path": ".devsynth/memory"
            },
            "agents": {
                "enabled": True,
                "dialectical": True
            },
            "core_values": {
                "transparency": True,
                "human_control": True,
                "quality": True
            }
        }
    
    def get_values_config(self):
        """Get the core values configuration."""
        return self.get("core_values", {})
    
    def save_values_config(self, values_config):
        """Save the core values configuration."""
        self.config["core_values"] = values_config
        return self.save_config()
    
    def get_promises_config(self):
        """Get the promises configuration."""
        return self.get("promises", {"promises": [], "agent_promises": []})
    
    def save_promises_config(self, promises_config):
        """Save the promises configuration."""
        self.config["promises"] = promises_config
        return self.save_config()
```

## 9. Workflow Examples

### 9.1 Project Initialization

```python
# [Spec §4.1.1] Project Creation - Workflow Example
def initialize_project_workflow(name, template, path, description):
    """Example workflow for initializing a project."""
    # Create dependencies
    config_manager = ConfigManager()
    file_system_adapter = FileSystemAdapter()
    event_bus = EventBus()
    template_service = TemplateService()
    project_repository = ProjectRepository()
    
    # Create the project service
    project_service = ProjectService(project_repository, template_service)
    
    # Create the use case
    init_project_use_case = InitProjectUseCase(project_service, file_system_adapter, event_bus)
    
    # Execute the use case
    project, message = init_project_use_case.execute(name, template, path, description)
    
    if not project:
        print(f"Error: {message}")
        return None
    
    print(f"Project initialized successfully: {project.name}")
    print(f"Path: {project.path}")
    
    return project
```

### 9.2 Specification Generation

```python
# [Spec §4.2.2] Specification Generation - Workflow Example
def generate_specification_workflow(project_id, output_path):
    """Example workflow for generating a specification."""
    # Create dependencies
    config_manager = ConfigManager()
    file_system_adapter = FileSystemAdapter()
    event_bus = EventBus()
    requirement_repository = RequirementRepository()
    project_repository = ProjectRepository()
    llm_adapter = OpenAIAdapter(config_manager.get("llm.api_key"), config_manager.get("llm.model"))
    
    # Create the requirement service
    requirement_service = RequirementService(requirement_repository, project_repository)
    
    # Create the agent system
    memory_adapter = ChromaDBAdapter(config_manager.get("memory.db_path"), llm_adapter)
    promise_system = PromiseSystem(config_manager, event_bus)
    core_values_system = CoreValuesSystem(config_manager)
    agent_system = AgentSystem(llm_adapter, memory_adapter, promise_system, core_values_system, event_bus)
    
    # Register agents
    spec_agent = Agent(generate_uuid(), "SpecificationAgent", "specification_generation")
    spec_agent.add_capability("refine_specification")
    spec_agent.set_system_prompt("You are a specification generation agent. Your task is to refine specifications based on requirements.")
    agent_system.register_agent(spec_agent)
    
    # Create the use case
    generate_spec_use_case = GenerateSpecificationUseCase(requirement_service, file_system_adapter, agent_system, event_bus)
    
    # Execute the use case
    specification, message = generate_spec_use_case.execute(project_id, output_path)
    
    if not specification:
        print(f"Error: {message}")
        return None
    
    print(f"Specification generated successfully")
    if output_path:
        print(f"Output path: {output_path}")
    
    return specification
```

### 9.3 Test Generation

```python
# [Spec §4.3] Test-Driven Development - Workflow Example
def generate_tests_workflow(specification, output_path, test_type="both"):
    """Example workflow for generating tests."""
    # Create dependencies
    config_manager = ConfigManager()
    file_system_adapter = FileSystemAdapter()
    event_bus = EventBus()
    test_repository = TestRepository()
    requirement_repository = RequirementRepository()
    project_repository = ProjectRepository()
    llm_adapter = OpenAIAdapter(config_manager.get("llm.api_key"), config_manager.get("llm.model"))
    
    # Create the test service
    test_service = TestService(test_repository, requirement_repository, project_repository)
    
    # Create the agent system
    memory_adapter = ChromaDBAdapter(config_manager.get("memory.db_path"), llm_adapter)
    promise_system = PromiseSystem(config_manager, event_bus)
    core_values_system = CoreValuesSystem(config_manager)
    agent_system = AgentSystem(llm_adapter, memory_adapter, promise_system, core_values_system, event_bus)
    
    # Register agents
    test_agent = Agent(generate_uuid(), "TestAgent", "test_generation")
    test_agent.add_capability("generate_tests")
    test_agent.set_system_prompt("You are a test generation agent. Your task is to generate tests based on specifications.")
    agent_system.register_agent(test_agent)
    
    # Create the use case
    generate_tests_use_case = GenerateTestsUseCase(test_service, file_system_adapter, agent_system, event_bus)
    
    # Execute the use case
    tests, message = generate_tests_use_case.execute(specification, output_path, test_type)
    
    if not tests:
        print(f"Error: {message}")
        return None
    
    print(f"Tests generated successfully: {len(tests)} tests")
    if output_path:
        print(f"Output path: {output_path}")
    
    return tests
```

### 9.4 Code Generation

```python
# [Spec §4.4] Code Generation and Implementation - Workflow Example
def generate_code_workflow(test_ids, output_path):
    """Example workflow for generating code."""
    # Create dependencies
    config_manager = ConfigManager()
    file_system_adapter = FileSystemAdapter()
    event_bus = EventBus()
    test_repository = TestRepository()
    llm_adapter = OpenAIAdapter(config_manager.get("llm.api_key"), config_manager.get("llm.model"))
    
    # Create the code service
    code_service = CodeService(test_repository, file_system_adapter)
    
    # Create the agent system
    memory_adapter = ChromaDBAdapter(config_manager.get("memory.db_path"), llm_adapter)
    promise_system = PromiseSystem(config_manager, event_bus)
    core_values_system = CoreValuesSystem(config_manager)
    agent_system = AgentSystem(llm_adapter, memory_adapter, promise_system, core_values_system, event_bus)
    
    # Register agents
    code_agent = Agent(generate_uuid(), "CodeAgent", "code_generation")
    code_agent.add_capability("generate_code")
    code_agent.set_system_prompt("You are a code generation agent. Your task is to generate code based on tests.")
    agent_system.register_agent(code_agent)
    
    # Create the use case
    generate_code_use_case = GenerateCodeUseCase(code_service, test_repository, file_system_adapter, agent_system, event_bus)
    
    # Execute the use case
    code, message = generate_code_use_case.execute(test_ids, output_path)
    
    if not code:
        print(f"Error: {message}")
        return None
    
    print(f"Code generated successfully: {len(code)} files")
    print(f"Output path: {output_path}")
    
    return code
```

## 10. References

- [Spec §3.1] High-Level Architecture
- [Spec §3.2] Component Descriptions
- [Spec §3.3] Interaction Diagrams
- [Spec §3.4] Data Flow
- [Spec §4.1] Project Initialization and Management
- [Spec §4.2] Requirement Analysis and Specification
- [Spec §4.3] Test-Driven Development
- [Spec §4.4] Code Generation and Implementation
- [Spec §4.5] Documentation Generation
- [Spec §4.6] Validation and Verification
- [Spec §4.7] Continuous Learning
- [Spec §5.1] Usability
- [Spec §5.2] Performance
- [Spec §5.3] Reliability
- [Spec §5.4] Security
- [Spec §5.5] Maintainability
- [Spec §5.6] Portability
- [Spec §8.1] Project Model
- [Spec §8.2] Requirement Model
- [Spec §8.3] Test Model
- [Spec §8.4] Agent Model
- [Spec §8.5] Workflow Model
- [Diagram: System Architecture Diagram]
- [Diagram: Component Interaction Diagram]
- [Diagram: Data Flow Diagram]
- [Diagram: Process Flow Diagram]
- [Diagram: State Diagram]
- [Diagram: Sequence Diagrams]
- [Diagram: Class/Entity Diagram]
