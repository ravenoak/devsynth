Feature: Delegating tasks with consensus voting
  As a coordinator
  I want teams to vote on task solutions
  So that the final result reflects majority consensus

  Scenario: Reach consensus via voting
    Given a coordinator with agents capable of voting
    When I delegate a voting-based task
    Then each agent should cast a vote
    And the outcome should be approved by consensus vote
