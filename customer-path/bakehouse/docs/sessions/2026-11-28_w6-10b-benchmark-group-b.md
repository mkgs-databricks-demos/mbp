# 2026-11-28 — W6 Session 10b: Benchmark Questions, View Group B

Build run `409860738864401`, wave 6, mode `edit` (allow_execute), branch `genie-build-bakehouse` (checked read-only).

## Scope
Plan 10 tasks for view group B: single-view benchmark questions with tokenized `expected_sql`, each run read-only, plus a notes file with statement states and an own-file coverage check.

## Decisions
* **Group split.** The manifest has 3 views. "Second half by name" was taken as `names[n//2:]`, so group B = `mv_bakehouse_sales` and `mv_bakehouse_supplier_coverage`, and group A = `mv_bakehouse_customer_activity`. This keeps the middle view covered whichever way 10a rounds (recorded as an assumption).
* **Ids** use the plan's `b-` prefix (`b-001`..`b-048`). The skill's `<group>_001` style is an example; the plan wins on prefix.
* **Skill source.** The UC skill `hls_fde_dev.dev_matthew_giglia_ontology_sdk.ontology_tuning` was not loadable in this session. I used the fallback `skills/ontology-tuning/SKILL.md` from the SDK checkout (`/Users/matthew.giglia@databricks.com/mbp/genie-ontology-modeled-knowledge-sdk`).
* Agent instructions and sample questions were not read (plan 10 context rule). Wording follows the metric view synonyms and business phrasing.
* Edge questions target known data traps: store names that are not unique (b-019), USA vs US country codes (b-023), the partial day 2024-05-17 (b-028), and franchises with no supplier on file (b-039, b-040).

## Changes
* `docs/tuning/benchmark/group_b.yml`: 48 questions (30 sales, 18 supplier coverage).
* `docs/tuning/benchmark/group_b_notes.md`: id / view / type / state / rows / statement_id table, plus coverage result.

## Checks
* expected_sql runs: 48/48 `SUCCEEDED` on the warehouse from `docs/registration/resolved_target.json`, tokens rendered to the dev target, read-only SELECTs.
* `benchmark.load_questions` on the written file: parses, and all 48 items match the executed set exactly (id, question, SQL, tags).
* `benchmark.coverage` on the own file (SDK wheel 0.1.1 installed from `dist/`): both views at least 12 questions, every measure and dimension tagged, every type except `cross_view` used. Problems left at set level: total < 100, cross-view share 0%, `cross_view` unused. The wave gate checks the combined set (10a + 10c).

## Requests / notes for other sessions
* 10c / gate: group B adds 48 questions. The combined set needs at least 100 questions and at least 25% cross-view. If 10a + 10b + 10c stays under 100, 10c needs more questions.
