Feature: Requirements Wizard
  As a developer gathering requirement details
  I want the wizard to persist and audit my answers
  So that project configuration reflects the latest decisions

  Scenario: Save requirements from the CLI wizard
    Given the DevSynth CLI is installed
    When I run the requirements wizard
    Then a saved requirements file "requirements_wizard.json" should exist

  Scenario: Cancel the wizard without persisting data
    Given the DevSynth CLI is installed
    When I cancel the requirements wizard
    Then no requirements file should exist
