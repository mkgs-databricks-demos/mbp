# 2026-11-28 — Wave 10, Session 14: Tuning Iteration 3 (MV-First)

* Build run: 409860738864401 (job 138308594859344, task `w10_session`), continuation 0.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (checked read-only with `runGit status`; no state-changing Git commands).
* Status: **pass**.

## Context

* Skills: the UC skill id `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`. ontology-tuning UC id also did not resolve; used `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md`.
* Read: `waves.json` (wave 10, session 14), plan 12, `PROJECT_MEMORY.md`, `sdk_config.json`, session 13 summary and status, `tuning_plan_03.md`, `iterations/02.md`, `accuracy_history.json`, the three metric view YAML files, the agent file's instructions (benchmarks section not read), bundle README / `genie_agents.yml`. No `hi_genie/` folder.
* SDK wheel 0.1.1 installed from the SDK `sdk_wheels` volume in this session's serverless Python env only.

## What was done

1. **Applied tuning_plan_03 in ladder order.**
   * S12 (step 6): new dimension `Supplier Size` = `COALESCE(franchise.supplier.size, 'Unknown')` in `mv_bakehouse_sales`, exact-value / keep-Unknown comment, synonyms `supplier size band`, `vendor size`.
   * C9 (step 1): `Supplier Size` comment in `mv_bakehouse_supplier_coverage` (exact values, keep Unknown, points to the sales dimension).
   * A3 (step 1): `Customer Purchase Band` comment in `mv_bakehouse_customer_activity` (all five exact values, `'11 or more times'` = `'11+ purchases'`). Listed all five CASE values rather than the plan's three (the current data has only three); noted in the plan outcome.
   * G1 (step 9): one text instruction in the agent file for exact top-N rows (backed by plan 03's x-004 exhaustion record).
2. **Validate and register.** `mv_yaml validate` exit 0 (3 files, 0 errors); `manifest.build_manifest` equals the committed `manifest.json` (not rewritten). `bundle validate --strict --target dev` OK; `bundle deploy --target dev` (0 changed, source-linked). `bundle run register_metric_views --target dev`: job 859595802942054, run 408107907495195, SUCCESS (generate_manifest 3, cardinality_test 2 checked / 0 failed, smoke_test 3 passed). Read-only checks: `Supplier Size` in mv_bakehouse_sales gives 6 rows incl. Unknown = 33537 (sum 66471 = total gross sales); purchase bands 11+ = 163, 6-10 = 128, 2-5 = 9; the three new comments are in `SHOW CREATE TABLE`.
3. **Agents.** In-process `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` -> exit 0 (`target schema and 3 identifiers resolve`); a subprocess run failed on default auth in the notebook env, so the in-process form (as in session 09) was used. `bundle validate --strict --target dev` OK; `bundle deploy --target dev`: `Updated genie_spaces.bakehouse_retail_sales_agent` (1 changed). Space `01f1eaeeac87195fa93d5b083cc91e84` `update_time` 2026-11-28T09:06:49Z; instruction present in the deployed space.
4. **Re-evaluate.** `benchmark.run_eval` eval run `01f1eb0b1b1913d6b9212913ea668510`, started 2026-11-28T09:07:15Z (35 min). Tuning 133/146 (91.1%, -0.7 pp); holdout 37/41 (90.2%, +4.9 pp, best so far); 186 SQL succeeded, 0 errors, 0 `unit_mismatch`, 0 `needs_review`. Fixed 3 (x-004, x-008, x-042: all targeted), regressed 4 (a-055, b-010, x-047, x-054), still failing 9 (benchmark_defect candidates). Appended iteration 3 to `accuracy_history.json` (4 entries). `asymptote`: not reached (3 plans; deltas 2.05, -0.68 pp).
5. **iterations/03.md** from `write_iteration_md` output (built in /tmp, written with the file tools) plus delta, regression triage, defect and SDK-note sections. 0 holdout ids.
6. **tuning_plan_03.md** marked applied with an outcome per action. **tuning_plan_04.md**: 13 tuning failures triaged (Ambiguity 2, Unit / format 1, Benchmark defect 10); actions S13, S14, S15 (step 1 comments in mv_bakehouse_sales), A4 (step 1 in mv_bakehouse_customer_activity) and G1r (partial revert of G1's "then the name" tie-break, which caused x-047). No new agent instruction.

## Problems found

* **G1 regressed x-047.** Its "then the name" tie-break ordered tied stores by `Franchise Name`; the expectation (and the Franchise ID comment) uses `Franchise ID`. Net 0 on the tuning split (x-004 fixed, x-047 broken); plan 04 removes the clause and moves the tie-break to the `Franchise ID` comment.
* **SDK** (carried): `run_eval` results carry Genie benchmark ids and `split = None`; mapped by exact question text (187/187) and `splits.json` before scoring.
* **SDK render in subprocess** fails on default auth in the serverless notebook env; in-process `runpy` works.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| `mv_yaml validate ontology-metric-views/metric_views` | pass (exit 0, before deploy and at the end) |
| manifest unchanged | pass |
| `bundle validate --strict --target dev` (ontology-metric-views) | pass |
| `bundle deploy --target dev` (ontology-metric-views) | pass |
| `register_metric_views` run 408107907495195 SUCCESS, started after the YAML change | pass |
| new dimension / comments in UC | pass |
| geniespace render `--check` | pass |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |
| `bundle deploy --target dev` (ontology-genie-agents) | pass |
| iteration_03 | pass |
| next_plan (`tuning_plan_04.md`) | pass |
| mv_first | pass |
| holdout blindness (0 holdout ids in 03.md, plan 03, plan 04) | pass |

## Requests / notes

* Session 15 (iteration 4): apply `tuning_plan_04.md` (YAML comments S13-S15, A4; G1r removes text from the agent file: render with `--check`, redeploy `ontology-genie-agents`). The asymptote is not reached; check it first per plan 12.
* Owner: benchmark_defect candidates a-045, a-046, a-061, b-010, b-039, b-042, x-018, x-035, x-048, x-055 (10 of 13 remaining tuning failures; frozen, not edited).
* SDK owner: `benchmark.run_eval` should return benchmark question ids and splits.

## Files

* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_sales.yml`
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_supplier_coverage.yml`
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_customer_activity.yml`
* `ontology-genie-agents/agents/bakehouse_retail_sales_agent.geniespace.json`
* `docs/tuning/tuning_plan_03.md` (marked applied, outcomes)
* `docs/tuning/accuracy_history.json` (iteration 3 appended)
* `docs/tuning/iterations/03.md` (new)
* `docs/tuning/tuning_plan_04.md` (new)
* Gitignored `ontology-genie-agents/.rendered/` refreshed by the render step.
