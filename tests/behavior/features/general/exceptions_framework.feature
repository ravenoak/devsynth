Feature: Exceptions Framework
  As a developer
  I want a unified exception base class
  So that error handling is consistent

  Scenario: Catch DevSynthError
    Given a component that raises a DevSynthError
    When I handle errors
    Then I can catch the base class
