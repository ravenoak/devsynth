Feature: Interactive Requirements Flow WebUI
  As a maintainer driving onboarding from the browser
  I want the WebUI form to store gathered details
  So that the CLI and WebUI stay in sync

  Scenario: Gather requirements through the WebUI form
    Given the WebUI is initialized
    When I run the interactive requirements flow in the WebUI
    Then an interactive requirements file "interactive_requirements.json" should exist
