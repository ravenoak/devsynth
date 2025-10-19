Feature: Self Analysis
  As a developer using DevSynth
  I want to analyze the DevSynth codebase itself
  So that I can understand its architecture, code quality, and identify improvement opportunities

  Background:
    Given the DevSynth system is initialized
    And the self analyzer is configured

  Scenario: Analyze codebase architecture
    When I analyze the DevSynth codebase architecture
    Then the analyzer should detect the architecture pattern used
    And the analyzer should identify architectural layers
    And the analyzer should analyze dependencies between layers
    And the analyzer should provide insights about the architecture

  Scenario: Detect architecture type
    When I analyze the DevSynth codebase architecture
    Then the analyzer should detect hexagonal architecture with high confidence
    And the analyzer should identify domain, application, and adapters layers
    And the analyzer should identify ports and adapters
    And the analyzer should provide a confidence score for the detected architecture

  Scenario: Identify layers in codebase
    When I analyze the DevSynth codebase architecture
    Then the analyzer should identify the following layers:
      | Layer       | Path Pattern                |
      | domain      | src/devsynth/domain/        |
      | application | src/devsynth/application/   |
      | adapters    | src/devsynth/adapters/      |
      | ports       | src/devsynth/ports/         |
    And the analyzer should categorize files into the appropriate layers

  Scenario: Analyze layer dependencies
    When I analyze the DevSynth codebase architecture
    Then the analyzer should identify dependencies between layers
    And the analyzer should verify that domain layer does not depend on other layers
    And the analyzer should verify that application layer depends only on domain layer
    And the analyzer should verify that adapters layer depends on application and domain layers
    And the analyzer should provide a dependency graph of the layers

  Scenario: Check architecture violations
    When I analyze the DevSynth codebase for architecture violations
    Then the analyzer should identify any violations of hexagonal architecture principles
    And the analyzer should provide details about each violation
    And the analyzer should suggest ways to fix the violations

  Scenario: Analyze code quality
    When I analyze the DevSynth code quality
    Then the analyzer should calculate complexity metrics
    And the analyzer should calculate readability metrics
    And the analyzer should calculate maintainability metrics
    And the analyzer should provide insights about code quality

  Scenario: Analyze complexity metrics
    When I analyze the DevSynth code quality
    Then the analyzer should calculate cyclomatic complexity for each function
    And the analyzer should calculate cognitive complexity for each function
    And the analyzer should identify functions with high complexity
    And the analyzer should provide an overall complexity score

  Scenario: Analyze readability metrics
    When I analyze the DevSynth code quality
    Then the analyzer should calculate docstring coverage
    And the analyzer should calculate comment-to-code ratio
    And the analyzer should analyze identifier naming conventions
    And the analyzer should provide an overall readability score

  Scenario: Analyze maintainability metrics
    When I analyze the DevSynth code quality
    Then the analyzer should calculate code duplication
    And the analyzer should calculate function length distribution
    And the analyzer should calculate class cohesion
    And the analyzer should provide an overall maintainability score

  Scenario: Analyze test coverage
    When I analyze the DevSynth test coverage
    Then the analyzer should calculate unit test coverage
    And the analyzer should calculate integration test coverage
    And the analyzer should calculate behavior test coverage
    And the analyzer should identify untested components
    And the analyzer should provide an overall test coverage score

  Scenario: Identify improvement opportunities
    When I analyze the DevSynth codebase for improvement opportunities
    Then the analyzer should identify areas with low test coverage
    And the analyzer should identify areas with high complexity
    And the analyzer should identify areas with low readability
    And the analyzer should identify areas with low maintainability
    And the analyzer should prioritize improvement opportunities
    And the analyzer should provide specific recommendations for each opportunity

  Scenario: Generate comprehensive insights
    When I request comprehensive insights about the DevSynth codebase
    Then the analyzer should generate a comprehensive report
    And the report should include architecture insights
    And the report should include code quality insights
    And the report should include test coverage insights
    And the report should include improvement opportunities
    And the report should include metrics summary

  Scenario: Integrate with EDRR workflow
    Given the EDRR workflow is configured
    When I initiate a self-analysis task
    Then the system should use self analysis in the Analysis phase
    And the system should use architecture analysis in the Design phase
    And the system should use code quality analysis in the Refinement phase
    And the system should use test coverage analysis in the Verification phase
    And the memory system should store self analysis results with appropriate EDRR phase tags

  Scenario: Integrate with WSDE team
    Given the WSDE team is configured
    When I assign a self-analysis task to the WSDE team
    Then the team should collaborate to analyze different aspects of the codebase
    And the team should share analysis results between agents
    And the team should produce a consolidated self-analysis report
