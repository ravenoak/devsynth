Feature: Agent API stub
  As an integration developer
  I want the stub to invoke CLI workflows
  So that programmatic clients mirror CLI behavior

  Scenario: Init endpoint triggers init command
    Given the Agent API stub is available
    When I call the init endpoint
    Then the init command should be executed through the bridge
