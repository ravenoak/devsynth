Feature: Validate Metadata Command
  As a documentation maintainer
  I want to validate metadata in Markdown files
  So that the documentation meets standards

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Validate metadata successfully
    Given a documentation file with valid metadata
    When I run the command "devsynth validate-metadata --directory docs"
    Then the output should indicate the metadata is valid

  Scenario: Handle missing documentation directory
    When I run the command "devsynth validate-metadata --directory ./missing-dir"
    Then the system should display an error message
