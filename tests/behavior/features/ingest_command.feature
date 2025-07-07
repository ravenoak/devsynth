Feature: Ingest Command
  As a developer
  I want to ingest a project using the CLI
  So that I can analyze and work with the project in DevSynth

  Background:
    Given I have a valid project manifest file "manifest.yaml"
    And the DevSynth CLI is installed

  Scenario: Successfully ingest a project with a valid manifest
    When I run the command "devsynth ingest manifest.yaml"
    Then the command should execute successfully
    And the system should display a success message
    And the project should be ingested into the system

  Scenario: Attempt to ingest a project with an invalid manifest
    Given I have an invalid project manifest file "invalid_manifest.yaml"
    When I run the command "devsynth ingest invalid_manifest.yaml"
    Then the command should fail
    And the system should display an error message explaining the issue

  Scenario: Ingest a project with additional options
    When I run the command "devsynth ingest manifest.yaml --verbose"
    Then the command should execute successfully
    And the system should display detailed progress information
    And the project should be ingested into the system

  Scenario: Ingest a project with a non-existent manifest file
    When I run the command "devsynth ingest non_existent_manifest.yaml"
    Then the command should fail
    And the system should display an error message indicating the file does not exist