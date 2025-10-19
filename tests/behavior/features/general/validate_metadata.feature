Feature: Validate Metadata
  As a developer using DevSynth
  I want to validate metadata in Markdown files
  So that I can ensure consistency and correctness in documentation

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @metadata-validation
  Scenario: Validate metadata in default directory
    When I run the command "devsynth validate-metadata"
    Then the system should validate metadata in the "docs/" directory
    And the output should indicate the validation results
    And the workflow should execute successfully

  @metadata-validation
  Scenario: Validate metadata in custom directory
    When I run the command "devsynth validate-metadata --directory ./custom-docs"
    Then the system should validate metadata in the "./custom-docs" directory
    And the output should indicate the validation results
    And the workflow should execute successfully

  @metadata-validation
  Scenario: Validate metadata in single file
    When I run the command "devsynth validate-metadata --file ./docs/specific-file.md"
    Then the system should validate metadata in the "./docs/specific-file.md" file
    And the output should indicate the validation results
    And the workflow should execute successfully

  @metadata-validation
  Scenario: Validate metadata with verbose output
    When I run the command "devsynth validate-metadata --verbose"
    Then the system should validate metadata in the "docs/" directory
    And the output should include detailed validation results
    And the workflow should execute successfully

  @metadata-validation
  Scenario: Handle directory with no Markdown files
    Given a directory with no Markdown files
    When I run the command "devsynth validate-metadata --directory ./empty-dir"
    Then the system should display a warning message
    And the warning message should indicate that no Markdown files were found
    And the workflow should execute successfully

  @metadata-validation
  Scenario: Handle invalid metadata in Markdown files
    Given a directory with Markdown files containing invalid metadata
    When I run the command "devsynth validate-metadata"
    Then the system should display validation errors
    And the output should indicate which files have invalid metadata
    And the workflow should execute successfully
