Feature: Invalid configuration handling
  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Config command with invalid key
    When I run the command "devsynth config --key bad --value test"
    Then the command should fail
    And the output should contain "invalid"
