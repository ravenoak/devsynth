Feature: Interactive Requirements Wizard
  As a developer
  I want to capture requirements using a guided wizard
  So that the results are stored in a structured file

  Scenario: Run the wizard from the CLI
    Given the DevSynth CLI is installed
    When I run the interactive requirements wizard
    Then a structured requirements file "requirements_wizard.json" should exist
