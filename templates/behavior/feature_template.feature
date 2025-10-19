Feature: Feature Name
  As a [role]
  I want [feature]
  So that [benefit]

  # Background section is optional but useful for common setup steps
  Background:
    Given the system is in a known state
    And any other preconditions

  # Scenario: Simple scenario with basic steps
  Scenario: Basic scenario name describing the behavior
    Given some initial context
    When an action is performed
    Then a particular outcome should be observed

  # Scenario Outline: For testing multiple variations with examples
  Scenario Outline: Parameterized scenario name
    Given a user with name "<name>"
    When they perform action with parameter "<parameter>"
    Then they should see result "<result>"

    Examples:
      | name  | parameter | result  |
      | Alice | value1    | success |
      | Bob   | value2    | failure |
      | Carol | value3    | success |

  # Scenario with data tables
  Scenario: Scenario with data table
    Given the following users exist:
      | name  | role     | active |
      | Alice | admin    | true   |
      | Bob   | user     | true   |
      | Carol | reviewer | false  |
    When Alice reviews Bob's submission
    Then the submission status should be "reviewed"

  # Scenario with multi-line text
  Scenario: Scenario with multi-line text
    Given a document with the following content:
      """
      This is a multi-line
      document that can be used
      for testing text processing
      features.
      """
    When the document is processed
    Then the word count should be 15
