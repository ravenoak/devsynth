# Related issue: ../../docs/specifications/dialectical_reasoning.md
Feature: Dialectical reasoner evaluation hooks
  As a quality engineer
  I want hooks to observe reasoning outcomes
  So that consensus decisions are auditable

  Scenario: Hook receives consensus result
    Given a dialectical reasoner with a registered hook
    When I evaluate a change that reaches consensus
    Then the hook should receive the reasoning and consensus flag
