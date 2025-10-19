Feature: WebUI Inspect Config Page
  As a developer
  I want to inspect and analyze configuration settings in the WebUI
  So that I can understand and verify my project's configuration

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Inspect Config page
    When I navigate to "Inspect Config"
    Then the inspect config page should be displayed

  Scenario: View configuration details
    When I navigate to "Inspect Config"
    And I submit the inspect config form
    Then the configuration details should be displayed

  Scenario: Filter configuration by category
    When I navigate to "Inspect Config"
    And I select a specific configuration category
    And I submit the inspect config form
    Then the filtered configuration details should be displayed

  Scenario: Search for specific configuration keys
    When I navigate to "Inspect Config"
    And I enter a search term in the configuration search field
    And I submit the inspect config form
    Then the matching configuration keys should be displayed

  Scenario: Export configuration report
    When I navigate to "Inspect Config"
    And I submit the inspect config form
    And I click the export config button
    Then the configuration report should be exported

  Scenario: Compare configuration with defaults
    When I navigate to "Inspect Config"
    And I enable the "Compare with defaults" option
    And I submit the inspect config form
    Then the configuration comparison should be displayed
    And differences from default values should be highlighted
