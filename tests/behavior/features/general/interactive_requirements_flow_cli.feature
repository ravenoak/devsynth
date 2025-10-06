Feature: Interactive Requirements Flow CLI
  As a maintainer collecting baseline project data
  I want the CLI flow to write a structured plan
  So that gathered inputs seed downstream automation

  Scenario: Gather requirements through the CLI collector
    Given the DevSynth CLI is installed
    When I run the interactive requirements flow
    Then an interactive requirements file "interactive_requirements.json" should exist
