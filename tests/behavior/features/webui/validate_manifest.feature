Feature: WebUI Validate Manifest Page
  As a developer
  I want to validate project manifests in the WebUI
  So that I can ensure my project structure is correct and complete

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Validate Manifest page
    When I navigate to "Validate Manifest"
    Then the validate manifest page should be displayed

  Scenario: Validate project manifest
    When I navigate to "Validate Manifest"
    And I submit the validate manifest form
    Then the manifest validation results should be displayed

  Scenario: Validate manifest with custom rules
    When I navigate to "Validate Manifest"
    And I select custom validation rules
    And I submit the validate manifest form
    Then the manifest validation results with custom rules should be displayed

  Scenario: Fix manifest issues automatically
    When I navigate to "Validate Manifest"
    And I submit the validate manifest form
    And validation issues are found
    And I click the auto-fix button
    Then the manifest issues should be fixed automatically
    And a success message should be displayed

  Scenario: Export manifest validation report
    When I navigate to "Validate Manifest"
    And I submit the validate manifest form
    And I click the export report button
    Then the manifest validation report should be exported

  Scenario: View manifest validation history
    When I navigate to "Validate Manifest"
    And I click the validation history button
    Then the manifest validation history should be displayed
    And previous validation results should be available for review
