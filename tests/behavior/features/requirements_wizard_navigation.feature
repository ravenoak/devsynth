@fast @requirements @ux
Feature: Requirements Wizard Navigation
  As a DevSynth operator refining requirements
  I want adaptive navigation controls
  So that I can revisit and validate entries without repeating the wizard

  Background:
    Given the requirements wizard is exposed through the UXBridge abstraction

  Scenario: Keyboard shortcuts move backward without losing data
    Given the operator is entering requirement details in the CLI
    When the operator presses the configured back shortcut
    Then the wizard returns to the previous step
    And the previously provided answers remain editable

  Scenario: Live summary updates while navigating in Textual
    Given the operator is using the Textual TUI for the requirements wizard
    When the operator advances to the acceptance criteria step
    Then the summary pane reflects the collected metadata and actors
    And the operator can open the review pane without leaving the current step

  Scenario: Multi-select prompts replace repeated yes-no confirmations
    Given prompt-toolkit capabilities are available
    When the operator selects optional integrations for the project
    Then the wizard presents a multi-select list with inline descriptions
    And the resulting configuration captures all chosen integrations in a single confirmation step
