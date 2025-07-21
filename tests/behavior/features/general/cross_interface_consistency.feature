Feature: Cross-Interface Consistency
  As a developer
  I want all interfaces (CLI, WebUI, and Agent API) to behave consistently
  So that users have a uniform experience regardless of interface

  Background:
    Given the CLI, WebUI, and Agent API are initialized

  Scenario Outline: Commands produce identical results across interfaces
    When I invoke the <command> command with identical parameters via CLI
    And I invoke the <command> command with identical parameters via WebUI
    And I invoke the <command> command with identical parameters via Agent API
    Then all interfaces should produce identical results
    And all interfaces should use the same UXBridge methods
    And all interfaces should handle progress indicators consistently

    Examples:
      | command     |
      | init        |
      | spec        |
      | test        |
      | code        |
      | doctor      |
      | edrr-cycle  |

  Scenario Outline: Error handling is consistent across interfaces
    When I invoke the <command> command with invalid parameters via CLI
    And I invoke the <command> command with invalid parameters via WebUI
    And I invoke the <command> command with invalid parameters via Agent API
    Then all interfaces should report the same error
    And all interfaces should handle the error gracefully

    Examples:
      | command     |
      | init        |
      | spec        |
      | test        |
      | code        |
      | doctor      |
      | edrr-cycle  |

  Scenario: User interaction is consistent across interfaces
    When I need to ask a question via CLI
    And I need to ask the same question via WebUI
    And I need to ask the same question via Agent API
    Then all interfaces should present the question consistently
    And all interfaces should handle the response consistently

  Scenario: Progress reporting is consistent across interfaces
    When I perform a long-running operation via CLI
    And I perform the same long-running operation via WebUI
    And I perform the same long-running operation via Agent API
    Then all interfaces should report progress consistently
    And all interfaces should indicate completion consistently