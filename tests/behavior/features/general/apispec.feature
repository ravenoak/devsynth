Feature: WebUI APISpec Page
  As a developer
  I want to generate and manage API specifications in the WebUI
  So that I can document and standardize my API interfaces

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to APISpec page
    When I navigate to "APISpec"
    Then the APISpec page should be displayed

  Scenario: Generate API specification from code
    When I navigate to "APISpec"
    And I select source code for API specification
    And I submit the APISpec form
    Then the API specification should be generated
    And a success message should be displayed

  Scenario: Generate API specification with custom format
    When I navigate to "APISpec"
    And I select source code for API specification
    And I select a custom API specification format
    And I submit the APISpec form
    Then the API specification should be generated in the selected format
    And a success message should be displayed

  Scenario: Edit API specification
    When I navigate to "APISpec"
    And I select an existing API specification
    And I make changes to the specification
    And I save the changes
    Then the API specification should be updated
    And a success message should be displayed

  Scenario: Validate API specification
    When I navigate to "APISpec"
    And I select an existing API specification
    And I click the validate button
    Then the API specification validation results should be displayed

  Scenario: Export API specification
    When I navigate to "APISpec"
    And I select an existing API specification
    And I click the export button
    Then the API specification should be exported

  Scenario: Generate client code from API specification
    When I navigate to "APISpec"
    And I select an existing API specification
    And I select a target language for client code
    And I click the generate client button
    Then the client code should be generated
    And a success message should be displayed

  Scenario: View API specification history
    When I navigate to "APISpec"
    And I click the specification history button
    Then the API specification history should be displayed
    And previous versions should be available for review
