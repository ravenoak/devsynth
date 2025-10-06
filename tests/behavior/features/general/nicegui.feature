Feature: NiceGUI WebUI
  As a developer
  I want to interact with DevSynth through a NiceGUI interface
  So that I can run workflows in a modern web environment

  Scenario: Navigate to Diagnostics page
    Given the NiceGUI WebUI is initialized
    When I navigate to "Diagnostics"
    Then the Diagnostics page should be displayed
