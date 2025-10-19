Feature: Environment Variables Integration
  As a developer
  I want DevSynth to load environment variables from a .env file
  So that I can securely configure the application with sensitive information

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Load OpenAI API key from .env file
    Given I have a .env file with the following content:
      """
      OPENAI_API_KEY=sk-test-key-12345
      """
    When I run the command "devsynth config --key openai_api_key"
    Then the system should display the value "sk-test-key-12345" for "openai_api_key"
    And the workflow should execute successfully

  Scenario: Load Serper API key from .env file
    Given I have a .env file with the following content:
      """
      SERPER_API_KEY=serper-test-key-67890
      """
    When I run the command "devsynth config --key serper_api_key"
    Then the system should display the value "serper-test-key-67890" for "serper_api_key"
    And the workflow should execute successfully

  Scenario: Override environment variables with command line configuration
    Given I have a .env file with the following content:
      """
      DEVSYNTH_LLM_MODEL=gpt-3.5-turbo
      """
    When I run the command "devsynth config --key llm_model --value gpt-4"
    Then the system should update the configuration
    And set "llm_model" to "gpt-4"
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Load multiple environment variables from .env file
    Given I have a .env file with the following content:
      """
      OPENAI_API_KEY=sk-test-key-12345
      SERPER_API_KEY=serper-test-key-67890
      DEVSYNTH_LLM_MODEL=gpt-3.5-turbo
      DEVSYNTH_LLM_TEMPERATURE=0.8
      """
    When I run the command "devsynth config"
    Then the system should display the value "sk-test-key-12345" for "openai_api_key"
    And the system should display the value "serper-test-key-67890" for "serper_api_key"
    And the system should display the value "gpt-3.5-turbo" for "llm_model"
    And the system should display the value "0.8" for "llm_temperature"
    And the workflow should execute successfully
