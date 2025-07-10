Feature: Configuration Loader
  As a developer
  I want the loader to detect project configuration
  So that CLI commands use consistent settings

  Scenario: Detect project.yaml configuration
    Given a project with a project.yaml file
    When the configuration loader runs
    Then the configuration should have the key "language" set to "python"

  Scenario: Detect pyproject.toml configuration
    Given a project with a pyproject.toml containing a [tool.devsynth] section
    When the configuration loader runs
    Then the configuration should have the key "language" set to "python"

  Scenario: Create configuration file
    Given an empty project directory
    When I save a default configuration
    Then a project.yaml file should be created
