Feature: Kuzu memory integration
  Scenario: Ephemeral store falls back when disabled
    Given DEVSYNTH_KUZU_EMBEDDED is "false"
    When I initialise an ephemeral Kuzu store
    Then the store should use the in-memory fallback
