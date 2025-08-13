Feature: Run tests from the CLI
  As a developer
  I want to invoke DevSynth's test runner
  So that I can ensure the command behaves correctly

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Running fast tests when none match exits successfully
    When I run the command "devsynth run-tests --speed=fast"
    Then the command should exit successfully
