# 2026-11-28 — Wave 8, Session 12: Tuning Iteration 1 (MV-First)

* Build run: 409860738864401 (job 138308594859344, task `w8_session`), continuation 0.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (checked read-only with `git rev-parse`; no state-changing Git commands).
* Status: **pass**.

## Context

* Skills: the UC skill ids for `genie_build_session_runner` and `ontology-tuning` did not resolve through `readSkillFile`; used the workspace fallbacks `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md` and `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md`.
* Read: `waves.json` (wave 8, session 12), plan 12, `PROJECT_MEMORY.md`, `sdk_config.json`, session 11 summary and status, `tuning_plan_01.md`, the three metric view YAML files, the agent file. No `hi_genie/` folder.
* SDK wheel 0.1.1 installed in this session's serverless Python env only.

## What was done

1. **Applied tuning_plan_01 (metric views only).** 13 actions across the three views (see the plan's Outcome column):
   * `mv_bakehouse_sales`: exact-value / `=`-filter comments on `Franchise Country`, `Franchise Size`, `Customer State`; day-over-day synonyms and comments on the growth measures; "do not multiply by 100" on `Product Mix` and the growth measure; per-store note on `Sales per Franchise`; **C4**: nested LEFT join `franchise -> supplier` and new dimensions `Supplier Status`, `Supplier Name`, `Supplier Approved`.
   * `mv_bakehouse_supplier_coverage`: value lists and synonyms on `Supplier Status` / `Supplier Approved`; basis comments on the two approved-supplier shares.
   * `mv_bakehouse_customer_activity`: country mapping comment, state value comment, grain comments on `First/Last Purchase Date` and `Buying Customers`.
2. **Two planned expression changes were applied as comments instead (decision).** S3 (map `California` to `CA`) and A1 (`USA` to `US`) would have changed what the frozen benchmark's `expected_sql` returns: it filters `Customer State = 'CA'` and `Customer Country = 'USA'`. Also, the source data shows `California`-style full names belong to customers whose country is Australia or Japan, while USA customers use 2-letter codes, so the mapping would merge different customers. Both questions (b-026, x-043) were fixed by the comments.
3. **Validate and register.** `mv_yaml validate` exit 0 (3 files, 0 errors); `manifest build` wrote 3 entries (unchanged). `bundle validate --strict --target dev` OK; `bundle deploy --target dev` (source-linked, 0 resources changed). `register_metric_views` job 859595802942054, run 504480741442581: SUCCESS (generate_manifest, register_each_mv, smoke_test, cardinality_test all SUCCESS). Read-only check on the registered view: `Supplier Status` in mv_bakehouse_sales gives 21 / 27 stores and gross sales 33537 / 32934, equal to the cross-view join through mv_bakehouse_supplier_coverage; the new comments are present.
4. **Agents.** No agent change: the agent tables have no `column_configs`, so the new dimensions are visible without editing the space. `ontology-genie-agents` not redeployed; `bundle validate --strict --target dev` OK.
5. **Re-evaluate.** `benchmark.run_eval` eval run `01f1eafb99ba1a47ac5f2814b651116f`, started 2026-11-28T07:16:16Z (about 35 min). Tuning 131/146 (89.7%, +9.6 pp from 80.1%); holdout 35/41 (85.4%, from 80.5%); 186 SQL succeeded, 0 errors, 0 `unit_mismatch`, 0 `needs_review`. Fixed 16, regressed 2 (a-046, b-048), still failing 13. Appended iteration 1 to `accuracy_history.json`; `asymptote`: not reached (1 of 3 required plans).
6. **iterations/01.md** written with `write_iteration_md`, plus delta, defect and SDK-note sections.
7. **tuning_plan_02.md**: 15 tuning failures triaged (Filter / edge 3, Unit / format 1, Ambiguity 1, Benchmark defect 10); 4 metric view actions (C7, C8, S8, S9) plus S10 (verify then comment) and one started exhaustion record (x-004, no agent change planned).

## Problems found

* **SDK: `run_eval` results carry `split = None`.** `write_iteration_md` therefore listed no tuning failures on the first call. Fixed by re-attaching splits from `splits.json` (`dataclasses.replace`), then rewriting; score unchanged (131/146), 15 failures listed, 0 holdout ids in the file. Session 11's baseline file was not affected (it lists 29). Candidate SDK fix: map the split in `run_eval` when `questions` is given.
* My first fixed/regressed comparison used a non-existent `correct` attribute and reported 146 failures; caught because it contradicted `score`, and redone with `matches_expected`.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| `mv_yaml validate ontology-metric-views/metric_views` | pass (exit 0) |
| `bundle validate --strict --target dev` (ontology-metric-views) | pass |
| `bundle deploy --target dev` (ontology-metric-views) | pass |
| `register_metric_views` run 504480741442581 after the YAML change | pass (SUCCESS) |
| new sales supplier dimensions equal the cross-view join | pass |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass (unchanged) |
| iteration_01 (eval after build start, history entry, 01.md, plan 01 marked applied with 16/16 outcomes) | pass |
| next_plan (`tuning_plan_02.md`) | pass |
| mv_first (no agent instruction or example SQL changed) | pass |
| holdout blindness (0 holdout ids in 01.md) | pass |

## Requests / notes

* Owner: benchmark_defect candidates are now a-045, a-046, a-061, b-010, b-013, b-039, b-042, x-018, x-035, x-056 (frozen; not edited). Ten of the 15 remaining tuning failures are candidates, which limits what tuning can still gain.
* Session 13 (iteration 2): apply `tuning_plan_02.md`; S10 needs a read-only check first.
* SDK owner: `benchmark.run_eval` should set `Result.split` (see Problems).

## Files

* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_sales.yml`
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_supplier_coverage.yml`
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_customer_activity.yml`
* `docs/tuning/tuning_plan_01.md` (marked applied, outcomes)
* `docs/tuning/accuracy_history.json` (iteration 1 appended)
* `docs/tuning/iterations/01.md` (new)
* `docs/tuning/tuning_plan_02.md` (new)
* `ontology-metric-views/metric_views/manifest.json` rebuilt, content unchanged
