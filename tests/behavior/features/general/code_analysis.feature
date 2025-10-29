# Specification: docs/specifications/code-analysis.md
Feature: Code Analysis
  As a developer
  I want to analyze my codebase structure and quality
  So that I can understand the project architecture and identify improvement opportunities

  Background:
    Given a DevSynth project is initialized
    And the codebase contains Python files
    And the inspect-code command is available

  @fast
  Scenario: Analyze project structure and metrics
    When I run the inspect-code command
    Then I should see project structure analysis
    And I should see code quality metrics
    And I should see language detection results
    And I should see size and complexity metrics

  @fast
  Scenario: Analyze specific directory path
    Given a specific directory path is provided
    When I run the inspect-code command with a path
    Then I should see analysis results for the specified directory
    And I should see file organization details
    And I should see module dependency information

  @fast
  Scenario: Detect programming languages
    Given the codebase contains multiple file types
    When I run the inspect-code command
    Then primary programming languages should be identified
    And file distribution by language should be shown
    And language-specific metrics should be provided

  @fast
  Scenario: Perform AST-based code analysis
    Given the codebase follows common design patterns
    When I run the inspect-code command
    Then AST analysis results should be provided
    And import relationship mapping should be available
    And function and class analysis should be included
    And complexity assessments should be performed

  @fast
  Scenario: Identify architectural patterns
    When I run the inspect-code command
    Then design pattern detection should be performed
    And layer separation analysis should be provided
    And component coupling metrics should be calculated
    And entry point identification should be completed
