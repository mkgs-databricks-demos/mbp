# 2026-11-28 — Wave 6, Session 10a: Benchmark Questions, View Group A

* Build run: 409860738864401 (job 138308594859344, task `w6_session`), continuation 0, first attempt.
* Mode: `edit` + `allow_execute`. Workflow `hybrid`, branch `genie-build-bakehouse` (checked read-only; no Git commands run).
* Status: **pass**.

## Context

* Skills: the UC skill ids for `genie_build_session_runner` and `ontology_tuning` did not resolve through `readSkillFile`. I used the workspace fallbacks: `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md` and `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md`.
* Read: `waves.json` (wave 6, session 10a), plan 10, plans `INDEX.md`, `PROJECT_MEMORY.md`, `sdk_config.json`, session 09 summary, the metric view manifest and YAML, and `docs/registration/resolved_target.json`. There is no `hi_genie/` folder. As plan 10 requires, I did not read the agent instructions.
* SDK wheel 0.1.1 (SDK checkout `dist/`) was installed in this session's serverless Python env only.

## Decisions

* View group A is the first half of the 3-view manifest by name, rounded up: `mv_bakehouse_customer_activity` and `mv_bakehouse_sales`. I rounded up so no view is left uncovered when two sessions split an odd count in parallel. Session 10b's `group_b.yml` covers `mv_bakehouse_sales` and `mv_bakehouse_supplier_coverage`, so sales is covered by both files. That overlap is harmless, and no ids collide.
* Before writing filters, I checked the dimension values in the data (gender, countries, purchase bands, customer id range, payment methods, store sizes, cities).

## Changes

* `docs/tuning/benchmark/group_a.yml`: 80 single-view questions (`a-001`..`a-080`). Each has type/view/measure/dimension tags (view-qualified) and tokenized `MEASURE()` SQL over `${target_catalog}.${target_schema}`.
* `docs/tuning/benchmark/group_a_notes.md`: the statement state for every id, the coverage result and the edge cases.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| `benchmark.load_questions` parses the file (80 questions, unique ids) | pass |
| written file is byte-equal to the authored and executed set | pass |
| every `expected_sql`, re-run from the written file, is `SUCCEEDED` | pass (80/80) |
| notes table matches the executed states for all 80 ids | pass |
| coverage, group A views: >= 12 per view (34 / 46), every measure and dimension tagged | pass |
| file-only coverage problems (< 100 total, 0% cross-view, `cross_view` type unused) | expected; the wave gate checks these on the combined set |
| `bundle validate` | skipped (no YAML bundle files touched) |

## Requests

None.
