Feature: Validate Manifest Command
  As a developer
  I want to validate my project manifest
  So that I can ensure it is well formed

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Validate manifest successfully
    When I run the command "devsynth validate-manifest"
    Then the output should indicate the project configuration is valid
    And the workflow should execute successfully

  Scenario: Handle missing manifest file
    Given no manifest file exists at the provided path
    When I run the command "devsynth validate-manifest --config missing.yaml"
    Then the system should display an error message
