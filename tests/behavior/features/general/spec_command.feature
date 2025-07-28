Feature: Spec Command
  As a developer
  I want to generate specifications from requirements
  So that I can produce design documents automatically

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Generate specifications from a requirements file
    When I run the command "devsynth spec --requirements-file requirements.md"
    Then the spec command should process "requirements.md"
    And generate specifications based on the requirements
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Handle missing requirements file
    Given the requirements file "missing.md" does not exist
    When I run the command "devsynth spec --requirements-file missing.md"
    Then the system should display an error message
    And the workflow should execute successfully
