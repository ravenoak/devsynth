# Related issue: ../../docs/specifications/config_loader_spec.md
Feature: Configuration Loader Specification
  Scenario: Load, save, and autocomplete configuration
    Given an empty project directory
    When I load the configuration
    Then the default configuration is returned
    When I save the configuration as project YAML
    Then a project configuration file is created
    When I autocomplete the config key with prefix "pro"
    Then "project_root" should be suggested
