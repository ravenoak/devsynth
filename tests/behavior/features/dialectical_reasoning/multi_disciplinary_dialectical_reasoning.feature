# Related issue: ../../../../issues/multi-disciplinary-dialectical-reasoning.md
Feature: Multi-disciplinary dialectical reasoning
  As a methodology developer
  I want dialectical reasoning to merge disciplinary perspectives
  So that solutions incorporate diverse expertise

  @fast
  Scenario: Reasoner gathers disciplinary perspectives
    Given a dialectical reasoner configured for multi-disciplinary analysis
    When a complex problem is evaluated
    Then the reasoner should request input from at least two disciplines
    And the gathered perspectives should be tracked with their disciplines
