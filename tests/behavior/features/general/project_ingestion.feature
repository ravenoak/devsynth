Feature: Project Ingestion
  As a developer using DevSynth
  I want to ingest a project into DevSynth
  So that the system can understand and work with my project structure

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @project-ingestion
  Scenario: Ingest a project with default parameters
    When I run the command "devsynth ingest"
    Then the system should ingest the project
    And the system should create a project model
    And the output should indicate that the project was ingested
    And the workflow should execute successfully

  @project-ingestion
  Scenario: Ingest a project with custom manifest path
    When I run the command "devsynth ingest --manifest ./custom-path/project.yaml"
    Then the system should ingest the project using "./custom-path/project.yaml"
    And the system should create a project model
    And the output should indicate that the project was ingested
    And the workflow should execute successfully

  @project-ingestion
  Scenario: Perform a dry run of project ingestion
    When I run the command "devsynth ingest --dry-run"
    Then the system should simulate project ingestion
    And the system should not make any changes
    And the output should indicate that a dry run was performed
    And the workflow should execute successfully

  @project-ingestion
  Scenario: Ingest a project with verbose output
    When I run the command "devsynth ingest --verbose"
    Then the system should ingest the project
    And the system should create a project model
    And the output should include detailed ingestion information
    And the workflow should execute successfully

  @project-ingestion
  Scenario: Validate project configuration without ingestion
    When I run the command "devsynth ingest --validate-only"
    Then the system should validate the project configuration
    And the system should not perform ingestion
    And the output should indicate that validation was performed
    And the workflow should execute successfully

  @project-ingestion
  Scenario: Ingest a project with all custom parameters
    When I run the command "devsynth ingest --manifest ./custom-path/project.yaml --verbose --dry-run"
    Then the system should simulate project ingestion using "./custom-path/project.yaml"
    And the system should not make any changes
    And the output should include detailed ingestion information
    And the workflow should execute successfully

  @project-ingestion
  Scenario: Handle missing manifest file
    When I run the command "devsynth ingest --manifest ./non-existent-manifest.yaml"
    Then the system should display an error message
    And the error message should indicate that the manifest file was not found
    And the workflow should not execute successfully

  @project-ingestion
  Scenario: Handle invalid manifest file
    Given a project with an invalid manifest file
    When I run the command "devsynth ingest"
    Then the system should display an error message
    And the error message should indicate that the manifest file is invalid
    And the workflow should not execute successfully
