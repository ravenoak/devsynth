Feature: Interactive Init Wizard
  As a developer bootstrapping a project
  I want the initialization wizard to honor environment defaults
  So that onboarding can run unattended when scripted

  Scenario: Run the initialization wizard with environment defaults
    Given the DevSynth CLI is installed
    When I run the initialization wizard
    Then a project configuration file should include the selected options
