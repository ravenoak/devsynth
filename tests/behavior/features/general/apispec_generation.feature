Feature: API Specification Generation
  As a developer using DevSynth
  I want to generate API specifications
  So that I can quickly create API documentation for my projects

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @apispec-generation
  Scenario: Generate a REST API specification with default parameters
    When I run the command "devsynth apispec"
    Then the system should generate a REST API specification
    And the specification should be in OpenAPI format
    And the specification should be created in the current directory
    And the specification should be named "api"
    And the output should indicate that the specification was generated
    And the workflow should execute successfully

  @apispec-generation
  Scenario: Generate an API specification with custom API type
    When I run the command "devsynth apispec --api-type graphql"
    Then the system should generate a GraphQL API specification
    And the specification should be in OpenAPI format
    And the specification should be created in the current directory
    And the specification should be named "api"
    And the output should indicate that the specification was generated
    And the workflow should execute successfully

  @apispec-generation
  Scenario: Generate an API specification with custom format
    When I run the command "devsynth apispec --format raml"
    Then the system should generate a REST API specification
    And the specification should be in RAML format
    And the specification should be created in the current directory
    And the specification should be named "api"
    And the output should indicate that the specification was generated
    And the workflow should execute successfully

  @apispec-generation
  Scenario: Generate an API specification with custom name
    When I run the command "devsynth apispec --name myapi"
    Then the system should generate a REST API specification
    And the specification should be in OpenAPI format
    And the specification should be created in the current directory
    And the specification should be named "myapi"
    And the output should indicate that the specification was generated
    And the workflow should execute successfully

  @apispec-generation
  Scenario: Generate an API specification in a custom location
    When I run the command "devsynth apispec --path ./api"
    Then the system should generate a REST API specification
    And the specification should be in OpenAPI format
    And the specification should be created in the "./api" directory
    And the specification should be named "api"
    And the output should indicate that the specification was generated
    And the workflow should execute successfully

  @apispec-generation
  Scenario: Generate an API specification with all custom parameters
    When I run the command "devsynth apispec --api-type grpc --format proto --name myservice --path ./services"
    Then the system should generate a gRPC API specification
    And the specification should be in Protocol Buffers format
    And the specification should be created in the "./services" directory
    And the specification should be named "myservice"
    And the output should indicate that the specification was generated
    And the workflow should execute successfully

  @apispec-generation
  Scenario: Handle unsupported API type
    When I run the command "devsynth apispec --api-type unsupported"
    Then the system should display an error message
    And the error message should indicate that the API type is not supported
    And the workflow should not execute successfully

  @apispec-generation
  Scenario: Handle unsupported format
    When I run the command "devsynth apispec --format unsupported"
    Then the system should display an error message
    And the error message should indicate that the format is not supported
    And the workflow should not execute successfully
