Feature: EDRR cycle command
  As a developer
  I want to run the edrr-cycle command with a manifest file
  So that DevSynth executes an EDRR cycle based on that manifest

  Scenario: Run EDRR cycle with manifest file
    Given a valid manifest file
    When I execute the edrr cycle command with that file
    Then the coordinator should process the manifest
    And the workflow should complete successfully

  Scenario: Handle missing manifest file
    Given no manifest file exists at the provided path
    When I execute the edrr cycle command with that file
    Then the system should report that the manifest file was not found
