Feature: ChromaDB Integration
  As a developer
  I want to use ChromaDB as a memory store
  So that I can leverage vector database capabilities for semantic search

  Scenario: Initialize ChromaDB memory store
    Given the DevSynth CLI is installed
    When I configure the memory store type as "chromadb"
    Then a ChromaDB memory store should be initialized

  Scenario: Store and retrieve items with ChromaDB
    Given the memory store type is configured as "chromadb"
    When I store an item in the memory store
    Then I should be able to retrieve the item by its ID

  Scenario: Perform semantic search with ChromaDB
    Given the memory store type is configured as "chromadb"
    And I have stored multiple items with different content
    When I perform a semantic search for similar content
    Then I should receive items ranked by semantic similarity

  Scenario: ChromaDB memory store persistence
    Given the memory store type is configured as "chromadb"
    And I have stored items in the memory store
    When I restart the application
    Then the previously stored items should still be available
