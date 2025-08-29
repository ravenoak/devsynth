#!/usr/bin/env bash
set -euo pipefail

# Validate offline defaults for CI fast lane
# Ensures deterministic, non-networked test defaults

fail=0

check_var() {
  local name="$1" expected="$2"
  local val="${!name:-}"
  if [[ "$val" != "$expected" ]]; then
    echo "ERROR: $name expected '$expected' but was '${val:-<unset>}'"
    fail=1
  else
    echo "OK: $name='$val'"
  fi
}

# Required defaults
check_var DEVSYNTH_PROVIDER "stub"
check_var DEVSYNTH_OFFLINE "true"

# Resource flags should be false by default
for res in CHROMADB DUCKDB FAISS KUZU LMDB RDFLIB TINYDB LMSTUDIO; do
  name="DEVSYNTH_RESOURCE_${res}_AVAILABLE"
  val="${!name:-}"
  if [[ "$val" != "false" ]]; then
    echo "WARN: $name is '${val:-<unset>}' (expected 'false' by default). Proceeding."
  else
    echo "OK: $name='false'"
  fi
done

# Stub key presence check (non-secret)
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "WARN: OPENAI_API_KEY is unset (fine for offline), tests should not rely on it."
else
  echo "OK: OPENAI_API_KEY present (stub)"
fi

if [[ $fail -ne 0 ]]; then
  echo "Offline defaults check FAILED"
  exit 1
fi

echo "Offline defaults check PASSED"
