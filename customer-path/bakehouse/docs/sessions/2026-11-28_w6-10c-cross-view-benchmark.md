# 2026-11-28 — Wave 6, Session 10c: Cross-View Benchmark Questions

* Build run: 409860738864401 (job 138308594859344, task `w6_session`), continuation 0.
* Mode: `edit` + `allow_execute` (read-only SQL). Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder at `ed0cab1`, read-only branch check; no Git commands).
* Status: **pass**.

## Context

* Session-runner UC skill id did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`. The `ontology_tuning` UC skill also did not resolve; used `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md`.
* Read: `waves.json` (wave 6, session 10c), plan 10, `PROJECT_MEMORY.md`, `sdk_config.json`, session 09 summary, the three metric view YAMLs, `metric_views/manifest.json`, `docs/registration/resolved_target.json`, SDK `benchmark` docstring. Agent instructions not read (plan rule). No `hi_genie/` folder.

## What was done

1. Installed SDK wheel 0.1.1 in the session's serverless Python env only.
2. Wrote 59 cross-view questions (`x-001`..`x-059`) in `docs/tuning/benchmark/cross_view.yml`, each over two or three metric views, with tokenized `MEASURE()` expected SQL joined across views on `Franchise ID`, franchise geography/size, or customer geography/gender.
3. First run: 15 statements failed (`Customer ID` is not a dimension of `mv_bakehouse_sales`; `Franchises per Supplier` divides by zero for the 'Unknown' supplier group). Rewrote those questions to join on customer geography/gender and to filter to suppliers on file.
4. Ran every `expected_sql` read-only on warehouse `24087b85239cacac`: 59/59 `SUCCEEDED`. Ids and states listed in `docs/tuning/benchmark/cross_view_notes.md`.
5. Verified the written file byte-for-byte equals the validated text, and that `benchmark.load_questions` parses 59 unique ids.
6. Coverage: own file 59/59 cross-view; combined set with `group_a.yml` / `group_b.yml` = 187 questions, 31.6% cross-view, no problems.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| expected_sql_runs (59/59 SUCCEEDED on warehouse) | pass |
| load_questions parses file, ids unique, prefix `x-` | pass |
| benchmark_coverage (combined set, informational; gate runs it) | pass |

## Findings / requests

* `Franchises per Supplier` raises DIVIDE_BY_ZERO when a group has no suppliers. Candidate MV-first fix for tuning (session 12): guard the denominator.
* `mv_bakehouse_sales` has no `Customer ID` dimension; per-customer cross-view questions are not expressible over metric views.

## Files

* `docs/tuning/benchmark/cross_view.yml` (new)
* `docs/tuning/benchmark/cross_view_notes.md` (new)
