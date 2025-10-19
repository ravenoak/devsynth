Feature: Database Schema Generation
  As a developer using DevSynth
  I want to generate database schemas
  So that I can quickly create database models for my projects

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @dbschema-generation
  Scenario: Generate a SQLite database schema with default parameters
    When I run the command "devsynth dbschema"
    Then the system should generate a SQLite database schema
    And the schema should be created in the current directory
    And the schema should be named "database"
    And the output should indicate that the schema was generated
    And the workflow should execute successfully

  @dbschema-generation
  Scenario: Generate a database schema with custom database type
    When I run the command "devsynth dbschema --db-type postgresql"
    Then the system should generate a PostgreSQL database schema
    And the schema should be created in the current directory
    And the schema should be named "database"
    And the output should indicate that the schema was generated
    And the workflow should execute successfully

  @dbschema-generation
  Scenario: Generate a database schema with custom name
    When I run the command "devsynth dbschema --name mydb"
    Then the system should generate a SQLite database schema
    And the schema should be created in the current directory
    And the schema should be named "mydb"
    And the output should indicate that the schema was generated
    And the workflow should execute successfully

  @dbschema-generation
  Scenario: Generate a database schema in a custom location
    When I run the command "devsynth dbschema --path ./db"
    Then the system should generate a SQLite database schema
    And the schema should be created in the "./db" directory
    And the schema should be named "database"
    And the output should indicate that the schema was generated
    And the workflow should execute successfully

  @dbschema-generation
  Scenario: Generate a database schema with all custom parameters
    When I run the command "devsynth dbschema --db-type mysql --name myproject --path ./db"
    Then the system should generate a MySQL database schema
    And the schema should be created in the "./db" directory
    And the schema should be named "myproject"
    And the output should indicate that the schema was generated
    And the workflow should execute successfully

  @dbschema-generation
  Scenario: Handle unsupported database type
    When I run the command "devsynth dbschema --db-type unsupported"
    Then the system should display an error message
    And the error message should indicate that the database type is not supported
    And the workflow should not execute successfully
