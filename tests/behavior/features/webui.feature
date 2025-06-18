Feature: Streamlit WebUI Navigation
  As a developer
  I want to access DevSynth workflows via a WebUI
  So that I can manage projects graphically

  Scenario: Open Requirements page
    Given the WebUI is initialized
    When I navigate to "Requirements"
    Then the "Requirements Gathering" header is shown

  Scenario: Submit onboarding form
    Given the WebUI is initialized
    When I navigate to "Onboarding"
    And I submit the onboarding form
    Then the init command should be executed

  Scenario: Update configuration value
    Given the WebUI is initialized
    When I navigate to "Config"
    And I update a configuration value
    Then the config command should be executed

