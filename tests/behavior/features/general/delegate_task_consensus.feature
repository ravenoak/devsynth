Feature: Delegating tasks with consensus voting
  As a coordinator
  I want teams to vote on task solutions
  So that the final result reflects majority consensus

  Scenario: Reach consensus via voting
    Given a coordinator with agents capable of voting
    When I delegate a voting-based task
    Then each agent should cast a vote
    And the outcome should be approved by consensus vote

  Scenario: No agents able to propose a solution
    Given a coordinator with agents unable to propose solutions
    When I delegate a voting-based task
    Then the system should return an error message indicating no solutions were proposed

  Scenario: Dialectical reasoning module raises an exception
    Given a coordinator with agents capable of voting
    And the dialectical reasoning module raises an exception
    When I delegate a voting-based task
    Then the system should return a graceful dialectical reasoning error message
