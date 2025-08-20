# Specification: docs/specifications/edrr-coordinator.md
Feature: EDRR Coordinator
  As a workflow orchestrator
  I want to coordinate EDRR phases across agents
  So that iterative cycles produce consistent results

  Background:
    Given a coordinator managing Expand, Differentiate, Refine, and Retrospect phases

  Scenario: Coordinator completes phases in order
    Given an initial context
    When the coordinator executes an EDRR cycle
    Then the coordinator reports completion
    And the final context contains results from all phases

  Scenario: Coordinator converges on a consistent result after conflicts
    Given agents produce conflicting outcomes during the Refine phase
    When the coordinator launches a micro cycle to reconcile differences
    Then the cycle terminates with a single coherent context
    And no further phase transitions occur
