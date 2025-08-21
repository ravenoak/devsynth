Feature: Multi-Layered Memory System and Tiered Cache Strategy
  As a developer
  I want frequently accessed memory items cached across layers
  So that subsequent retrievals are fast

  Background:
    Given a memory system with a cache size of 2

  @fast @memory
  Scenario: Second retrieval hits the cache
    Given I store an item "alpha" in short-term memory
    When I retrieve "alpha" twice
    Then the first retrieval results in a cache miss
    And the second retrieval results in a cache hit

  @fast @memory
  Scenario: LRU eviction removes least recently used item
    Given I store items "alpha" and "beta" in short-term memory
    And I retrieve "alpha"
    And I store item "gamma" in short-term memory
    When I retrieve "beta"
    Then the retrieval results in a cache miss
    And the cache contains "gamma"
