Feature: Enhanced ChromaDB Integration
  As a developer
  I want to use enhanced ChromaDB features
  So that I can improve performance and track changes over time

  Scenario: Use caching layer to reduce disk I/O
    Given the memory store type is configured as "chromadb"
    When I store an item in the memory store
    And I retrieve the same item multiple times
    Then the subsequent retrievals should use the cache
    And disk I/O operations should be reduced

  Scenario: Version tracking for stored artifacts
    Given the memory store type is configured as "chromadb"
    When I store an item in the memory store
    And I update the same item with new content
    Then both versions of the item should be available
    And I should be able to retrieve the item history
    And the latest version should be returned by default

  Scenario: Retrieve specific version of an item
    Given the memory store type is configured as "chromadb"
    And I have stored multiple versions of an item
    When I request a specific version of the item
    Then that specific version should be returned

  Scenario: Optimized embedding storage
    Given the memory store type is configured as "chromadb"
    When I store multiple items with similar content
    Then the embedding storage should be optimized
    And similar embeddings should be stored efficiently
