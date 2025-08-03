Feature: UXBridge Interface
  As a developer
  I want consistent interaction methods across all interfaces
  So that workflows behave the same in the CLI, WebUI and Agent API

  Scenario: CLI asks a question
    Given the CLI is running
    When a workflow asks "Proceed?"
    Then the user is prompted through the bridge

  Scenario: WebUI displays results
    Given the WebUI is running
    When a workflow completes an action
    Then the result is shown through the bridge

  Scenario: Agent API confirms a choice
    Given the Agent API is used
    When a workflow requires confirmation
    Then the choice is confirmed through the bridge

  Scenario: Dear PyGUI prompts the user
    Given Dear PyGUI is running
    When a workflow asks a question in Dear PyGUI
    Then the user is prompted through Dear PyGUI
