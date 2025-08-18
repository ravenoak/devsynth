Feature: Project Documentation Ingestion
  As a developer
  I want the system to ingest project documentation
  So that specifications and guides are indexed for retrieval

  Scenario: Ingests markdown documents with metadata
    Given a repository containing documentation with YAML front matter
    When the project documentation ingestion runs
    Then each document's title and path are recorded in the index
