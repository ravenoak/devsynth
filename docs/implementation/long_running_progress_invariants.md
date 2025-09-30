---
author: DevSynth Team
date: '2025-09-30'
last_reviewed: '2025-09-30'
status: published
tags:
- implementation
- invariants
title: Long-running Progress Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Long-running Progress Invariants
</div>

# Long-running Progress Invariants

This note captures the deterministic timelines shared by the CLI and WebUI progress indicators, focusing on adaptive refresh intervals, checkpoint/history cadence, and nested completion cascades that keep both surfaces in sync.

## CLI timeline invariants

### Deterministic scaffolding

The CLI indicator is exercised under a deterministic clock and a stubbed Rich ``Progress`` implementation so elapsed time, checkpoint timestamps, and subtask fan-out can be asserted precisely. The helper ``FakeClock`` advances monotonically and records every tick while ``FakeProgress`` mirrors Rich's task bookkeeping without side effects, allowing the tests to interrogate history and checkpoint fields directly.【F:tests/unit/application/cli/test_long_running_progress.py†L25-L113】 These shims drive the concrete ``LongRunningProgressIndicator`` implementation, which maintains sanitized task metadata, adaptive refresh intervals, and checkpoint lists on the underlying Rich task objects.【F:src/devsynth/application/cli/long_running_progress.py†L60-L195】

### Adaptive intervals and checkpoint cadence

With the deterministic scaffolding in place, ``test_update_adapts_interval_and_checkpoints`` proves that the indicator tightens its update cadence to 0.5 seconds at the beginning and end of a run, relaxes to a two-second cadence through the middle, and emits ETA checkpoints on ≥10% progress deltas with consistent timestamps and projections.【F:tests/unit/application/cli/test_long_running_progress.py†L120-L153】 The implementation's adaptive logic mirrors these expectations by toggling ``_update_interval`` based on fractional completion and persisting checkpoint dictionaries to the Rich task state.【F:src/devsynth/application/cli/long_running_progress.py†L146-L195】

### Status history and sanitized summaries

``test_status_history_tracks_unique_status_changes`` confirms that only new status strings are appended to the task history alongside the current completion percentage and deterministic timestamps, preventing duplicate entries when the status repeats.【F:tests/unit/application/cli/test_long_running_progress.py†L156-L171】 ``test_summary_reflects_fake_timeline_and_sanitizes_descriptions`` then validates that both the live task and the summary snapshot sanitize hostile descriptions, compute elapsed/remaining time from the fake clock, and echo the same checkpoint list gathered during updates.【F:tests/unit/application/cli/test_long_running_progress.py†L175-L199】 The summary helper surfaces these fields verbatim, ensuring operators can reconcile CLI telemetry with the Rich task metadata.【F:src/devsynth/application/cli/long_running_progress.py†L319-L360】 The deterministic harness ``simulate_progress_timeline`` exposes the same timeline through a declarative event list so the focused regression ``test_simulation_timeline_produces_deterministic_transcript`` can assert event ordering, checkpoint spacing, and sanitized subtask roll-ups without reimplementing Rich internals.【F:src/devsynth/application/cli/long_running_progress.py†L207-L320】【F:tests/unit/application/cli/test_long_running_progress.py†L402-L470】

### Behavioral telemetry audit

Regression coverage now drives the CLI indicator through the BDD narrative defined in `tests/behavior/features/long_running_progress.feature`, patching Rich's `Progress` class with a deterministic stub so checkpoints, history entries, and completion banners can be asserted end to end.【F:tests/behavior/features/long_running_progress.feature†L1-L8】【F:tests/behavior/test_progress_failover_and_recursion.py†L51-L94】 The behavior test mirrors production usage by invoking `LongRunningProgressIndicator.update`, `add_subtask`, and `complete` under a monotonic clock, then verifying that `get_summary` preserves the recorded history and checkpoint cadence alongside the Rich-facing state.【F:src/devsynth/application/cli/long_running_progress.py†L122-L359】 Focused fast runs capture reproducible artefacts under `issues/tmp_artifacts/long_running_progress/20250930T214900Z/` so reviewers can trace the deterministic simulation that exercises nested subtasks, ETA checkpoints, and completion banners.【F:issues/tmp_artifacts/long_running_progress/20250930T214900Z/notes.md†L1-L5】

## WebUI timeline invariants

### Streamlit stub and deterministic time slices

WebUI simulations reuse the deterministic pattern by injecting a purpose-built ``BehaviorStreamlitStub`` that records every rendered status, ETA, and subtask event while bypassing the real Streamlit runtime.【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L166-L296】 For focused progress tests, ``_init_progress_with_time`` reloads the module, wires a fake ``time.time`` sequence, and captures dedicated containers so ETA and status updates can be asserted without cross-test interference.【F:tests/unit/interface/test_webui_progress.py†L12-L72】 The new ``simulate_progress_rendering`` helper applies the same deterministic scaffolding to the rendering layer, calling ``ProjectSetupPages._render_progress_summary`` under a supplied clock so summaries, history bands, and sanitized error channels can be asserted without a real Streamlit runtime.【F:src/devsynth/interface/webui/rendering.py†L33-L112】【F:tests/unit/interface/test_webui_simulations_fast.py†L46-L95】 These harnesses drive the ``WebUI._UIProgress`` class, which mirrors the CLI behaviour by tracking update timestamps, rendering ETA bands, and falling back to sanitized placeholders when the clock is frozen.【F:src/devsynth/interface/webui.py†L386-L541】【F:tests/unit/interface/test_webui_simulations_fast.py†L97-L133】

### Status thresholds and ETA formatting

The focused progress tests sweep through the automatic status thresholds, demonstrating that the WebUI transitions from "Starting..." through "Finalizing..." and "Complete" as the deterministic increments cross the documented percentages, with the ETA container emitting seconds, minutes, or hour/minute bands depending on the simulated pace.【F:tests/unit/interface/test_webui_progress.py†L220-L308】 The broader behaviour checklist echoes the same thresholds under the Streamlit stub, verifying sanitized description updates and ETA formatting across long-running projections.【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L1022-L1076】

### Nested cascade order

Nested task lifecycles are validated end-to-end: the behaviour checklist proves that subtask markdown and success messages stay sanitized, that unknown subtasks are ignored without mutating history, and that completing the root task cascades completion to every registered subtask even when ``Streamlit.success`` is unavailable, falling back to ``write`` for the final announcement.【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L960-L1056】 The WebUI implementation implements this contract by sanitizing subtask descriptions, updating progress bars in place, and iterating through subtask IDs during ``complete`` to guarantee the cascade order matches the CLI timeline.【F:src/devsynth/interface/webui.py†L493-L541】

## Evidence

- CLI simulations: ``tests/unit/application/cli/test_long_running_progress.py::{test_update_adapts_interval_and_checkpoints,test_status_history_tracks_unique_status_changes,test_summary_reflects_fake_timeline_and_sanitizes_descriptions}``【F:tests/unit/application/cli/test_long_running_progress.py†L120-L199】
- WebUI simulations: ``tests/unit/interface/test_webui_progress.py::{test_ui_progress_eta_displays_seconds_when_under_minute,test_ui_progress_eta_displays_minutes_when_under_hour,test_ui_progress_eta_displays_hours_and_minutes,test_ui_progress_status_transitions_without_explicit_status,test_ui_progress_subtasks_update_with_frozen_time}`` and ``tests/unit/interface/test_webui_behavior_checklist_fast.py::{test_ui_progress_complete_cascades_and_falls_back_to_write}``【F:tests/unit/interface/test_webui_progress.py†L220-L353】【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L1022-L1056】
