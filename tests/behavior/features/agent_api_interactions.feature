Feature: Agent API Interactions
  As a developer
  I want to drive workflows through the Agent API
  So that automation can use DevSynth remotely

  Scenario: Invoke workflows via HTTP endpoints
    Given the Agent API server is running
    When I POST to /init
    And I POST to /gather
    And I POST to /synthesize
    And I GET /status
    Then the CLI init command should be called
    And the CLI gather command should be called
    And the CLI run_pipeline command should be called
    And the status message should be "run:unit"
