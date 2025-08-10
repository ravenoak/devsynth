# Sprint-EDRR Integration Guide

This guide explains how the `SprintAdapter` connects traditional sprint practices with DevSynth's Expand, Differentiate, Refine, Retrospect (EDRR) methodology.

## Phase Alignment

Sprint ceremonies map directly to EDRR phases:

- **Sprint Planning** → **Expand**. Requirement analysis during the Expand phase produces the inputs for the upcoming sprint plan.
- **Sprint Retrospective** → **Retrospect**. Outputs from the Retrospect phase are summarized into actionable retrospective insights.

## Integration Steps

1. **Expand to Plan** – Requirement analysis during the Expand phase is translated into the upcoming sprint plan, including scope, objectives, and success criteria.
2. **Retrospect to Improve** – After the Retrospect phase, evaluation metrics, positives, improvements, and action items are consolidated into sprint retrospective summaries.
3. **Ceremony Mapping** – `SprintAdapter.get_ceremony_phase()` maps common ceremonies to the correct EDRR phases, ensuring planning aligns with Expand and retrospectives align with Retrospect.

## Requirement Analysis

During the **Expand** phase, requirement analysis results feed directly into sprint planning. After each cycle, the adapter updates the upcoming sprint plan and records the actual scope delivered.

## Retrospective Evaluation

Retrospective data is automatically reviewed at the end of the cycle. Evaluation metrics are stored for later inspection alongside positive notes, improvement areas, and action items.

## Usage

1. Configure DevSynth to use the sprint methodology.
2. Run an EDRR cycle. Requirement analysis outcomes will populate the next sprint plan.
3. After the Retrospect phase, evaluation results are logged into sprint metrics for continuous improvement.

## Consensus and Logging

Dialectical reasoning now checks for consensus before recording requirement decisions. When consensus cannot be reached, the failure is logged so teams can address outstanding conflicts in subsequent EDRR cycles, completing the feedback loop.
