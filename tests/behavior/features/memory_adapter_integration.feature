Feature: Memory Adapter Integration
  As a developer
  I want the memory manager to work with multiple adapters
  So that information stored in different adapters can be queried consistently

  Scenario: Store items in graph and tinydb adapters
    Given a memory manager with graph and tinydb adapters
    When I store a graph memory item with id "G1"
    And I store a tinydb memory item with id "T1"
    Then querying items by type should return both stored items
