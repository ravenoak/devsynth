Feature: Interactive Requirements Flow CLI
  As a developer
  I want to gather basic project settings interactively
  So that they are saved for later use

  Scenario: Gather project settings using the CLI
    Given the DevSynth CLI is installed
    When I run the interactive requirements flow
    Then an interactive requirements file "interactive_requirements.json" should exist
