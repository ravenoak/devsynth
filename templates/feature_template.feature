Feature: [Feature Name]
  As a [role]
  I want to [capability]
  So that [benefit]

  Background:
    Given [common setup step 1]
    And [common setup step 2]

  Scenario: [Scenario 1 Name]
    Given [precondition 1]
    When [action 1]
    Then [expected outcome 1]
    And [expected outcome 2]

  Scenario: [Scenario 2 Name]
    Given [precondition 1]
    When [action 1]
    Then [expected outcome 1]

  Scenario Outline: [Parameterized Scenario Name]
    Given [precondition with <parameter>]
    When [action with <parameter>]
    Then [expected outcome with <parameter>]

    Examples:
      | parameter | other_value |
      | value1    | result1     |
      | value2    | result2     |
      | value3    | result3     |
