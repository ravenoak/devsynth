Feature: WebUI Validate Metadata Page
  As a developer
  I want to validate project metadata in the WebUI
  So that I can ensure my project metadata is accurate and complete

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Validate Metadata page
    When I navigate to "Validate Metadata"
    Then the validate metadata page should be displayed

  Scenario: Validate project metadata
    When I navigate to "Validate Metadata"
    And I submit the validate metadata form
    Then the metadata validation results should be displayed

  Scenario: Validate metadata with specific schema
    When I navigate to "Validate Metadata"
    And I select a specific metadata schema
    And I submit the validate metadata form
    Then the metadata validation results with the selected schema should be displayed

  Scenario: Fix metadata issues automatically
    When I navigate to "Validate Metadata"
    And I submit the validate metadata form
    And validation issues are found
    And I click the auto-fix button
    Then the metadata issues should be fixed automatically
    And a success message should be displayed

  Scenario: Export metadata validation report
    When I navigate to "Validate Metadata"
    And I submit the validate metadata form
    And I click the export report button
    Then the metadata validation report should be exported

  Scenario: View metadata validation history
    When I navigate to "Validate Metadata"
    And I click the validation history button
    Then the metadata validation history should be displayed
    And previous validation results should be available for review

  Scenario: Compare metadata with template
    When I navigate to "Validate Metadata"
    And I select a metadata template for comparison
    And I submit the validate metadata form
    Then the metadata comparison results should be displayed
    And differences from the template should be highlighted
