# Related issue: ../../docs/specifications/dialectical_reasoning.md
Feature: Dialectical reasoner evaluation hooks
  As a quality engineer
  I want hooks to observe reasoning outcomes
  So that consensus decisions are auditable

  Scenario: Hook records consensus success
    Given a dialectical reasoner with a registered hook
    And the evaluation outcome will reach consensus
    When I evaluate the change
    Then the hook should record the evaluation outcome

  Scenario: Hook records consensus failure
    Given a dialectical reasoner with a registered hook
    And the evaluation outcome will fail to reach consensus
    When I evaluate the change
    Then the hook should record the evaluation outcome
