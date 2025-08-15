Feature: Dialectical reasoning persists results to memory
  As a requirements engineer
  I want dialectical reasoning results stored in memory
  So that they can be reviewed later

  @fast
  Scenario: Successful evaluation stores reasoning
    Given a dialectical reasoner with memory
    And a requirement change
    When the change is evaluated
    Then the reasoning result should be stored in memory with phase "REFINE"

  @fast
  Scenario: Invalid consensus response stores reasoning for retrospection
    Given a dialectical reasoner with memory
    And a requirement change
    When the change is evaluated with invalid consensus output
    Then the reasoning result should be stored in memory with phase "RETROSPECT"
    And a consensus error is raised
