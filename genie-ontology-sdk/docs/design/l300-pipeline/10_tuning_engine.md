# Session 10 — Tuning Plan & Benchmark Execution

**Wave:** 8 — Tuning
**Mode:** execute
**Depends on:** 09
**Estimated effort:** Heavy (~30+ min, may need multiple continuation passes)

## Goal

Generate a tuning plan, run benchmark questions, and iterate on metric view definitions to improve accuracy. Core principle: **tune the metric views first, not the agent**.

## Context

Read: `docs/tuning/deployment_results.md` (space_ids), `docs/research/02_kpi_definitions.md` (benchmark source), `ontology-metric-views/metric_views/**/*.yml` (current MVs), `ontology-genie-agents/agents/*.geniespace.json` (current agents).

## Tasks

### 1. Generate Benchmark Questions

10-20 questions per agent covering: simple single-measure, multi-dimension breakdowns, time comparisons, filtered queries, ratio/derived measures, edge cases.

Write to: `docs/tuning/benchmark_questions.md`

### 2. Run Benchmarks

For each question, send to agent via conversation API. Evaluate: SQL generated, correct tables, correct measures (MEASURE()), correct filters, reasonable results.

### 3. Diagnose Failures

**MV-level fixes (Phase 1 — do first):** missing synonym, ambiguous measure comment, missing measure, wrong filter, missing dimension.

**Agent-level fixes (Phase 2 — only if MV fixes insufficient):** genuinely ambiguous term instruction, complex multi-step example SQL, cross-MV join spec.

### 4. Apply Fixes and Re-test

Update MV YAMLs, re-register (CREATE OR REPLACE VIEW), re-run failed benchmarks. Repeat until accuracy >= 70%.

### 5. Write Results

`docs/tuning/tuning_plan.md`: Phase 1 and Phase 2 actions with rationale.
`docs/tuning/benchmark_results.md`: question, expected, actual, pass/fail, overall accuracy per agent.

## Pass Criteria

- [ ] Tuning plan documented
- [ ] Benchmark results with accuracy scores
- [ ] Overall accuracy >= 70%
- [ ] MV changes applied and re-registered
- [ ] Agent changes minimal (overfitting avoided)
