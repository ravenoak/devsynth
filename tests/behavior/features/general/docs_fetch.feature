Feature: Documentation Fetch and Cache
  As a developer
  I want to fetch and cache library documentation
  So that I can reference it during development

  Background:
    Given a documentation provider configured for "example-lib" version "1.0.0"

  Scenario: Successful fetch and cache
    When I fetch documentation for "example-lib" version "1.0.0"
    Then the documentation should be stored in the local cache
    And I should be able to retrieve a summary via the CLI

  Scenario: Cache miss triggers fresh fetch
    Given the cache for "example-lib" version "2.0.0" is empty
    When I fetch documentation for "example-lib" version "2.0.0"
    Then the system should retrieve the docs from the external provider
    And store them in the cache

  Scenario: Invalid library request
    When I fetch documentation for "nonexistent-lib" version "0.0.1"
    Then I should receive an error message indicating the docs were not found
