Feature: Agent API Interactions
  As a developer
  I want to drive workflows through the Agent API
  So that automation can use DevSynth remotely

  Scenario: Invoke core workflows via HTTP endpoints
    Given the Agent API server is running
    When I POST to /init
    And I POST to /gather
    And I POST to /synthesize
    And I GET /status
    Then the CLI init command should be called
    And the CLI gather command should be called
    And the CLI run_pipeline command should be called
    And the status message should be "run:unit"

  Scenario: Generate specifications via HTTP endpoint
    Given the Agent API server is running
    When I POST to /spec with requirements file "requirements.md"
    Then the CLI spec command should be called
    And the requirements file should be "requirements.md"

  Scenario: Generate tests via HTTP endpoint
    Given the Agent API server is running
    When I POST to /test with spec file "specs.md"
    Then the CLI test command should be called
    And the spec file should be "specs.md"

  Scenario: Generate code via HTTP endpoint
    Given the Agent API server is running
    When I POST to /code
    Then the CLI code command should be called

  Scenario: Run diagnostics via HTTP endpoint
    Given the Agent API server is running
    When I POST to /doctor with path "." and fix "false"
    Then the CLI doctor command should be called
    And the path should be "."
    And the fix parameter should be "false"

  Scenario: Run EDRR cycle via HTTP endpoint
    Given the Agent API server is running
    When I POST to /edrr-cycle with prompt "Improve this code"
    Then the CLI edrr_cycle command should be called
    And the prompt should be "Improve this code"
