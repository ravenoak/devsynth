Feature: WebUI Onboarding Flow
  As a maintainer using the onboarding dashboard
  I want the WebUI to surface the wizard and trigger initialization
  So that onboarding actions match the CLI experience

  Scenario: Open the onboarding workspace
    Given the WebUI is initialized
    When I navigate to "Onboarding"
    Then the "Project Onboarding" header is shown

  Scenario: Submit onboarding form through the WebUI
    Given the WebUI is initialized
    When I submit the onboarding form
    Then the init command should be executed
