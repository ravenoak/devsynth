Feature: Doctor Command
  As a developer
  I want to validate environment configuration
  So that I can fix issues before running other commands

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Warn about invalid environment configuration
    Given a project with invalid environment configuration
    When I run the command "devsynth doctor"
    Then the system should display a warning message
    And the output should indicate configuration errors

  Scenario: Validate existing environment configuration
    Given valid environment configuration
    When I run the command "devsynth doctor"
    Then the system should display a success message
