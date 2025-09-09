#!/usr/bin/env bash
set -euo pipefail

# scripts/diagnostics.sh — quick diagnostics for test environment hangs/flakes
# Usage:
#   bash scripts/diagnostics.sh
#   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 bash scripts/diagnostics.sh  # simulate smoke mode

printf "DevSynth Diagnostics — %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Show key env vars (redacting secrets)
redact() { sed -E 's/(API_KEY|TOKEN|SECRET)=([^ ]+)/\1=***REDACTED***/g'; }

echo "\n[Environment snapshot]"
(
  env | sort | grep -E '^(DEVSYNTH_|PYTEST_|OPENAI_|LM_STUDIO_|CI=)' || true
) | redact

# Python and Poetry versions
echo "\n[Versions]"
command -v python >/dev/null 2>&1 && python --version || echo "python: not found"
command -v poetry >/dev/null 2>&1 && poetry --version || echo "poetry: not found"

# Pytest plugins list (respects smoke mode if PYTEST_DISABLE_PLUGIN_AUTOLOAD=1)
# When plugins are disabled, explicitly show that state and list builtins only.
echo "\n[Pytest plugins]"
if [[ "${PYTEST_DISABLE_PLUGIN_AUTOLOAD:-}" =~ ^(1|true|yes)$ ]]; then
  echo "Plugin autoload disabled (smoke mode). Listing built-in/explicit plugins only:"
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --trace-config -q 2>/dev/null | sed -n '1,120p' || true
else
  pytest --trace-config -q 2>/dev/null | sed -n '1,120p' || true
fi

# Show resolved test paths and quick inventory (non-fatal)
echo "\n[Test discovery snapshot]"
pytest --collect-only -q 2>/dev/null | sed -n '1,120p' || true

# Summarize effective CLI defaults for provider env
echo "\n[Provider defaults snapshot]"
python - <<'PY'
import os
from devsynth.config.provider_env import ProviderEnv
env = ProviderEnv.from_env().with_test_defaults()
print(env.as_dict())
PY

echo "\nDiagnostics complete."
