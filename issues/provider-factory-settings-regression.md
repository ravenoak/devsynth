---
Title: ProviderFactory missing-settings regression
Date: 2025-10-22 06:01 UTC
Status: closed
Affected Area: tests
Reproduction:
  - `poetry run pytest tests/unit/adapters/test_provider_system.py::test_provider_factory_injected_config_survives_missing_settings -q`
Exit Code: 0 (pre-fix run raised ImportError due to missing get_settings)
Artifacts:
  - diagnostics/provider_system_regression.log
Suspected Cause: ProviderFactory assumed devsynth.config.settings always exported get_settings, so partial reloads (or monkeypatching in tests) raised ImportError before TLS defaults were constructed.
Next Actions:
  - [x] Add regression coverage that deletes the settings.get_settings attribute before ProviderFactory.create_provider runs.
  - [x] Harden provider_system._load_settings_module and ProviderFactory to tolerate missing exports when explicit config is supplied.
  - [x] Rebind devsynth.config.settings.get_settings during module initialisation to avoid attr gaps during reloads.
Resolution Evidence:
  - diagnostics/provider_system_regression.log
---
