Feature: WebUI Onboarding Flow
  As a developer
  I want to onboard my project using the WebUI
  So that initialization runs through a graphical form

  Scenario: Open onboarding page
    Given the WebUI is initialized
    When I navigate to "Onboarding"
    Then the "Project Onboarding" header is shown

  Scenario: Submit onboarding form via WebUI
    Given the WebUI is initialized
    When I submit the onboarding form
    Then the init command should be executed
