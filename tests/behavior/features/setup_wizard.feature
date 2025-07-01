Feature: Setup Wizard
  As a developer
  I want a guided initialization wizard
  So that I can configure my project interactively

  Scenario: Run the setup wizard
    Given the DevSynth CLI is installed
    When I run the setup wizard
    Then a project configuration file should include the selected options

  Scenario: Cancel the setup wizard
    Given the DevSynth CLI is installed
    When I cancel the setup wizard
    Then no project configuration file should exist
