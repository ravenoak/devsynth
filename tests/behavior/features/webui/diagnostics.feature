Feature: WebUI Diagnostics Page
  As a developer
  I want to run detailed diagnostics on my project in the WebUI
  So that I can identify and resolve complex issues in my development environment

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Diagnostics page
    When I navigate to "Diagnostics"
    Then the Diagnostics page should be displayed

  Scenario: Run basic diagnostics
    When I navigate to "Diagnostics"
    And I click the run basic diagnostics button
    Then the basic diagnostics should run
    And the diagnostics results should be displayed

  Scenario: Run advanced diagnostics
    When I navigate to "Diagnostics"
    And I select advanced diagnostics mode
    And I click the run diagnostics button
    Then the advanced diagnostics should run
    And the detailed diagnostics results should be displayed

  Scenario: Run performance diagnostics
    When I navigate to "Diagnostics"
    And I select performance diagnostics mode
    And I click the run diagnostics button
    Then the performance diagnostics should run
    And the performance metrics should be displayed

  Scenario: Run memory diagnostics
    When I navigate to "Diagnostics"
    And I select memory diagnostics mode
    And I click the run diagnostics button
    Then the memory diagnostics should run
    And the memory usage metrics should be displayed

  Scenario: Run network diagnostics
    When I navigate to "Diagnostics"
    And I select network diagnostics mode
    And I click the run diagnostics button
    Then the network diagnostics should run
    And the network connectivity results should be displayed

  Scenario: Export diagnostics report
    When I navigate to "Diagnostics"
    And I click the run diagnostics button
    And I click the export report button
    Then the diagnostics report should be exported

  Scenario: Schedule periodic diagnostics
    When I navigate to "Diagnostics"
    And I click the schedule button
    And I configure the diagnostics schedule
    And I save the schedule
    Then the diagnostics should be scheduled
    And a success message should be displayed

  Scenario: View diagnostics history
    When I navigate to "Diagnostics"
    And I click the history button
    Then the diagnostics history should be displayed
    And previous diagnostics results should be available for review
