
Feature: Code Generation
  As a developer
  I want DevSynth to generate code based on requirements and tests
  So that I can implement my software faster

  Scenario: Generate code from requirements and tests
    Given I have a DevSynth project with analyzed requirements
    And I have generated tests
    When I run the command "devsynth generate code"
    Then the system should generate code that implements the requirements
    And the generated code should pass the generated tests
    And the code should follow best practices and coding standards

  Scenario: Iterative code refinement
    Given I have a DevSynth project with generated code
    When I run the command "devsynth refine code --feedback 'Improve error handling'"
    Then the system should analyze the existing code
    And update the code to improve error handling
    And ensure all tests still pass
