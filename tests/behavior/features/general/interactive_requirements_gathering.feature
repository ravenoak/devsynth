# Related issue: ../../docs/specifications/interactive_requirements_gathering.md
Feature: Interactive Requirements Gathering
  Scenario: Gather goals using the CLI wizard
    Given the DevSynth CLI is installed
    When I run the requirements gathering wizard
    Then a requirements plan file "requirements_plan.yaml" should exist

  Scenario: Gather goals using the WebUI wizard
    Given the WebUI is initialized
    When I run the requirements gathering wizard in the WebUI
    Then a requirements plan file "requirements_plan.yaml" should exist
