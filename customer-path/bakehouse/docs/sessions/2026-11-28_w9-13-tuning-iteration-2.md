# 2026-11-28 — Wave 9, Session 13: Tuning Iteration 2 (MV-First)

* Build run: 409860738864401 (job 138308594859344, task `w9_session`), continuation 0.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (checked read-only with `runGit status`; no state-changing Git commands).
* Status: **pass**.

## Context

* Skills: the UC skill id `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`. ontology-tuning from `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md` (same fallback as session 12).
* Read: `waves.json` (wave 9, session 13), plan 12, `sdk_config.json`, session 12 summary and status, `tuning_plan_02.md`, `iterations/01.md`, `accuracy_history.json`, the two changed metric view YAML files, `resolved_target.json`.
* SDK wheel 0.1.1 installed from `/Volumes/hls_fde_dev/dev_matthew_giglia_ontology_sdk/sdk_wheels/.internal/` in this session's serverless Python env only.

## What was done

1. **S10 read-only check first.** On the registered `mv_bakehouse_sales`, `Prior Day Gross Sales` for `Supplier on file` on 2024-05-16 = 1755 (filtered, or grouped by date and status) = `Gross Sales` on 2024-05-15 for that group. The per-store sum (expected 1647) drops stores with no sale on 2024-05-16. The measure is right; x-048 is a benchmark defect. No expression change (step 5 not needed).
2. **Applied tuning_plan_02 (metric views only; comments and synonyms).**
   * `mv_bakehouse_supplier_coverage`: C7 exact-value / `=`-filter comment on `Supplier Continent`; C8 synonyms `approved vendors`, `number of approved suppliers`, `number of approved vendors` and a usage note on `Approved Suppliers`.
   * `mv_bakehouse_sales`: S8 'Unknown supplier is not a supplier' note on `Supplier Name`; S9 'do not multiply by 100' on the view comment and on `Franchises with Sales`; S10 grouping note on `Prior Day Gross Sales`. S11 record only.
3. **Validate and register.** `mv_yaml validate` exit 0 (3 files, 0 errors); `manifest build` to a temp path equals the committed `manifest.json` (unchanged, not rewritten). `bundle validate --strict --target dev` OK; `bundle deploy --target dev` (source-linked, 0 changed). `register_metric_views` job 859595802942054, run 251284026050684: SUCCESS (generate_manifest, cardinality_test 2 checked / 0 failed, smoke_test 3 passed). All five new comments verified in `SHOW CREATE TABLE`.
4. **Agents.** No agent change in plan 02; `ontology-genie-agents` not redeployed; `bundle validate --strict --target dev` OK.
5. **Re-evaluate.** `benchmark.run_eval` eval run `01f1eb035de91aad886e10d893b5fefc`, started 2026-11-28T08:11:51Z (35 min). Tuning 134/146 (91.8%, +2.1 pp); holdout 35/41 (85.4%, unchanged); 186 SQL succeeded, 0 errors. Fixed 5 (b-010, b-013, b-048, x-056, x-059), regressed 2 (x-008, x-042), still failing 10. Appended iteration 2 to `accuracy_history.json`; `asymptote`: not reached (2 of 3 required plans; deltas 9.59, 2.05 pp).
6. **iterations/02.md** written from `write_iteration_md` output (built in /tmp, copied with the file tools), plus delta, S10 check, defect and SDK-note sections. 0 holdout ids in it.
7. **tuning_plan_02.md** marked applied with an outcome per action. **tuning_plan_03.md**: 12 tuning failures triaged (Filter / edge 2, Ambiguity 1, Benchmark defect 9); actions S12 (step 6: `Supplier Size` in mv_bakehouse_sales), C9 and A3 (step 1 comments), and G1 (step 9, one agent instruction for exact top-N rows) backed by a completed x-004 exhaustion record.

## Problems found

* **SDK: `run_eval` results carry the Genie benchmark id (32-hex) as `question_id`, and `split = None`.** `score` therefore gave n=0 per split. Fixed in-session by mapping each result to its benchmark id by exact question text (187/187) and the split from `splits.json`; overall 169/187 unchanged. Session 12 saw only the split symptom. Candidate SDK fix: map ids and splits in `run_eval` when `questions` is given.
* x-055: S8 worked, but the question still grades BAD on rounding alone (expectation uses `ROUND(..., 2)`).

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| `mv_yaml validate ontology-metric-views/metric_views` | pass (exit 0, before deploy and at the end) |
| manifest unchanged (temp build diff) | pass |
| `bundle validate --strict --target dev` (ontology-metric-views) | pass |
| `bundle deploy --target dev` (ontology-metric-views) | pass |
| `register_metric_views` run 251284026050684 after the YAML change | pass (SUCCESS) |
| new comments present in UC | pass (5/5) |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass (unchanged) |
| iteration_02 | pass |
| next_plan (`tuning_plan_03.md`) | pass |
| mv_first (no agent instruction or example SQL changed this iteration; G1 planned with exhaustion record) | pass |
| holdout blindness (0 holdout ids in 02.md and tuning_plan_03.md) | pass |

## Requests / notes

* Owner: benchmark_defect candidates now a-045, a-046, a-061, b-039, b-042, x-018, x-035, x-048, x-055 (frozen; not edited). 9 of 12 remaining tuning failures.
* Session 14 (iteration 3): apply `tuning_plan_03.md`. G1 changes the agent file: render with `--check` and redeploy `ontology-genie-agents`.
* SDK owner: `benchmark.run_eval` should return benchmark question ids and splits (see Problems).

## Files

* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_supplier_coverage.yml`
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_sales.yml`
* `docs/tuning/tuning_plan_02.md` (marked applied, outcomes)
* `docs/tuning/accuracy_history.json` (iteration 2 appended)
* `docs/tuning/iterations/02.md` (new)
* `docs/tuning/tuning_plan_03.md` (new)
