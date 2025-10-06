Feature: Interactive Requirements Wizard
  As a developer using the CLI wizard
  I want the bridge-backed flow to persist answers
  So that requirements are saved for later automation

  Scenario: Persist responses from the CLI wizard
    Given the DevSynth CLI is installed
    When I run the interactive requirements wizard
    Then a structured requirements file "requirements_wizard.json" should exist
