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

  Scenario: WSDE workflow applies multi-disciplinary reasoning
    Given a WSDE team with multi-disciplinary reasoning support
    When the team executes a basic decision workflow
    Then the workflow output should include a multi-disciplinary evaluation
