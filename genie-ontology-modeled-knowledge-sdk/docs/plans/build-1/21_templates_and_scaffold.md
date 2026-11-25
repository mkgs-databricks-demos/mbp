# Session 21: Templates & Scaffold — Required consumer_group, Resolved Target (R4.3, R4.4)

## Scope
Remove the broad default grant, make the resolved metric-view target a single source of truth, and stop the scaffold from leaving placeholder files. `bundle validate` only, no deploy.

## Context
* [REQUESTS R4](REQUESTS.md#r4-fix-the-library-and-template-defects) items 3 and 4; review gap G9.
* Build-0 observations 27 (placeholder agent left behind), 28 (two hand-written overrides drifted and blocked wave 0-8: the template's `schema_name` default is `ontology`, the overrides assumed the project name), and the session 06 note (`warehouse_id` required but unused).
* Development-mode schema names are `dev_<short_name>_<schema_name>`; a consumer bundle cannot reference another bundle's resources, so resolve from `databricks bundle summary -o json` of the metric-views bundle.

## Tasks
1. Both templates: `consumer_group` has no default; README and overrides examples say the owner must name a group. `bundle validate --strict` without it must fail with a message naming `consumer_group` (gate check `consumer_group_required`).
2. `warehouse_id` in the metric-views template: optional (empty default), used only by an ad hoc check if set; document it.
3. New `targets.py`: `resolve_target(bundle_dir, target="dev") -> dict` runs `databricks bundle summary -o json` (subprocess, injectable runner for tests) and returns `{catalog, schema, warehouse_id, source: "bundle_summary", resolved_at}`; `write_resolved_target(path, data)`; CLI `python -m genie_ontology_modeled_knowledge_sdk.targets resolve --bundle <dir> --target dev --out <path>`.
4. Registration notebook in the metric-views template: `dbutils.notebook.exit(json.dumps({"catalog": ..., "schema": ...}))` so the run output also carries the resolved target.
5. Agents template README: render with `geniespace render --params <resolved_target.json> --check` (session 19's flags).
6. `scaffold.py`: render `schema_name` from `sdk_config.target_schema`; do not copy the placeholder `ontology_agent.geniespace.json` (curation writes real agents); keep the no-overwrite rule.
7. Tests: templates (no default group, optional warehouse), scaffold (schema_name rendered, no placeholder), targets (fake summary JSON for dev-prefixed and non-dev targets).

## Acceptance Criteria
- [ ] Gate checks `pytest`, `lint`, `consumer_group_required` pass; `validate_bundles` for the metric-views template passes with scratch overrides that include `consumer_group`.
- [ ] `targets resolve` on a fake summary gives the dev-prefixed schema.

## Owned Paths
- `templates/ontology-metric-views/**`, `templates/ontology-genie-agents/**`
- `src/genie_ontology_modeled_knowledge_sdk/scaffold.py`, `src/genie_ontology_modeled_knowledge_sdk/targets.py`
- `tests/test_template_mv_bundle.py`, `tests/test_template_agent_bundle.py`, `tests/test_scaffold.py`, `tests/test_targets.py`

## Dependencies
- Session 18. Session 19 consumes the `resolved_target.json` format; session 23 builds on these templates.
