# Methodology Integration Guide

This guide outlines how the `SprintAdapter` aligns EDRR phases with Agile sprint ceremonies.

## Sprint Planning and Requirement Analysis

During the **Expand** phase the adapter automatically converts results from the requirements analysis step into a sprint plan. The plan captures the recommended scope, objectives and success criteria for the upcoming sprint.

## Automated Retrospective Review

After the **Retrospect** phase the adapter summarizes retrospective findings and records them in sprint metrics. Evaluations are stored alongside the summary to support continuous improvement.

## Setup

1. Instantiate `SprintAdapter` with sprint settings.
2. Call `after_expand` with Expand results to update the sprint plan.
3. Call `after_retrospect` with Retrospect results to capture the review.
4. Execute `after_cycle` to finalize metrics and reporting.
