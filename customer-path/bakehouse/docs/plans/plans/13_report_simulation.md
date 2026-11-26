# Session 18: Independent Report Simulation

## Scope
An evaluation independent of tuning: simulate 4-5 analyst reports for `bakehouse_retail_sales`, each as 8-15 turns in one Genie conversation, graded against ground-truth SQL written before the report is run. Read-only; no deploys. Do not read `docs/tuning/**` or any agent instructions.

## Context
* Inputs allowed: `docs/research/**`, `docs/semantics/**`, `docs/data_profiles/**`, `docs/deployment/deployment_results.md` (space ids), source tables from `docs/inputs_report.md`.
* Ground truth runs over the source tables, not the metric views.
* Target overall score 80%, recorded, not gated: a lower score becomes a backlog item.

## Tasks
1. Write 4-5 report personas in `docs/evaluation/personas.md`, each with 8-15 planned turns.
2. For every turn, write a ground-truth SQL file under `docs/evaluation/ground_truth/`, run it read-only, and record its state and the write time.
3. Run each report as one Genie conversation (`start_conversation_and_wait`, then follow-ups), recording the run time.
4. Grade each turn against its ground truth and write `docs/evaluation/report_simulation_results.md` with per-turn grades, per-report scores and an overall score.
5. State in the session summary that no tuning file and no agent instructions were read.

## Acceptance Criteria
- [ ] 4-5 reports, 8-15 turns each, one conversation per report.
- [ ] Every ground-truth file predates its report run and ran `SUCCEEDED`.

## Owned Paths
- `docs/evaluation/**`

## Dependencies
- Session 17: the tuned agents.
