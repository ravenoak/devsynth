Feature: ChromaDB memory store
  In order to store optimized embeddings
  As a developer
  I want to inspect embedding optimization and efficiency

  Scenario: ChromaDB store reports optimized embeddings
    Given a ChromaDB memory store
    When I check its embedding optimization
    Then it should report optimized embeddings
    And the embedding storage efficiency is above 0.0
