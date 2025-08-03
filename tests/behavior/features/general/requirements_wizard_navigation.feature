Feature: Requirements Wizard Navigation
  As a developer
  I want to move through the requirements wizard
  So that I can review my answers before saving

  Scenario: Navigate forward and backward
    Given the WebUI is initialized
    When I open the requirements wizard
    And I click the wizard next button
    Then the wizard should show step 2
    When I click the wizard back button
    Then the wizard should show step 1

  Scenario: Cancel resets wizard state
    Given the WebUI is initialized
    When I open the requirements wizard
    And I click the wizard next button
    And I click the wizard cancel button
    Then the wizard state should reset to step 1
