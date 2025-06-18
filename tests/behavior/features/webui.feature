Feature: WebUI Interaction
  As a developer
  I want to interact with DevSynth through a web interface
  So that I can run workflows without the command line

  Scenario: Initialize a project using the WebUI
    Given the DevSynth WebUI is running
    When I navigate to the "Onboarding" section
    And I submit the initialization form
    Then the init workflow should execute via UXBridge

