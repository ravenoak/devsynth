Feature: Comprehensive Documentation Ingestion
  As a developer
  I want to ingest documentation from various sources and formats
  So that I can access and query information efficiently

  Background:
    Given the documentation ingestion system is initialized
    And the memory system is available

  Scenario: Ingest documentation from Markdown files
    Given I have Markdown documentation files in a directory
    When I ingest the Markdown documentation
    Then the documentation should be processed and stored in the memory system
    And I should be able to query information from the Markdown documentation

  Scenario: Ingest documentation from text files
    Given I have text documentation files in a directory
    When I ingest the text documentation
    Then the documentation should be processed and stored in the memory system
    And I should be able to query information from the text documentation

  Scenario: Ingest documentation from JSON files
    Given I have JSON documentation files in a directory
    When I ingest the JSON documentation
    Then the documentation should be processed and stored in the memory system
    And I should be able to query information from the JSON documentation

  Scenario: Ingest documentation from Python files
    Given I have Python source files with docstrings in a directory
    When I ingest the Python documentation
    Then the documentation should be processed and stored in the memory system
    And I should be able to query information from the Python docstrings

  Scenario: Ingest documentation from HTML files
    Given I have HTML documentation files in a directory
    When I ingest the HTML documentation
    Then the documentation should be processed and stored in the memory system
    And I should be able to query information from the HTML documentation

  Scenario: Ingest documentation from RST files
    Given I have RST documentation files in a directory
    When I ingest the RST documentation
    Then the documentation should be processed and stored in the memory system
    And I should be able to query information from the RST documentation

  Scenario: Ingest documentation from a URL
    Given I have a URL pointing to documentation
    When I ingest the documentation from the URL
    Then the documentation should be processed and stored in the memory system
    And I should be able to query information from the URL documentation

  Scenario: Ingest documentation from multiple sources
    Given I have documentation in multiple formats:
      | format   | source_type |
      | Markdown | directory   |
      | JSON     | directory   |
      | Python   | directory   |
      | HTML     | URL         |
    When I ingest documentation from all sources
    Then all documentation should be processed and stored in the memory system
    And I should be able to query information across all documentation sources

  Scenario: Integration with memory system
    When I ingest documentation from multiple formats
    Then the documentation should be stored in appropriate memory stores:
      | content_type | memory_store_type |
      | text         | vector            |
      | metadata     | structured        |
      | relationships| graph             |
    And I should be able to retrieve documentation using different query methods
