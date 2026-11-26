# Skills publish results (build-1 session 27, wave 1-3)

Date: 2026-11-26. Target `dev`; skills schema = the SDK schema, written here as `<skills_catalog>.<skills_schema>` (resolved from `databricks bundle summary -t dev`). Publisher: `skills_publish.publish` (`databricks-sdk` 0.171.0), the same module `notebooks/publish_skills.ipynb` calls. Two runs in build run of session 27; no grants, no schema creation (`check_schema`: exists).

## Runs

| Skill id | Files | Run 1 changes | Run 2 changes |
|---|---|---|---|
| `<skills_catalog>.<skills_schema>.ontology_domain_research` | 1 | 1 | 0 |
| `<skills_catalog>.<skills_schema>.ontology_context_extraction` | 1 | 1 | 0 |
| `<skills_catalog>.<skills_schema>.ontology_deep_eda` | 1 | 1 | 0 |
| `<skills_catalog>.<skills_schema>.ontology_mv_synthesis` | 2 | 2 | 0 |
| `<skills_catalog>.<skills_schema>.ontology_agent_curation` | 1 | 1 | 0 |
| `<skills_catalog>.<skills_schema>.ontology_tuning` | 3 | 3 | 0 |
| **Total** | **9** | **9** (6 created, 6 finalized) | **0** (no uploads, no finalize) |

## Schema listing after run 2

`ai_gateway.list_skills(parent="schemas/<skills_catalog>.<skills_schema>")` returned 6 ids:

* `<skills_catalog>.<skills_schema>.ontology_agent_curation`
* `<skills_catalog>.<skills_schema>.ontology_context_extraction`
* `<skills_catalog>.<skills_schema>.ontology_deep_eda`
* `<skills_catalog>.<skills_schema>.ontology_domain_research`
* `<skills_catalog>.<skills_schema>.ontology_mv_synthesis`
* `<skills_catalog>.<skills_schema>.ontology_tuning`

Each `get_skill` returned `bundle_name` equal to the folder name, a `finalize_time`, and a published file count equal to the local count above. Before run 1 the listing returned 0 skills (P1-3: skills preview on, no feature-disabled error).
