Feature: Unified configuration loader behavior
  As a DevSynth maintainer
  I want the unified loader to choose the correct configuration source
  So that CLI workflows share consistent project settings

  Background:
    Given a temporary project root

  Scenario: Loader falls back to YAML when pyproject lacks DevSynth section
    Given a pyproject file without a DevSynth section
    And a YAML configuration with language "python"
    When I load the unified configuration
    Then the loader should report it uses YAML
    And the loaded language should be "python"

  Scenario: Malformed pyproject configuration surfaces a configuration error
    Given a malformed pyproject configuration
    When I attempt to load the unified configuration
    Then a configuration error should be reported for "pyproject.toml"
