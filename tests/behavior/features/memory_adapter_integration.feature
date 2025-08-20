Feature: Memory Adapter Integration
  As a system integrator
  I want the memory manager to coordinate multiple adapters
  So that data remains consistent across storage backends

  Background:
    Given a memory manager configured with adapters "graph" and "tinydb"

  @slow @property
  Scenario: adapters maintain consistent state under randomized operations
    When I execute a random sequence of store and retrieve operations across adapters
    Then all adapters should reflect the same set of memory item identifiers
    And no operation should corrupt or lose previously stored items
