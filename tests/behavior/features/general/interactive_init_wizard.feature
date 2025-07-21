Feature: Interactive Init Wizard
  As a developer
  I want to configure my project through a guided wizard
  So that optional features are enabled correctly

  Scenario: Run the initialization wizard
    Given the DevSynth CLI is installed
    When I run the initialization wizard
    Then a project configuration file should include the selected options
