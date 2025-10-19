Feature: WebUI Ingestion Page
  As a developer
  I want to ingest external data and code into my project in the WebUI
  So that I can incorporate external resources into my development process

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Ingestion page
    When I navigate to "Ingestion"
    Then the ingestion page should be displayed

  Scenario: Ingest code from repository
    When I navigate to "Ingestion"
    And I enter a repository URL
    And I submit the ingestion form
    Then the repository code should be ingested
    And a success message should be displayed

  Scenario: Ingest code from local directory
    When I navigate to "Ingestion"
    And I select a local directory for ingestion
    And I submit the ingestion form
    Then the local code should be ingested
    And a success message should be displayed

  Scenario: Ingest data from file
    When I navigate to "Ingestion"
    And I select a data file for ingestion
    And I submit the ingestion form
    Then the data should be ingested
    And a success message should be displayed

  Scenario: Ingest data with custom parser
    When I navigate to "Ingestion"
    And I select a data file for ingestion
    And I select a custom parser
    And I submit the ingestion form
    Then the data should be ingested with the custom parser
    And a success message should be displayed

  Scenario: View ingestion history
    When I navigate to "Ingestion"
    And I click the ingestion history button
    Then the ingestion history should be displayed
    And previous ingestion results should be available for review

  Scenario: Configure ingestion settings
    When I navigate to "Ingestion"
    And I click the ingestion settings button
    And I update the ingestion settings
    And I save the settings
    Then the ingestion settings should be updated
    And a success message should be displayed
