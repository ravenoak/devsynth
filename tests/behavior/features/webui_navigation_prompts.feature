Feature: WebUI Navigation and Prompts
  As a developer
  I want to navigate the WebUI and respond to prompts
  So that workflows can be driven graphically

  Scenario: Navigate to Requirements page
    Given the WebUI is initialized
    When I navigate to "Requirements"
    Then the "Requirements Gathering" header is shown

  Scenario: Submit onboarding information when prompted
    Given the WebUI is initialized
    When I navigate to "Onboarding"
    And I submit the onboarding form
    Then the init command should be executed

  Scenario: Navigate to Analysis page
    Given the WebUI is initialized
    When I navigate to "Analysis"
    Then the "Code Analysis" header is shown

  Scenario: Navigate to Synthesis page
    Given the WebUI is initialized
    When I navigate to "Synthesis"
    Then the "Synthesis Execution" header is shown

  Scenario: Navigate to Config page
    Given the WebUI is initialized
    When I navigate to "Config"
    Then the "Configuration Editing" header is shown
