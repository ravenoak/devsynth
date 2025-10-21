@fast @cli @ux
Feature: CLI UX Enhancements
  As a DevSynth operator guiding initial configuration
  I want enriched CLI interactions
  So that I can complete wizards quickly without losing context

  Background:
    Given the CLI routes interactions through the UXBridge abstraction

  @prompt_toolkit
  Scenario: Prompt-toolkit session provides history and completions
    Given prompt-toolkit is available in the execution environment
    And the operator starts the DevSynth setup wizard from the CLI
    When the operator navigates between questions using keyboard shortcuts
    Then the prompt session exposes command history navigation without manual editing
    And the prompt session offers tab-completion for available options
    And previously entered answers remain intact after moving backwards

  @rich
  Scenario: Rich fallback engages when prompt-toolkit is unavailable
    Given prompt-toolkit is not installed
    When the operator launches the requirements wizard from the CLI
    Then the CLI falls back to Rich-based prompts without raising errors
    And the wizard still offers on-screen guidance for available commands
    And navigation defaults to explicit commands while preserving sanitised output

  @textual
  Scenario: Textual TUI surfaces multi-pane wizard layout
    Given the operator invokes "poetry run devsynth tui"
    When the Textual application loads the requirements wizard workflow
    Then the interface shows separate panes for inputs, live summary, and contextual help
    And the operator can move backward or forward using keyboard navigation without typing sentinel commands
    And the resulting configuration artefact matches the CLI baseline output
