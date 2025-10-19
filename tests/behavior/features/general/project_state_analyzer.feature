Feature: Project State Analysis
  As a developer using DevSynth
  I want to analyze the state of my project
  So that I can understand its architecture, components, and alignment with requirements

  Background:
    Given the DevSynth system is initialized
    And the project state analyzer is configured

  Scenario: Analyze project structure
    When I analyze the project structure
    Then the analyzer should identify all files in the project
    And the analyzer should categorize files by type
    And the analyzer should detect the programming languages used
    And the analyzer should provide metrics about the project structure

  Scenario: Infer project architecture
    When I analyze the project architecture
    Then the analyzer should detect the architecture pattern used
    And the analyzer should identify components based on the architecture
    And the analyzer should provide confidence scores for detected architectures
    And the analyzer should identify architectural layers

  Scenario: Analyze MVC architecture
    Given a project with Model-View-Controller architecture
    When I analyze the project architecture
    Then the analyzer should detect MVC architecture with high confidence
    And the analyzer should identify models, views, and controllers
    And the analyzer should analyze dependencies between MVC components

  Scenario: Analyze hexagonal architecture
    Given a project with hexagonal architecture
    When I analyze the project architecture
    Then the analyzer should detect hexagonal architecture with high confidence
    And the analyzer should identify domain, application, and adapters layers
    And the analyzer should analyze dependencies between layers
    And the analyzer should identify ports and adapters

  Scenario: Analyze layered architecture
    Given a project with layered architecture
    When I analyze the project architecture
    Then the analyzer should detect layered architecture with high confidence
    And the analyzer should identify the different layers
    And the analyzer should analyze dependencies between layers

  Scenario: Analyze microservices architecture
    Given a project with microservices architecture
    When I analyze the project architecture
    Then the analyzer should detect microservices architecture with high confidence
    And the analyzer should identify individual microservices
    And the analyzer should analyze communication patterns between microservices

  Scenario: Analyze event-driven architecture
    Given a project with event-driven architecture
    When I analyze the project architecture
    Then the analyzer should detect event-driven architecture with high confidence
    And the analyzer should identify event producers and consumers
    And the analyzer should analyze event flow patterns

  Scenario: Analyze requirements-specification alignment
    Given a project with requirements and specifications
    When I analyze the alignment between requirements and specifications
    Then the analyzer should extract requirements from documentation
    And the analyzer should extract specifications from documentation
    And the analyzer should match requirements to specifications
    And the analyzer should identify unmatched requirements
    And the analyzer should identify orphaned specifications

  Scenario: Analyze specification-code alignment
    Given a project with specifications and code
    When I analyze the alignment between specifications and code
    Then the analyzer should extract specifications from documentation
    And the analyzer should analyze code to determine implementation status
    And the analyzer should match specifications to code implementations
    And the analyzer should identify unimplemented specifications

  Scenario: Generate project health report
    When I request a project health report
    Then the analyzer should generate a comprehensive health report
    And the report should include requirements coverage metrics
    And the report should include specifications implementation metrics
    And the report should include overall health score
    And the report should identify issues in the project
    And the report should provide recommendations for improvement

  Scenario: Identify architecture violations
    Given a project with architectural constraints
    When I analyze the project for architecture violations
    Then the analyzer should identify violations of architectural constraints
    And the analyzer should provide details about each violation
    And the analyzer should suggest ways to fix the violations

  Scenario: Integrate with EDRR workflow
    Given the EDRR workflow is configured
    When I initiate a project analysis task
    Then the system should use project state analysis in the Analysis phase
    And the system should use architecture analysis in the Design phase
    And the system should use alignment analysis in the Verification phase
    And the memory system should store project analysis results with appropriate EDRR phase tags

  Scenario: Integrate with WSDE team
    Given the WSDE team is configured
    When I assign a project analysis task to the WSDE team
    Then the team should collaborate to analyze different aspects of the project
    And the team should share analysis results between agents
    And the team should produce a consolidated project analysis report
