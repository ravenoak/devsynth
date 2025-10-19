Feature: Enhanced EDRR Memory Integration
  As a developer
  I want enhanced memory integration in the EDRR framework
  So that knowledge is preserved, retrieved, and utilized more effectively across cycles

  Background:
    Given the EDRR coordinator is initialized with enhanced memory features
    And the memory system is available with graph capabilities
    And the WSDE team is available
    And the AST analyzer is available
    And the prompt manager is available
    And the documentation manager is available

  Scenario: Context-aware memory retrieval
    Given the EDRR coordinator is in the "Differentiate" phase
    When the coordinator needs to retrieve relevant information from memory
    Then the retrieval should be context-aware based on the current phase
    And the retrieval should prioritize items relevant to the current task
    And the retrieval should consider semantic similarity beyond exact matches
    And the retrieval should include items from previous related cycles
    And the retrieved items should be ranked by relevance to the current context
    And the coordinator should use this context-aware information in the current phase

  Scenario: Memory persistence across cycles
    Given the EDRR coordinator has completed a cycle for a specific domain
    When a new cycle is started in the same domain
    Then knowledge from the previous cycle should be accessible
    And insights from the previous cycle should influence the new cycle
    And the coordinator should establish explicit links between related cycles
    And the memory persistence should work across different memory adapter types
    And the persistent memory should be queryable with domain-specific filters

  Scenario: Enhanced knowledge graph integration
    Given the memory system is configured with graph capabilities
    When the EDRR coordinator stores and retrieves information
    Then the information should be stored in a knowledge graph structure
    And the knowledge graph should capture relationships between concepts
    And the knowledge graph should support transitive inference
    And the coordinator should be able to traverse the graph to find related information
    And the knowledge graph should evolve and refine with new information
    And the coordinator should use graph-based reasoning for complex queries

  Scenario: Multi-modal memory with heterogeneous data types
    Given the EDRR coordinator processes different types of information
    When this information is stored in memory
    Then the memory system should handle multiple data modalities
    And code snippets should be stored with AST metadata
    And natural language should be stored with semantic metadata
    And diagrams should be stored with structural metadata
    And the coordinator should retrieve information across modalities
    And cross-modal relationships should be preserved in the memory graph

  Scenario: Memory with temporal awareness and versioning
    Given the EDRR coordinator evolves knowledge over time
    When information is updated in subsequent cycles
    Then the memory system should maintain version history
    And the coordinator should be able to retrieve specific versions
    And the memory should track when and why information was updated
    And temporal queries should be supported (e.g., "as of last week")
    And the coordinator should be able to compare different versions of the same knowledge
    And the memory system should support rollback to previous versions if needed
