Feature: Interactive Requirements Flow WebUI
  As a developer
  I want to gather basic project settings through the WebUI
  So that they are saved for later use

  Scenario: Gather project settings using the WebUI
    Given the WebUI is initialized
    When I run the interactive requirements flow in the WebUI
    Then an interactive requirements file "interactive_requirements.json" should exist
