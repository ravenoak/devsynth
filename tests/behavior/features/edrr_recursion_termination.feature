# Related issue: ../../docs/specifications/edrr-recursion-termination.md
Feature: Edrr recursion termination
  As a developer
  I want recursion guards to trigger before the coordinator spawns unsafe cycles
  So that nested EDRR flows remain bounded and auditable

  @fast @reqid-edrr-recursion-termination
  Scenario: Validate Edrr recursion termination
    Given the specification "edrr-recursion-termination.md" exists
    Then the BDD coverage acknowledges the specification

  Scenario: Maximum recursion depth stops new cycles
    Given the coordinator is operating at its configured recursion depth limit
    When the coordinator evaluates a micro-cycle request
    Then recursion terminates because the depth cap has been reached
    And human overrides can still resume recursion when explicitly requested
