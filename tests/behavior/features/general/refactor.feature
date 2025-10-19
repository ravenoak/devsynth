Feature: WebUI Refactor Page
  As a developer
  I want to refactor my code through the WebUI
  So that I can improve code quality and maintainability

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Refactor page
    When I navigate to "Refactor"
    Then the refactor page should be displayed

  Scenario: Analyze code for refactoring opportunities
    When I navigate to "Refactor"
    And I select source code for analysis
    And I submit the refactor analysis form
    Then the refactoring opportunities should be displayed

  Scenario: Apply automatic refactoring
    When I navigate to "Refactor"
    And I select source code for refactoring
    And I select automatic refactoring mode
    And I submit the refactor form
    Then the code should be refactored automatically
    And a success message should be displayed

  Scenario: Apply guided refactoring
    When I navigate to "Refactor"
    And I select source code for refactoring
    And I select guided refactoring mode
    And I submit the refactor form
    Then the guided refactoring steps should be displayed
    And I should be able to approve each refactoring step

  Scenario: Apply specific refactoring patterns
    When I navigate to "Refactor"
    And I select source code for refactoring
    And I select specific refactoring patterns
    And I submit the refactor form
    Then the selected refactoring patterns should be applied
    And a success message should be displayed

  Scenario: Preview refactoring changes
    When I navigate to "Refactor"
    And I select source code for refactoring
    And I select refactoring patterns
    And I click the preview button
    Then the refactoring changes should be previewed
    And I should be able to accept or reject the changes

  Scenario: View refactoring history
    When I navigate to "Refactor"
    And I click the refactoring history button
    Then the refactoring history should be displayed
    And previous refactoring operations should be available for review
