@fast @uxbridge @parity
Feature: Shared UXBridge across CLI, Textual TUI, and WebUI
  As a DevSynth maintainer
  I want consistent workflows across presentation layers
  So that testing and documentation remain accurate regardless of UI shell

  Background:
    Given the UXBridge protocol defines capability negotiation for history, multi-select, and layout panels

  Scenario: Workflow orchestration is agnostic to the active bridge
    Given the setup wizard workflow is executed through the CLI bridge
    When the workflow is re-executed through the Textual bridge
    Then both runs emit the same sequence of orchestration calls
    And the persisted configuration artefacts are equivalent

  Scenario: Accessibility themes are respected across bridges
    Given a high-contrast theme is configured for DevSynth
    When the operator switches between CLI, Textual, and WebUI presentations
    Then the rendered prompts and panes honour the configured theme without additional setup
    And screenshots captured during documentation match the expected colour palette

  Scenario: Logging output remains consistent
    Given workflows emit sanitised progress events through the UXBridge
    When the CLI, Textual, and WebUI bridges record wizard interactions
    Then the resulting logs contain equivalent structured entries for prompts, navigation events, and summaries
