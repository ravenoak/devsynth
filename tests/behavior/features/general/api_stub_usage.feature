Feature: Agent API Stub Usage
  As a developer
  I want to invoke workflows via the Agent API stub
  So that automation can leverage the same UXBridge logic

  Scenario: Initialize a project through the API stub
    Given the Agent API stub is available
    When I call the init endpoint
    Then the init command should be executed through the bridge
