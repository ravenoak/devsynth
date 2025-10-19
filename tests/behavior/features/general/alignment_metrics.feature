Feature: WebUI Alignment Metrics Page
  As a developer
  I want to view and analyze alignment metrics in the WebUI
  So that I can understand how well my implementation aligns with requirements

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Alignment Metrics page
    When I navigate to "Alignment Metrics"
    Then the alignment metrics page should be displayed

  Scenario: View alignment metrics
    When I navigate to "Alignment Metrics"
    And I submit the alignment metrics form
    Then the alignment metrics should be displayed

  Scenario: Filter alignment metrics by component
    When I navigate to "Alignment Metrics"
    And I select a specific component for alignment analysis
    And I submit the alignment metrics form
    Then the filtered alignment metrics should be displayed

  Scenario: Export alignment metrics report
    When I navigate to "Alignment Metrics"
    And I submit the alignment metrics form
    And I click the export report button
    Then the alignment metrics report should be exported

  Scenario: View alignment metrics visualization
    When I navigate to "Alignment Metrics"
    And I submit the alignment metrics form
    And I click the visualization tab
    Then the alignment metrics visualization should be displayed

  Scenario: Compare alignment metrics between versions
    When I navigate to "Alignment Metrics"
    And I select multiple versions for comparison
    And I submit the alignment metrics form
    Then the alignment metrics comparison should be displayed
