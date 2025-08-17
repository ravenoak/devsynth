# Reference: docs/user_guides/api_reference_generation.md
Feature: API Reference Documentation Generation
  As a developer using DevSynth
  I want to generate API reference documentation
  So that I can provide comprehensive documentation for my project

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @docs-generation
  Scenario: Generate API reference documentation with default parameters
    When I run the command "devsynth generate-docs"
    Then the system should generate API reference documentation
    And the documentation should be created in the "docs/api_reference" directory
    And the output should indicate that the documentation was generated
    And the workflow should execute successfully

  @docs-generation
  Scenario: Generate API reference documentation for a specific project path
    When I run the command "devsynth generate-docs --path ./my-project"
    Then the system should generate API reference documentation for "./my-project"
    And the documentation should be created in the "docs/api_reference" directory
    And the output should indicate that the documentation was generated
    And the workflow should execute successfully

  @docs-generation
  Scenario: Generate API reference documentation with custom output directory
    When I run the command "devsynth generate-docs --output-dir ./custom-docs"
    Then the system should generate API reference documentation
    And the documentation should be created in the "./custom-docs" directory
    And the output should indicate that the documentation was generated
    And the workflow should execute successfully

  @docs-generation
  Scenario: Generate API reference documentation with all custom parameters
    When I run the command "devsynth generate-docs --path ./my-project --output-dir ./custom-docs"
    Then the system should generate API reference documentation for "./my-project"
    And the documentation should be created in the "./custom-docs" directory
    And the output should indicate that the documentation was generated
    And the workflow should execute successfully

  @docs-generation
  Scenario: Handle project with no code
    Given a project with no source code
    When I run the command "devsynth generate-docs"
    Then the system should display a warning message
    And the warning message should indicate that no source code was found
    And the workflow should execute successfully

  @docs-generation
  Scenario: Handle invalid project path
    When I run the command "devsynth generate-docs --path ./non-existent-project"
    Then the system should display an error message
    And the error message should indicate that the project path does not exist
    And the workflow should not execute successfully
