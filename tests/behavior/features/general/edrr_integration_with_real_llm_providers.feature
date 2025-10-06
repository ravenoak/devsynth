Feature: Provider failover for EDRR integration
  As an integration engineer
  I want offline safeguards to prefer deterministic providers
  So that EDRR runs avoid accidental network usage when credentials are missing

  Background:
    Given providers are configured with default fallbacks

  Scenario: Offline runs fall back to the stub provider
    Given DEVSYNTH_OFFLINE is enabled without OPENAI credentials
    When the provider factory resolves the "openai" provider
    Then the stub provider is returned with retry settings intact
