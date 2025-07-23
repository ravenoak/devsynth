Feature: Code Command
  As a developer
  I want to generate implementation code from tests
  So that I can quickly produce working software

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Generate code from tests
    When I run the command "devsynth code"
    Then the code command should be executed
    And the workflow should execute successfully
    And the system should display a success message
