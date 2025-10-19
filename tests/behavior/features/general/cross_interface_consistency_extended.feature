Feature: Extended Cross-Interface Consistency
  As a developer
  I want all interfaces (CLI, WebUI, Agent API) to use the same UXBridge interface
  So that workflow arguments and behavior remain consistent across interfaces

  Scenario Outline: Commands executed through shared bridge
    Given the CLI, WebUI, and Agent API share a UXBridge
    When <command> is invoked from all interfaces
    Then all invocations pass identical arguments
    And the command behavior is consistent across interfaces

    Examples:
      | command |
      | init    |
      | spec    |
      | test    |
      | code    |
      | doctor  |
      | edrr_cycle |

  Scenario: Error handling is consistent across interfaces
    Given the CLI, WebUI, and Agent API share a UXBridge
    When an error occurs during command execution
    Then all interfaces handle the error consistently
    And appropriate error messages are displayed

  Scenario: User input handling is consistent across interfaces
    Given the CLI, WebUI, and Agent API share a UXBridge
    When user input is required during command execution
    Then all interfaces prompt for input consistently
    And the input is processed correctly
