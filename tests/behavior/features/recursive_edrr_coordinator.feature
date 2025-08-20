Feature: Recursive EDRR Coordinator
  As a system maintainer
  I want recursion to terminate predictably
  So that micro cycles do not run indefinitely

  Background:
    Given a configured EDRR coordinator

  Scenario: Recursion stops at maximum depth
    Given a task requiring nested analysis
    When the coordinator reaches its maximum recursion depth
    Then no further micro cycles are spawned

  Scenario: Termination criteria halt recursion early
    Given a task whose complexity exceeds configured thresholds
    When the coordinator evaluates recursion termination
    Then recursion ends due to complexity limits

  Scenario Outline: Resource constraints force recursion termination
    Given a task with <factor> beyond safe limits
    When the coordinator evaluates recursion termination
    Then recursion ends because of <factor>

    Examples:
      | factor       |
      | memory usage |
      | time limit   |
