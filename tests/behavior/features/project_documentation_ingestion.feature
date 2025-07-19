Feature: Project Documentation Ingestion
  As a developer
  I want DevSynth to ingest documentation directories defined in project.yaml
  So that the documentation is available in the memory system

  Scenario: Ingest documentation from configured docs directory
    Given a project with a docs directory configured in project.yaml
    When I ingest documentation using the project configuration
    Then the documentation files should be stored in memory
