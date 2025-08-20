Feature: Project State Analysis
  As a developer
  I want to analyze the state of my project
  So that I can understand its completeness

  Scenario: Generate project state summary
    Given a project with requirements, specifications, tests, and code
    When I analyze the project state
    Then the analysis reports counts for requirements, specifications, tests, and code
    And the analysis includes a health score between 0 and 10
