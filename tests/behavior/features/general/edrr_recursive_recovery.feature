Feature: Recursive EDRR phase recovery
  Scenario: Recovery hook enables recursive phase transition
    Given an enhanced coordinator with a micro cycle and failing metrics
    When recovery hooks adjust metrics
    Then the micro cycle transitions to the next phase
