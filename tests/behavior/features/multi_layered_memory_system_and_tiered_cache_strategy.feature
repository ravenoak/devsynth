Feature: Multi-Layered Memory System and Tiered Cache Strategy
  As a developer
  I want a memory system with multiple cache tiers
  So that frequently accessed data is retrieved quickly

  Scenario: Value is promoted to the first layer after access
    Given a two-layer memory system with a key stored in the second layer
    When the key is retrieved
    Then the value is returned
    And the first layer now contains the key

  Scenario: Cache hit ratio is calculated
    Given an empty two-layer memory system
    When a key is stored and retrieved twice
    And a missing key is requested once
    Then the overall cache hit ratio is 2/3
