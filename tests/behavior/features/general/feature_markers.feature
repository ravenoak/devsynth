Feature: Feature Markers
  As a compliance officer
  I want feature marker functions
  So that auditing tools can trace requirements

  Scenario: Locate feature marker
    Given a documented feature
    When I search the marker module
    Then I find a corresponding marker function
