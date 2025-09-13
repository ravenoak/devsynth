# Related issue: ../../../../docs/specifications/requirements_gathering.md
Feature: Requirements Gathering Wizard
  As a developer
  I want to capture project goals and constraints interactively
  So that they are stored in the configuration

  Scenario: Gather goals using the CLI wizard
    Given the DevSynth CLI is installed
    When I run the requirements gathering wizard
    Then a requirements plan file "requirements_plan.yaml" should exist

  Scenario: Gather goals using the WebUI wizard
    Given the WebUI is initialized
    When I run the requirements gathering wizard in the WebUI
    Then a requirements plan file "requirements_plan.yaml" should exist
