Feature: Additional Storage Backends
  As a developer
  I want to use different storage backends (TinyDB, DuckDB, LMDB)
  So that I can choose the best option for my specific use case

  Scenario: Initialize TinyDB memory store
    Given the DevSynth CLI is installed
    When I configure the memory store type as "tinydb"
    Then a TinyDB memory store should be initialized

  Scenario: Store and retrieve items with TinyDB
    Given the memory store type is configured as "tinydb"
    When I store an item in the memory store
    Then I should be able to retrieve the item by its ID

  Scenario: Search items with TinyDB
    Given the memory store type is configured as "tinydb"
    And I have stored multiple items with different content
    When I search for items with specific criteria
    Then I should receive items matching the criteria

  Scenario: TinyDB memory store persistence
    Given the memory store type is configured as "tinydb"
    And I have stored items in the memory store
    When I restart the application
    Then the previously stored items should still be available

  Scenario: Initialize DuckDB memory store
    Given the DevSynth CLI is installed
    When I configure the memory store type as "duckdb"
    Then a DuckDB memory store should be initialized

  Scenario: Store and retrieve items with DuckDB
    Given the memory store type is configured as "duckdb"
    When I store an item in the memory store
    Then I should be able to retrieve the item by its ID

  Scenario: Search items with DuckDB
    Given the memory store type is configured as "duckdb"
    And I have stored multiple items with different content
    When I search for items with specific criteria
    Then I should receive items matching the criteria

  Scenario: DuckDB memory store persistence
    Given the memory store type is configured as "duckdb"
    And I have stored items in the memory store
    When I restart the application
    Then the previously stored items should still be available

  Scenario: Store and retrieve vectors with DuckDB
    Given the memory store type is configured as "duckdb"
    And vector store is enabled
    When I store a vector in the vector store
    Then I should be able to retrieve the vector by its ID

  Scenario: Perform similarity search with DuckDB
    Given the memory store type is configured as "duckdb"
    And vector store is enabled
    And I have stored multiple vectors with different embeddings
    When I perform a similarity search with a query embedding
    Then I should receive vectors ranked by similarity

  Scenario: Initialize LMDB memory store
    Given the DevSynth CLI is installed
    When I configure the memory store type as "lmdb"
    Then a LMDB memory store should be initialized

  Scenario: Store and retrieve items with LMDB
    Given the memory store type is configured as "lmdb"
    When I store an item in the memory store
    Then I should be able to retrieve the item by its ID

  Scenario: Search items with LMDB
    Given the memory store type is configured as "lmdb"
    And I have stored multiple items with different content
    When I search for items with specific criteria
    Then I should receive items matching the criteria

  Scenario: LMDB memory store persistence
    Given the memory store type is configured as "lmdb"
    And I have stored items in the memory store
    When I restart the application
    Then the previously stored items should still be available

  Scenario: LMDB transaction support
    Given the memory store type is configured as "lmdb"
    When I begin a transaction
    And I store multiple items within the transaction
    And I commit the transaction
    Then all items should be stored atomically

  Scenario: LMDB transaction rollback
    Given the memory store type is configured as "lmdb"
    And I have stored an item in the memory store
    When I begin a transaction
    And I modify the item within the transaction
    And I abort the transaction
    Then the item should remain unchanged

  Scenario: Initialize FAISS vector store
    Given the DevSynth CLI is installed
    When I configure the memory store type as "faiss"
    Then a FAISS vector store should be initialized

  Scenario: Store and retrieve vectors with FAISS
    Given the memory store type is configured as "faiss"
    When I store a vector in the vector store
    Then I should be able to retrieve the vector by its ID

  Scenario: Perform similarity search with FAISS
    Given the memory store type is configured as "faiss"
    And I have stored multiple vectors with different embeddings
    When I perform a similarity search with a query embedding
    Then I should receive vectors ranked by similarity

  Scenario: FAISS vector store persistence
    Given the memory store type is configured as "faiss"
    And I have stored vectors in the vector store
    When I restart the application
    Then the previously stored vectors should still be available

  Scenario: Get FAISS collection statistics
    Given the memory store type is configured as "faiss"
    And I have stored multiple vectors in the vector store
    When I request collection statistics
    Then I should receive information about the vector collection
