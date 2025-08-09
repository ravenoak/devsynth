Feature: MVU Command Execution
  As a developer
  I want to use MVU-related CLI commands
  So that I can manage MVU metadata

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Initialize MVU configuration
    When I run the command "devsynth mvu init"
    Then the command should succeed
    And the file ".devsynth/mvu.yml" should exist

  Scenario: Rewrite commit history
    Given MVU rewrite completes successfully
    When I run the command "devsynth mvu rewrite --dry-run"
    Then the command should succeed
    And the output should contain "Dry run complete"
