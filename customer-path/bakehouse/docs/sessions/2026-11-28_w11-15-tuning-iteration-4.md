# 2026-11-28 - Wave 11, Session 15: Tuning Iteration 4 (Conditional, MV-First)

* Build run: 409860738864401 (job 138308594859344, task `w11_session`), continuation 0.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (checked read-only through the Repos API: branch `genie-build-bakehouse`, head ca9152af0078; no Git commands).
* Status: **pass**.

## Context

* Skills: the UC skill id `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`. ontology-tuning: used `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md` (as session 14).
* Read: `waves.json` (wave 11, session 15), plan 12, `PROJECT_MEMORY.md`, `sdk_config.json`, session 14 summary and status, `tuning_plan_04.md`, `iterations/03.md`, `accuracy_history.json`, the YAML files and the agent instructions (benchmarks section not read). No `hi_genie/` folder.
* SDK wheel 0.1.1 installed from the SDK `sdk_wheels` volume in this session's serverless Python env only. Module constants match the skill table.

## What was done

1. **Asymptote first (conditional iteration).** `benchmark.asymptote` over the 4-entry history: `reached=False` (3 plans, deltas 2.05, -0.68 pp). Full iteration required.
2. **Applied tuning_plan_04 in ladder order.** S13 (`Franchise ID` tie-break comment), S14 (`Franchise Size` combined-sizes comment), S15 (`Customer Gender` exact lowercase values, mv_bakehouse_sales), A4 (same, mv_bakehouse_customer_activity), G1r (removed ", then the name," from the G1 agent instruction). Stored gender values confirmed `male`, `female`.
3. **Validate and register.** `mv_yaml validate` exit 0 (3 files); `manifest.build_manifest` equals the committed `manifest.json`. `bundle validate --strict --target dev` OK; `bundle deploy --target dev` (0 changed, source-linked). `bundle run register_metric_views --target dev`: job 859595802942054, run 441938839010062, SUCCESS 09:58-10:01Z (generate_manifest 3, smoke_test 3 passed, cardinality_test 2 checked / 0 failed). All four comments present in `SHOW CREATE TABLE`.
4. **Agents.** In-process `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` exit 0 (target schema and 3 identifiers resolve). `bundle validate --strict --target dev` OK; `bundle deploy --target dev`: 1 changed. Space `01f1eaeeac87195fa93d5b083cc91e84` update_time 2026-11-28T10:02:38Z; G1r text live.
5. **Re-evaluate.** `benchmark.run_eval(..., questions=qs)`: eval run `01f1eb12ed5416b4899a1792a7e7a3c6`, started 2026-11-28T10:03:14Z (~35 min). Tuning 135/146 (92.5%, +1.4 pp, best so far); holdout 34/41 (82.9%, -7.3 pp, numbers only). 186/187 SQL succeeded, 0 errors, 0 `unit_mismatch`, 0 `needs_review`. Fixed 3 (x-047, x-054, a-055: all targeted; x-004 stays fixed), regressed 1 (x-021), still failing 10 (benchmark_defect candidates). Appended iteration 4 to `accuracy_history.json` (5 entries). Asymptote after: not reached (deltas -0.68, +1.37 pp; holdout gap 7.3 pp).
6. **iterations/04.md** from `write_iteration_md` output (built in /tmp, written with the file tools) plus asymptote note, delta, overfitting signal, regression triage, defect and SDK sections. **tuning_plan_04.md** marked applied with an outcome per action. **tuning_plan_05.md**: 11 tuning failures (Filter / edge 1: x-021; Benchmark defect 10); actions C10 (step 1 comment in mv_bakehouse_supplier_coverage) and R1 (revert G1r, the overfitting response for the holdout drop). No new agent instruction or example SQL.

## Problems found

* **Holdout fell 3 questions while tuning rose 2.** Treated as the skill's overfitting signal; plan 05 reverts the latest agent-layer change (G1r) and states a decision rule for plan 06 if holdout does not recover (then it is evaluation variance, re-apply G1r). Holdout questions were not opened.
* **x-021** (tuning split): Genie keeps the `Unknown` supplier-continent row in a per-supplier question; not caused by a plan 04 change.
* **SDK**: passing `questions=` to `run_eval` returns benchmark ids directly (no text mapping needed this time); `Result.split` still `None`, splits taken from `splits.json`. Subprocess render still fails on default auth; in-process `runpy` works.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| asymptote checked first (not reached) | pass |
| `mv_yaml validate ontology-metric-views/metric_views` | pass (exit 0, before deploy and at the end) |
| manifest unchanged | pass |
| `bundle validate --strict --target dev` (ontology-metric-views) | pass |
| `bundle deploy --target dev` (ontology-metric-views) | pass |
| `register_metric_views` run 441938839010062 SUCCESS, started after the YAML change | pass |
| comments in UC | pass (4/4) |
| geniespace render `--check` | pass |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |
| `bundle deploy --target dev` (ontology-genie-agents) | pass |
| iteration_04 | pass |
| mv_first | pass |
| holdout blindness (0 holdout ids in 04.md, plan 04, plan 05) | pass |
| agent file tokenized (no literal catalog / warehouse id) | pass |

## Requests / notes

* Session 16 (iteration 5): check the asymptote first, then apply `tuning_plan_05.md` (C10 YAML comment -> register; R1 restores the G1 text -> render `--check`, redeploy agents) and follow its plan 06 decision rule on holdout.
* Owner: benchmark_defect candidates a-045, a-046, a-061, b-010, b-039, b-042, x-018, x-035, x-048, x-055 (10 of 11 remaining tuning failures; frozen, not edited).
* SDK owner: `run_eval` should set `Result.split`.

## Files

* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_sales.yml`
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_customer_activity.yml`
* `ontology-genie-agents/agents/bakehouse_retail_sales_agent.geniespace.json`
* `docs/tuning/tuning_plan_04.md` (marked applied, outcomes)
* `docs/tuning/accuracy_history.json` (iteration 4 appended)
* `docs/tuning/iterations/04.md` (new)
* `docs/tuning/tuning_plan_05.md` (new)
* Gitignored `ontology-genie-agents/.rendered/` refreshed by the render step.
