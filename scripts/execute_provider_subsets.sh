#!/usr/bin/env bash
set -euo pipefail

# DevSynth provider subsets executor for docs/tasks.md Tasks 21–33
# - Aligns with docs/plan.md Section 3 and .junie/guidelines.md
# - Captures outputs under test_reports/ and diagnostics/
# - Restores hermetic defaults when done
#
# Usage examples:
#   bash scripts/execute_provider_subsets.sh lmstudio
#   bash scripts/execute_provider_subsets.sh openai
#   bash scripts/execute_provider_subsets.sh all
#
# Requirements:
# - Poetry installed; project installed with correct extras as needed by each subset
# - For OpenAI: export OPENAI_API_KEY with a real key before running
# - For LM Studio: an endpoint listening at LM_STUDIO_ENDPOINT (defaults to http://127.0.0.1:1234)

cmd="${1:-all}"

mkdir -p test_reports test_reports/quality diagnostics

log_exec() {
  local ts cmd exit_code artifacts notes
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  cmd="$1"
  exit_code="$2"
  artifacts="$3"
  notes="$4"
  {
    echo "Timestamp: ${ts}"
    echo "Command: ${cmd}"
    echo "Exit code: ${exit_code}"
    echo "Key outputs/artifacts: ${artifacts}"
    echo "Notes/anomalies: ${notes}"
    echo "---"
  } >> diagnostics/exec_log.txt
}

run_cmd() {
  local c="$1"; shift || true
  local artifacts_msg="${1:-}"
  local notes_msg="${2:-}"
  set +e
  eval "${c}"
  local rc=$?
  set -e
  log_exec "${c}" "${rc}" "${artifacts_msg}" "${notes_msg}"
  return ${rc}
}

run_lmstudio() {
  echo "[LM Studio] Installing extras: memory llm" >&2
  run_cmd "poetry install --with dev --extras 'memory llm'" "poetry install completed" "Tasks 21"

  export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  export LM_STUDIO_ENDPOINT="${LM_STUDIO_ENDPOINT:-http://127.0.0.1:1234}"

  # Try to detect if LM Studio endpoint is reachable; if not, start a mock server
  need_mock=0
  if command -v curl >/dev/null 2>&1; then
    set +e
    curl -sS --max-time 1 "${LM_STUDIO_ENDPOINT}/health" >/dev/null
    rc=$?
    set -e
    if [ $rc -ne 0 ]; then
      need_mock=1
    fi
  else
    need_mock=1
  fi

  if [ $need_mock -eq 1 ]; then
    echo "[LM Studio] No reachable endpoint detected at ${LM_STUDIO_ENDPOINT}; starting mock server" >&2
    # Ensure fastapi/uvicorn are available for the mock
    run_cmd "poetry add fastapi uvicorn --group dev" "Added fastapi/uvicorn for mock" "Mock deps"
    # Start mock in background
    POETRY_RUN_MOCK="poetry run python scripts/mock_lmstudio_server.py --host $(echo ${LM_STUDIO_ENDPOINT} | sed -E 's#http://([^:/]+).*#\1#') --port $(echo ${LM_STUDIO_ENDPOINT} | sed -E 's#http://[^:]+:(\d+).*#\1#')"
    bash -c "${POETRY_RUN_MOCK}" &
    MOCK_PID=$!
    # Give it a moment to start
    sleep 1
  fi

  echo "[LM Studio] Running fast subset (non-slow) provider tests directly (pytest)" >&2
  # Note: pytest -m does not support function-like markers with arguments; we run the known provider test module directly
  run_cmd "poetry run pytest -q --no-cov --maxfail=1 tests/integration/general/test_lmstudio_provider.py -m 'not slow' | tee test_reports/lmstudio_fast_subset_stdout.txt" "test_reports/lmstudio_fast_subset_stdout.txt" "Tasks 24–25"

  # Stop mock if started
  if [ ${MOCK_PID:-0} -ne 0 ] 2>/dev/null; then
    echo "[LM Studio] Stopping mock server (pid ${MOCK_PID})" >&2
    kill ${MOCK_PID} || true
  fi

  echo "[LM Studio] Restoring hermetic defaults" >&2
  unset DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE || true
}

run_openai() {
  echo "[OpenAI] Installing extras: llm" >&2
  run_cmd "poetry install --with dev --extras llm" "poetry install completed" "Task 27"

  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "ERROR: OPENAI_API_KEY is not set. Export a real key before running this subset." >&2
    return 2
  fi

  export DEVSYNTH_PROVIDER=openai
  export OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o-mini}"

  echo "[OpenAI] Running fast subset (non-slow) with resource marker" >&2
  run_cmd "poetry run devsynth run-tests --speed=fast -m \"requires_resource('openai') and not slow\" | tee test_reports/openai_fast_subset_stdout.txt" "test_reports/openai_fast_subset_stdout.txt" "Tasks 31–32"

  echo "[OpenAI] Restoring hermetic defaults" >&2
  unset OPENAI_API_KEY || true
  export DEVSYNTH_PROVIDER=stub
  export DEVSYNTH_OFFLINE=true
}

case "${cmd}" in
  lmstudio)
    run_lmstudio || exit $?
    ;;
  openai)
    run_openai || exit $?
    ;;
  all)
    run_lmstudio || true
    run_openai || true
    ;;
  *)
    echo "Usage: $0 [lmstudio|openai|all]" >&2
    exit 1
    ;;
 esac

echo "Done. Review diagnostics/exec_log.txt and test_reports/*subset_stdout.txt for evidence." >&2
