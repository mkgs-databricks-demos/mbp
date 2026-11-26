# Sessions 10a / 10b / 10c: Benchmark Authoring

## Scope
Write the `{{domain_name}}` benchmark question set in three parallel sessions: 10a covers view group A (first half of `ontology-metric-views/metric_views/manifest.json` by name), 10b covers view group B (second half), 10c writes cross-view questions (two or more metric views). Each question has `expected_sql` that ran read-only with state `SUCCEEDED`. No deploys.

## Context
* Skill: `ontology-tuning`, loaded by its Unity Catalog id from `sdk_config.json` `skills` (`<catalog>.<schema>.ontology_tuning`); if it is not in the session's skill list, read `skills/ontology-tuning/SKILL.md` from the SDK checkout. Follow its question tags, splits and coverage rules.
* SDK (installed wheel `{{sdk_version}}`): `genie_ontology_modeled_knowledge_sdk.benchmark` `load_questions`, `load_question_set`, `coverage(questions, mv_yaml_paths)`.
* Coverage targets for the whole set (checked by the wave gate over all three files): 100-498 questions, at least 12 per metric view, every measure and dimension tagged at least once, at least 25% cross-view.
* Inputs: metric view YAML, `docs/semantics/**`, `docs/research/**`, `docs/data_profiles/**`. Never read agent instructions.

## Tasks
1. Read the manifest and pick your views (10a / 10b) or the join paths between views (10c).
2. Write questions in your file (`docs/tuning/benchmark/group_a.yml`, `group_b.yml` or `cross_view.yml`), each with an id unique across the three files (prefix `a-`, `b-`, `x-`), tags and `expected_sql` over the metric views.
3. Run every `expected_sql` read-only on the warehouse and list each id with its statement state in your notes file.
4. Run `benchmark.coverage` on your own file and record the result in the notes file (the gate checks the combined set).

## Acceptance Criteria
- [ ] Every question has `expected_sql` that ran `SUCCEEDED`.
- [ ] 10a / 10b: at least 12 questions per view in the group, every measure and dimension tagged. 10c: enough cross-view questions for 25% of the combined set.

## Owned Paths
- 10a: `docs/tuning/benchmark/group_a.yml`, `docs/tuning/benchmark/group_a_notes.md`
- 10b: `docs/tuning/benchmark/group_b.yml`, `docs/tuning/benchmark/group_b_notes.md`
- 10c: `docs/tuning/benchmark/cross_view.yml`, `docs/tuning/benchmark/cross_view_notes.md`

## Dependencies
- Session 09: deployed agents. Sessions 05/06: registered metric views.
