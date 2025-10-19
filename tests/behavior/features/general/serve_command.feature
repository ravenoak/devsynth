Feature: Serve Command
  As a developer
  I want to run the DevSynth API server using the CLI
  So that I can provide API access to DevSynth functionality

  Background:
    Given the DevSynth CLI is installed
    And no other service is running on port 8080

  Scenario: Start the API server with default settings
    When I run the command "devsynth serve"
    Then the command should execute successfully
    And the API server should start on the default port
    And the system should display a message indicating the server is running

  Scenario: Start the API server with a custom port
    When I run the command "devsynth serve --port 9090"
    Then the command should execute successfully
    And the API server should start on port 9090
    And the system should display a message indicating the server is running on port 9090

  Scenario: Start the API server with verbose logging
    When I run the command "devsynth serve --verbose"
    Then the command should execute successfully
    And the API server should start with verbose logging enabled
    And the system should display detailed log messages

  Scenario: Attempt to start the API server on a port that's already in use
    Given a service is already running on port 8080
    When I run the command "devsynth serve --port 8080"
    Then the command should fail
    And the system should display an error message about the port being in use
