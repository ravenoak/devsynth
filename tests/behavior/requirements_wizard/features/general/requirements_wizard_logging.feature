Feature: Requirements Wizard Logging
  As a developer
  I want detailed logs for the requirements wizard
  So that interactions can be audited and debugged

  Scenario: Logs capture wizard steps
    Given the DevSynth CLI is installed
    When I run the requirements wizard with logging enabled
    Then log entries for each wizard step should be persisted
