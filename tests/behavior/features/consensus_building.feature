# Related issue: ../../../docs/specifications/consensus-building.md
Feature: Consensus Building
  As a decision-making system
  I want to derive a consensus from agent votes
  So that teams can agree on a single option

  Scenario: Consensus reached with majority
    Given votes "A,B,A"
    When we build consensus
    Then consensus decision is "A"

  Scenario: No consensus reached
    Given votes "A,B"
    When we build consensus with threshold 0.6
    Then no consensus decision is made
