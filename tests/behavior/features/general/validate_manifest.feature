Feature: Validate Manifest
  As a developer using DevSynth
  I want to validate my project configuration file
  So that I can ensure it conforms to the schema and project structure

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @manifest-validation
  Scenario: Validate config with default paths
    When I run the command "devsynth validate-manifest"
    Then the system should validate the project configuration
    And the output should indicate that the configuration is valid
    And the workflow should execute successfully

  @manifest-validation
  Scenario: Validate config with custom configuration path
    When I run the command "devsynth validate-manifest --config ./custom-path/project.yaml"
    Then the system should validate the project configuration at "./custom-path/project.yaml"
    And the output should indicate that the configuration is valid
    And the workflow should execute successfully

  @manifest-validation
  Scenario: Validate config with custom schema path
    When I run the command "devsynth validate-manifest --schema ./custom-schema.json"
    Then the system should validate the project configuration against "./custom-schema.json"
    And the output should indicate that the configuration is valid
    And the workflow should execute successfully

  @manifest-validation
  Scenario: Handle invalid configuration
    Given a project with an invalid configuration file
    When I run the command "devsynth validate-manifest"
    Then the system should display an error message
    And the error message should indicate the validation errors
    And the workflow should not execute successfully

  @manifest-validation
  Scenario: Handle missing configuration file
    Given a project without a configuration file
    When I run the command "devsynth validate-manifest"
    Then the system should display an error message
    And the error message should indicate that no configuration file was found
    And the workflow should not execute successfully

  @manifest-validation
  Scenario: Handle missing schema
    Given a project with a missing schema file
    When I run the command "devsynth validate-manifest --schema ./missing-schema.json"
    Then the system should display an error message
    And the error message should indicate that the schema file was not found
    And the workflow should not execute successfully
