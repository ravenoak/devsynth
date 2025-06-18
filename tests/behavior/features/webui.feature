Feature: WebUI Interaction
  As a developer
  I want to run DevSynth workflows from a browser
  So that the WebUI mirrors CLI functionality

  Scenario: Initialize a project using the WebUI
    Given the DevSynth WebUI is running
    When I navigate to the "Onboarding" page
    And I submit the initialization form
    Then the init workflow should execute via UXBridge

  Scenario: Generate specifications through the WebUI
    Given the DevSynth WebUI is running
    When I navigate to the "Requirements" page
    And I submit the specification form
    Then the spec workflow should execute via UXBridge

  Scenario: Update configuration from the WebUI
    Given the DevSynth WebUI is running
    When I navigate to the "Config" page
    And I update a setting
    Then the config workflow should execute via UXBridge
