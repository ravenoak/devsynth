Feature: WebUI DBSchema Page
  As a developer
  I want to manage database schemas in the WebUI
  So that I can design, visualize, and generate database structures

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to DBSchema page
    When I navigate to "DBSchema"
    Then the DBSchema page should be displayed

  Scenario: Create a new database schema
    When I navigate to "DBSchema"
    And I click the create new schema button
    And I enter schema details
    And I save the schema
    Then the database schema should be created
    And a success message should be displayed

  Scenario: Import database schema from file
    When I navigate to "DBSchema"
    And I click the import schema button
    And I select a schema file to import
    And I confirm the import
    Then the database schema should be imported
    And a success message should be displayed

  Scenario: Edit existing database schema
    When I navigate to "DBSchema"
    And I select an existing schema
    And I make changes to the schema
    And I save the schema
    Then the database schema should be updated
    And a success message should be displayed

  Scenario: Generate SQL from schema
    When I navigate to "DBSchema"
    And I select an existing schema
    And I click the generate SQL button
    Then the SQL code should be generated
    And the SQL code should be displayed

  Scenario: Export schema to different formats
    When I navigate to "DBSchema"
    And I select an existing schema
    And I click the export button
    And I select an export format
    Then the schema should be exported in the selected format

  Scenario: Visualize database schema
    When I navigate to "DBSchema"
    And I select an existing schema
    And I click the visualize button
    Then the schema visualization should be displayed
    And the visualization should accurately represent the schema

  Scenario: Validate database schema
    When I navigate to "DBSchema"
    And I select an existing schema
    And I click the validate button
    Then the schema validation results should be displayed
