Feature: WebUI Gather Wizard
  As a developer
  I want to gather project information using a guided wizard in the WebUI
  So that I can easily collect and organize project resources

  Background:
    Given the WebUI is initialized

  Scenario: Start the Gather wizard
    When I navigate to "Requirements"
    And I click the start gather wizard button
    Then the gather wizard should be displayed
    And the wizard should show the first step

  Scenario: Navigate through Gather wizard steps
    When I navigate to "Requirements"
    And I click the start gather wizard button
    And I click the wizard next button
    Then the wizard should show step 2
    When I click the wizard back button
    Then the wizard should show step 1

  Scenario: Complete the Gather wizard
    When I navigate to "Requirements"
    And I click the start gather wizard button
    And I enter project resource information
    And I click the wizard next button
    And I enter resource location information
    And I click the wizard next button
    And I enter resource metadata
    And I click the finish button
    Then the gather process should complete
    And a success message should be displayed
    And the gathered resources should be available in the project

  Scenario: Cancel the Gather wizard
    When I navigate to "Requirements"
    And I click the start gather wizard button
    And I enter project resource information
    And I click the cancel button
    Then the wizard should be closed
    And no changes should be made to the project

  Scenario: Gather wizard validates input
    When I navigate to "Requirements"
    And I click the start gather wizard button
    And I enter invalid project resource information
    And I click the wizard next button
    Then validation errors should be displayed
    And the wizard should remain on the current step

  Scenario: Gather wizard persists state between steps
    When I navigate to "Requirements"
    And I click the start gather wizard button
    And I enter project resource information
    And I click the wizard next button
    And I enter resource location information
    And I click the wizard back button
    Then the previously entered project resource information should be preserved

  Scenario: Gather wizard with custom resource types
    When I navigate to "Requirements"
    And I click the start gather wizard button
    And I select a custom resource type
    And I enter custom resource information
    And I complete the wizard
    Then the custom resources should be gathered
    And a success message should be displayed
