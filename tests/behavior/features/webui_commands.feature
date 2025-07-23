Feature: WebUI Command Execution
  As a developer
  I want to run DevSynth workflows from the WebUI
  So that I can manage my project graphically

  Background:
    Given the WebUI is initialized

  Scenario: Initialize a project through onboarding
    When I submit the onboarding form
    Then the init command should be executed

  Scenario: Generate specifications from the requirements page
    When I navigate to "Requirements"
    And I submit the specification form
    Then the spec command should be executed

  Scenario: Inspect requirements from the requirements page
    When I navigate to "Requirements"
    And I submit the inspect form
    Then the inspect command should be executed

  Scenario: Inspect code from the analysis page
    When I navigate to "Analysis"
    And I submit the analysis form
    Then the inspect_code command should be executed

  Scenario: Generate tests from the synthesis page
    When I navigate to "Synthesis"
    And I submit the test form
    Then the test command should be executed

  Scenario: Generate code from the synthesis page
    When I navigate to "Synthesis"
    And I click the generate code button
    Then the code command should be executed

  Scenario: Run the pipeline from the synthesis page
    When I navigate to "Synthesis"
    And I click the run pipeline button
    Then the run_pipeline command should be executed

  Scenario: Update configuration via the config page
    When I navigate to "Config"
    And I update a configuration value
    Then the config command should be executed

  Scenario: View all configuration via the config page
    When I navigate to "Config"
    And I view all configuration
    Then the config command should be executed

  Scenario: Run an EDRR cycle from the EDRR Cycle page
    When I navigate to "EDRR Cycle"
    And I submit the edrr cycle form
    Then the edrr_cycle command should be executed

  Scenario: Check alignment from the Alignment page
    When I navigate to "Alignment"
    And I submit the alignment form
    Then the align command should be executed
