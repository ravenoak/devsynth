Feature: Requirements Wizard
  As a developer
  I want to collect basic requirements interactively
  So that they can be saved or cancelled

  Scenario: Save requirements
    Given the DevSynth CLI is installed
    When I run the requirements wizard
    Then a saved requirements file "requirements_wizard.json" should exist

  Scenario: Cancel the requirements wizard
    Given the DevSynth CLI is installed
    When I cancel the requirements wizard
    Then no requirements file should exist
