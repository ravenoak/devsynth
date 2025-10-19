Feature: Methodology Adapters Integration
  As a developer using DevSynth
  I want to use different methodology adapters
  So that I can integrate the EDRR process with my preferred development methodology

  Background:
    Given the DevSynth system is initialized
    And the methodology configuration is loaded from manifest.yaml

  Scenario: Configure Sprint Methodology Adapter
    When I set the methodology type to "sprint" in the configuration
    And I configure the sprint duration to 2 weeks
    And I configure the ceremony mappings:
      | ceremony       | edrr_phase                  |
      | planning       | retrospect.iteration_planning |
      | dailyStandup   | phase_progression_tracking  |
      | review         | refine.outputs_review       |
      | retrospective  | retrospect.process_evaluation |
    Then the methodology adapter should be of type "SprintAdapter"
    And the sprint duration should be 2 weeks
    And the ceremony mappings should be correctly configured

  Scenario: Configure Ad-Hoc Methodology Adapter
    When I set the methodology type to "adhoc" in the configuration
    And I configure the phase settings:
      | phase         | skipable |
      | expand        | false    |
      | differentiate | true     |
      | refine        | false    |
      | retrospect    | false    |
    Then the methodology adapter should be of type "AdHocAdapter"
    And the phase settings should be correctly configured

  Scenario: Sprint Adapter Phase Progression
    Given the methodology type is set to "sprint"
    And the current phase is "expand"
    And all required activities for the phase are completed
    And the phase time allocation is not exceeded
    When the system checks if it should progress to the next phase
    Then the result should be true
    And the next phase should be "differentiate"

  Scenario: Ad-Hoc Adapter Phase Progression
    Given the methodology type is set to "adhoc"
    And the current phase is "expand"
    And the user has explicitly requested to progress to the next phase
    When the system checks if it should progress to the next phase
    Then the result should be true
    And the next phase should be "differentiate"

  Scenario: Sprint Adapter Generates Reports
    Given the methodology type is set to "sprint"
    And a complete EDRR cycle has been executed
    When the system generates reports for the cycle
    Then a sprint review report should be generated
    And a sprint retrospective report should be generated
    And the reports should contain the cycle results

  Scenario: Ad-Hoc Adapter Generates Reports
    Given the methodology type is set to "adhoc"
    And a complete EDRR cycle has been executed
    When the system generates reports for the cycle
    Then a summary report should be generated
    And the report should contain the cycle results
