Feature: Requirements Management
  As a developer using DevSynth
  I want to manage requirements with dialectical reasoning
  So that I can ensure my project meets stakeholder needs

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @requirements-management
  Scenario: List all requirements
    When I run the command "devsynth requirements --action list"
    Then the system should display all requirements
    And the output should include requirement IDs, titles, and statuses
    And the workflow should execute successfully

  @requirements-management
  Scenario: Show a specific requirement
    When I run the command "devsynth requirements --action show --id REQ-001"
    Then the system should display the details of requirement "REQ-001"
    And the output should include the requirement's title, description, status, and priority
    And the workflow should execute successfully

  @requirements-management
  Scenario: Create a new requirement
    When I run the command "devsynth requirements --action create --title 'New Feature' --description 'This is a new feature' --status 'Proposed' --priority 'Medium' --type 'Functional'"
    Then the system should create a new requirement
    And the output should indicate that the requirement was created
    And the output should include the new requirement's ID
    And the workflow should execute successfully

  @requirements-management
  Scenario: Update an existing requirement
    When I run the command "devsynth requirements --action update --id REQ-001 --title 'Updated Feature' --status 'Approved'"
    Then the system should update requirement "REQ-001"
    And the output should indicate that the requirement was updated
    And the workflow should execute successfully

  @requirements-management
  Scenario: Delete a requirement
    When I run the command "devsynth requirements --action delete --id REQ-001 --reason 'No longer needed'"
    Then the system should delete requirement "REQ-001"
    And the output should indicate that the requirement was deleted
    And the workflow should execute successfully

  @requirements-management
  Scenario: List requirement changes
    When I run the command "devsynth requirements --action changes"
    Then the system should display all requirement changes
    And the output should include change IDs, affected requirements, and change types
    And the workflow should execute successfully

  @requirements-management
  Scenario: Approve a requirement change
    When I run the command "devsynth requirements --action approve-change --id CHG-001 --comment 'Looks good'"
    Then the system should approve change "CHG-001"
    And the output should indicate that the change was approved
    And the workflow should execute successfully

  @requirements-management
  Scenario: Reject a requirement change
    When I run the command "devsynth requirements --action reject-change --id CHG-001 --reason 'Not aligned with project goals'"
    Then the system should reject change "CHG-001"
    And the output should indicate that the change was rejected
    And the workflow should execute successfully

  @requirements-management
  Scenario: Start a chat session about requirements
    When I run the command "devsynth requirements --action chat"
    Then the system should start a chat session
    And the output should indicate that the chat session has started
    And the workflow should execute successfully

  @requirements-management
  Scenario: Continue an existing chat session
    When I run the command "devsynth requirements --action continue-chat --id CHAT-001"
    Then the system should continue chat session "CHAT-001"
    And the output should display the chat history
    And the workflow should execute successfully

  @requirements-management
  Scenario: Evaluate the impact of a requirement change
    When I run the command "devsynth requirements --action evaluate-change --id CHG-001"
    Then the system should evaluate the impact of change "CHG-001"
    And the output should include affected components and estimated effort
    And the workflow should execute successfully

  @requirements-management
  Scenario: Assess the impact of a new requirement
    When I run the command "devsynth requirements --action assess-impact --id REQ-001"
    Then the system should assess the impact of requirement "REQ-001"
    And the output should include affected components and estimated effort
    And the workflow should execute successfully

  @requirements-management
  Scenario: Handle non-existent requirement
    When I run the command "devsynth requirements --action show --id NON-EXISTENT"
    Then the system should display an error message
    And the error message should indicate that the requirement was not found
    And the workflow should not execute successfully

  @requirements-management
  Scenario: Handle missing required parameters
    When I run the command "devsynth requirements --action create --title 'New Feature'"
    Then the system should display an error message
    And the error message should indicate that required parameters are missing
    And the workflow should not execute successfully
