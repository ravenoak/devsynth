Feature: WebUI Synthesis Page
  As a DevSynth user
  I want to use the WebUI synthesis page
  So that I can generate tests and code for my project

  Background:
    Given the WebUI is initialized
    And I have a valid project directory

  Scenario: Access the synthesis page
    When I navigate to the "Synthesis" page
    Then I should see the synthesis page title
    And I should see the synthesis options

  Scenario: Generate tests with default settings
    Given I am on the synthesis page
    When I click the "Generate Tests" button
    Then the test generation should be executed
    And I should see the test generation results

  Scenario: Generate code with default settings
    Given I am on the synthesis page
    When I click the "Generate Code" button
    Then the code generation should be executed
    And I should see the code generation results

  Scenario: Run full pipeline with default settings
    Given I am on the synthesis page
    When I click the "Run Pipeline" button
    Then the full pipeline should be executed
    And I should see the pipeline execution results

  Scenario: Generate tests with custom settings
    Given I am on the synthesis page
    When I expand the advanced options
    And I select specific test generation options
    And I click the "Generate Tests" button
    Then the test generation should be executed with custom settings
    And I should see the test generation results

  Scenario: Generate code with custom settings
    Given I am on the synthesis page
    When I expand the advanced options
    And I select specific code generation options
    And I click the "Generate Code" button
    Then the code generation should be executed with custom settings
    And I should see the code generation results

  Scenario: Handle errors during synthesis
    Given I am on the synthesis page
    When I click the "Generate Tests" button
    And an error occurs during test generation
    Then I should see an appropriate error message
    And I should be able to retry the operation

  Scenario: Navigate between synthesis and other pages
    Given I am on the synthesis page
    When I navigate to the "Analysis" page
    And I navigate back to the "Synthesis" page
    Then I should see the synthesis page with preserved state
