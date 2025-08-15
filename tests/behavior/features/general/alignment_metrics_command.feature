Feature: Alignment Metrics Command
  As a developer
  I want to collect alignment metrics
  So that I can measure coverage between requirements, specifications, tests and code

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @medium
  Scenario: Collect metrics successfully
    When I run the command "devsynth alignment-metrics"
    Then the system should display alignment metrics
    And the workflow should execute successfully

  @medium
  Scenario: Handle failure during metrics collection
    Given alignment metrics calculation fails
    When I run the command "devsynth alignment-metrics"
    Then the system should display an error message
