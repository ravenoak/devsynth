Feature: Shared UXBridge across CLI and WebUI
  As a developer
  I want the CLI and WebUI to use the same UXBridge interface
  So that workflow arguments remain consistent

  Scenario: Init command executed through shared bridge
    Given the CLI and WebUI share a UXBridge
    When init is invoked from the CLI and WebUI
    Then both invocations pass identical arguments
