Feature: WebUI Analysis Page
  As a DevSynth user
  I want to use the WebUI analysis page
  So that I can analyze my project's code

  Background:
    Given the WebUI is initialized
    And I have a valid project directory

  Scenario: Access the analysis page
    When I navigate to the "Analysis" page
    Then I should see the analysis page title
    And I should see the code analysis form

  Scenario: Run code analysis with default settings
    Given I am on the analysis page
    When I submit the analysis form with default settings
    Then the code analysis should be executed
    And I should see the analysis results

  Scenario: Run code analysis with custom settings
    Given I am on the analysis page
    When I enter a custom path for analysis
    And I select specific analysis options
    And I submit the analysis form
    Then the code analysis should be executed with custom settings
    And I should see the analysis results

  Scenario: Handle errors during code analysis
    Given I am on the analysis page
    When I enter an invalid path for analysis
    And I submit the analysis form
    Then I should see an appropriate error message
    And I should be able to correct the input and resubmit

  Scenario: Navigate between analysis and other pages
    Given I am on the analysis page
    When I navigate to the "Synthesis" page
    And I navigate back to the "Analysis" page
    Then I should see the analysis page with preserved state
