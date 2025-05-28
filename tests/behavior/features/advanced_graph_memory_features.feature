Feature: Advanced Graph Memory Features
  As a developer using DevSynth
  I want to use advanced features of the GraphMemoryAdapter
  So that I can leverage RDFLib integration, memory volatility controls, and memory store integration

  Background:
    Given the DevSynth system is initialized
    And the GraphMemoryAdapter is configured with RDFLibStore integration

  Scenario: Use RDFLib namespace handling and graph serialization
    Given I have a GraphMemoryAdapter with RDFLibStore integration
    When I store a memory item with content "Test content with namespaces"
    Then the memory item should be stored with proper namespace handling
    And the graph should be serialized in Turtle format
    And I should be able to retrieve the memory item with its original content

  Scenario: Use advanced RDF triple patterns
    Given I have a GraphMemoryAdapter with RDFLibStore integration
    When I store a memory item with complex metadata:
      | key           | value                 |
      | edrr_phase    | EXPAND                |
      | priority      | high                  |
      | tags          | python,code,important |
    Then the memory item should be stored as RDF triples
    And I should be able to retrieve the memory item with all metadata intact

  Scenario: Apply memory volatility controls
    Given I have a GraphMemoryAdapter with RDFLibStore integration
    When I add memory volatility controls with decay rate 0.1 and threshold 0.5
    Then all memory items should have confidence values
    And all memory items should have decay rates
    And all memory items should have confidence thresholds

  Scenario: Apply advanced memory decay
    Given I have a GraphMemoryAdapter with RDFLibStore integration
    And I have added memory volatility controls
    And I have stored multiple memory items with different access patterns
    When I apply advanced memory decay
    Then items accessed less frequently should decay faster
    And items with more relationships should decay slower
    And items that haven't been accessed recently should decay faster

  Scenario: Integrate with another memory store
    Given I have a GraphMemoryAdapter with RDFLibStore integration
    And I have a TinyDBMemoryAdapter
    When I integrate the GraphMemoryAdapter with the TinyDBMemoryAdapter in "bidirectional" mode
    Then memory items from the GraphMemoryAdapter should be exported to the TinyDBMemoryAdapter
    And memory items from the TinyDBMemoryAdapter should be imported to the GraphMemoryAdapter
    And I should be able to retrieve the same items from both adapters

  Scenario: Integrate with a vector store
    Given I have a GraphMemoryAdapter with RDFLibStore integration
    And I have a ChromaDBVectorStore
    When I integrate the GraphMemoryAdapter with the ChromaDBVectorStore in "bidirectional" mode
    Then memory items with vectors should be properly synchronized between stores
    And I should be able to perform vector similarity searches on both stores