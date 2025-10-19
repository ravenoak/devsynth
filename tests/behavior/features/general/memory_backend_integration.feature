Feature: Memory Backend Integration
  As a developer using DevSynth
  I want to test all available memory backends
  So that I can ensure they work correctly with the WSDE model

  Background:
    Given the DevSynth system is initialized
    And a team of agents is configured
    And the WSDE model is enabled

  Scenario Outline: Store and retrieve WSDE artifacts in different memory backends
    Given the memory system is configured with a "<backend_type>" backend
    When I store a WSDE team state in the memory backend
    And I store a solution in the memory backend
    And I store a dialectical reasoning result in the memory backend
    Then I should be able to retrieve the team state from the memory backend
    And I should be able to retrieve the solution from the memory backend
    And I should be able to retrieve the dialectical reasoning result from the memory backend
    And all retrieved artifacts should match their original versions

    Examples:
      | backend_type |
      | memory       |
      | file         |
      | tinydb       |
      | chromadb     |
      | duckdb       |
      | faiss        |
      | json         |
      | lmdb         |
      | rdflib       |

  Scenario: Cross-backend relationships between WSDE artifacts
    Given the memory system is configured with multiple backends
    When I store team state in the "file" backend
    And I store a solution in the "tinydb" backend
    And I store a dialectical reasoning result in the "chromadb" backend
    And I create relationships between these artifacts
    Then I should be able to retrieve all artifacts from their respective backends
    And I should be able to traverse relationships between artifacts in different backends
    And the relationship metadata should correctly identify the source and target backends

  Scenario: Memory backend performance comparison
    Given the memory system is configured with all available backends
    When I perform a benchmark storing 100 memory items in each backend
    And I perform a benchmark retrieving items by type from each backend
    And I perform a benchmark retrieving items by metadata from each backend
    Then I should get performance metrics for each backend
    And I should be able to compare the performance of different backends
