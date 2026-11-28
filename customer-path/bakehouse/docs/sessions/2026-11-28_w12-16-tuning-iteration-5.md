# 2026-11-28 - Wave 12, Session 16: Tuning Iteration 5 (Conditional, MV-First)

* Build run: 409860738864401 (job 138308594859344, task `w12_session`), continuation 0.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (checked read-only through the Repos API: branch `genie-build-bakehouse`, head b72e4014869c; no Git commands).
* Status: **pass**.

## Context

* Skills: the UC skill id `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`. ontology-tuning: the UC id did not resolve either; used `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md` (as sessions 14-15).
* Read: `waves.json` (wave 12, session 16), plan 12, `sdk_config.json`, session 15 summary and status, `tuning_plan_05.md`, `iterations/04.md`, `accuracy_history.json`, the supplier-coverage YAML and the agent instructions (benchmarks section not read). No `hi_genie/` folder.
* SDK wheel 0.1.1 installed from `/Volumes/hls_fde_dev/dev_matthew_giglia_ontology_sdk/sdk_wheels` in this session's serverless Python env only. Module constants match the skill table.

## What was done

1. **Asymptote first (conditional iteration).** `benchmark.asymptote` over the 5-entry history: `reached=False` (4 plans, deltas -0.68, +1.37 pp, holdout gap 7.3 pp). Full iteration required.
2. **Applied tuning_plan_05 in ladder order.** C10 (step 1: per-supplier 'Unknown' rule on the `Supplier Continent` and `Franchises per Supplier` comments in mv_bakehouse_supplier_coverage), then R1 (restored the plan 03 G1 text "ORDER BY the measure DESC, then the name, and LIMIT N" in the agent's top-N instruction; revert of G1r, no new instruction).
3. **Validate and register.** `mv_yaml validate` exit 0 (3 files); `manifest.build_manifest` equals the committed `manifest.json`. `bundle validate --strict --target dev` OK; `bundle deploy --target dev` (0 changed, source-linked). `bundle run register_metric_views --target dev`: job 859595802942054, run 370009555972263, SUCCESS 10:55-10:57Z (generate_manifest 3, smoke_test 3 passed, cardinality_test 2 checked / 0 failed). Both C10 comments present in `SHOW CREATE TABLE`.
4. **Agents.** In-process `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` exit 0 (target schema and 3 identifiers resolve). `bundle validate --strict --target dev` OK; `bundle deploy --target dev`: 1 changed. Space `01f1eaeeac87195fa93d5b083cc91e84` update_time 2026-11-28T10:58:46Z; R1 text live.
5. **Re-evaluate.** `benchmark.run_eval(..., questions=qs)` in a background thread: eval run `01f1eb1ac8b81eafb4ed2a621d77348a`, started 2026-11-28T10:59:29Z (~41 min). Tuning 133/146 (91.1%, -1.4 pp); holdout 36/41 (87.8%, +4.9 pp, numbers only). 186/187 SQL succeeded, 0 errors, 0 `unit_mismatch`, 0 `needs_review`. Fixed 1 (x-021, targeted; x-004 stays fixed), regressed 3 (x-047 by R1; b-044, x-016 not caused by plan 05), still failing 10. Appended iteration 5 to `accuracy_history.json` (6 entries). Asymptote after: not reached (deltas +1.37, -1.37 pp; holdout gap 2.4 pp).
6. **iterations/05.md** from `write_iteration_md` output plus asymptote note, delta, overfitting-response outcome, regression triage, defect and SDK sections. **tuning_plan_05.md** marked applied with an outcome per action. **tuning_plan_06.md**: 13 tuning failures (Ambiguity 1: x-047; Filter / edge 1: b-044; Benchmark defect 11); actions S16 (step 1 `Franchise Name` comment in mv_bakehouse_sales) and C11 (step 1 lowercase `Supplier Ingredient` comment). Agent: keep R1 per the plan 05 decision rule (case 2); no agent change.

## Problems found

* **R1 trade-off.** Restoring "then the name" won back 2 holdout questions and lost x-047 (tie at 1.0 broken by Franchise Name instead of Franchise ID). Plan 06 fixes it in the metric view, not in the agent.
* **b-044:** supplier ingredients are stored lowercase; Genie filtered `'Almonds'`.
* **x-016:** grading variance on an expectation that adds a column not asked for (values match); recorded as benchmark_defect.
* **Asymptote:** 5 of 6 plans applied, not reached. Iteration 6 (session 17) is the last before `exhausted`.
* **SDK:** `Result.split` still `None` (splits from `splits.json`).

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| asymptote checked first (not reached) | pass |
| `mv_yaml validate ontology-metric-views/metric_views` | pass (exit 0, before deploy and at the end) |
| manifest unchanged | pass |
| `bundle validate --strict --target dev` (ontology-metric-views) | pass |
| `bundle deploy --target dev` (ontology-metric-views) | pass |
| `register_metric_views` run 370009555972263 SUCCESS, started after the YAML change | pass |
| comments in UC | pass (2/2) |
| geniespace render `--check` | pass |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |
| `bundle deploy --target dev` (ontology-genie-agents) | pass |
| iteration_05 | pass |
| mv_first | pass |
| holdout blindness (0 holdout ids in 05.md, plan 05, plan 06) | pass |
| agent file tokenized, `validate_space` 0 problems | pass |

## Requests / notes

* Session 17 (iteration 6): check the asymptote first, then apply `tuning_plan_06.md` (S16, C11: YAML comments -> register; no agent change), re-evaluate, and write `tuning_summary.md`. If not reached after iteration 6, `asymptote` reports `exhausted`: state it plainly for the owner.
* Owner: benchmark_defect candidates a-045, a-046, a-061, b-010, b-039, b-042, x-016, x-018, x-035, x-048, x-055 (11 of 13 remaining tuning failures; frozen, not edited).
* SDK owner: `run_eval` should set `Result.split`.

## Files

* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_supplier_coverage.yml`
* `ontology-genie-agents/agents/bakehouse_retail_sales_agent.geniespace.json`
* `docs/tuning/tuning_plan_05.md` (marked applied, outcomes)
* `docs/tuning/accuracy_history.json` (iteration 5 appended)
* `docs/tuning/iterations/05.md` (new)
* `docs/tuning/tuning_plan_06.md` (new)
* Gitignored `ontology-genie-agents/.rendered/` refreshed by the render step.
