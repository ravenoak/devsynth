Feature: Version-Aware Documentation Management
  As a developer
  I want to fetch and manage version-specific documentation
  So that I can access accurate information for the libraries I'm using

  Background:
    Given the documentation management system is initialized

  Scenario: Fetch and store documentation for a specific library version
    When I request documentation for "requests" version "2.28.1"
    Then the documentation should be fetched from the appropriate source
    And stored in the documentation repository
    And I should be able to query information about HTTP requests

  Scenario: Use cached documentation for previously fetched versions
    Given documentation for "numpy" version "1.22.4" has been previously fetched
    When I request documentation for "numpy" version "1.22.4" again
    Then the system should use the cached documentation
    And not fetch from external sources

  Scenario: Detect version drift and update documentation
    Given documentation for "pandas" version "1.4.2" is stored
    When a new version "1.5.0" is detected
    Then the system should flag the documentation as outdated
    And offer to update to the new version

  Scenario: Query documentation across multiple libraries
    Given documentation for multiple libraries is available:
      | library | version |
      | numpy   | 1.22.4  |
      | pandas  | 1.4.2   |
      | scipy   | 1.8.1   |
    When I query for information about "statistical functions"
    Then I should receive relevant documentation from all applicable libraries
    And the results should be ranked by relevance

  Scenario: Filter documentation by version constraints
    Given documentation for multiple versions of "tensorflow" is available:
      | version |
      | 2.8.0   |
      | 2.9.0   |
      | 2.10.0  |
    When I query for "keras API" with version constraint ">= 2.9.0"
    Then I should only receive documentation from versions 2.9.0 and 2.10.0
    And not from version 2.8.0

  Scenario: Documentation ingestion with memory integration
    When I fetch documentation for "scikit-learn" version "1.1.2"
    Then the documentation chunks should be stored in the vector memory store
    And metadata should be stored in the structured memory store
    And relationships should be stored in the knowledge graph
