Feature: WebUI Requirements Wizard with WizardState
  As a developer
  I want to capture requirements using a guided wizard in the WebUI with proper state management
  So that I can easily define and organize project requirements

  Background:
    Given the WebUI is initialized

  Scenario: Start the Requirements wizard
    When I navigate to "Requirements"
    And I click the start requirements wizard button
    Then the requirements wizard should be displayed
    And the wizard should show the first step

  Scenario: Navigate through Requirements wizard steps
    When I navigate to "Requirements"
    And I click the start requirements wizard button
    And I click the wizard next button
    Then the wizard should show step 2
    When I click the wizard back button
    Then the wizard should show step 1

  Scenario: Complete the Requirements wizard
    When I navigate to "Requirements"
    And I click the start requirements wizard button
    And I enter project goals information
    And I click the wizard next button
    And I enter project constraints information
    And I click the wizard next button
    And I enter project priorities
    And I click the finish button
    Then the requirements process should complete
    And a success message should be displayed
    And the requirements should be saved to "requirements_wizard.json"

  Scenario: Cancel the Requirements wizard
    When I navigate to "Requirements"
    And I click the start requirements wizard button
    And I enter project goals information
    And I click the cancel button
    Then the wizard should be closed
    And no requirements file should be created

  Scenario: Requirements wizard validates input
    When I navigate to "Requirements"
    And I click the start requirements wizard button
    And I enter invalid project goals information
    And I click the wizard next button
    Then validation errors should be displayed
    And the wizard should remain on the current step

  Scenario: Requirements wizard persists state between steps
    When I navigate to "Requirements"
    And I click the start requirements wizard button
    And I enter project goals information
    And I click the wizard next button
    And I enter project constraints information
    And I click the wizard back button
    Then the previously entered project goals information should be preserved

  Scenario: Requirements wizard handles errors gracefully
    When I navigate to "Requirements"
    And I click the start requirements wizard button
    And I trigger an error condition
    Then an error message should be displayed
    And the wizard state should be properly reset
