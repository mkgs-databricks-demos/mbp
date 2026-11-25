# Session 05: Metric View YAML Synthesis

## Scope
Turn the discovery outputs for `{{domain_name}}` into parameterized metric view YAML files under `ontology-metric-views/metric_views/`, with materialization blocks where the EDA signals call for them, and write `manifest.json`. Writing files only: registration is session 06.

## Context
* Skill: load `skills/ontology-mv-synthesis/SKILL.md` (and the platform `metric-views` skill it points to).
* Inputs: `docs/research/**`, `docs/semantics/**`, `docs/context/**`, `docs/data_profiles/**`, `sdk_config.json`.
* SDK functions: `genie_ontology_modeled_knowledge_sdk.mv_yaml` `load_mv`, `validate_mv`, CLI `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate <dir>`; `genie_ontology_modeled_knowledge_sdk.manifest` `build_manifest(metric_views_dir)`, `write_manifest(...)`, `validate_manifest_json(list)`. In the project, use the vendored copy (`PYTHONPATH=ontology-metric-views/src`, module `genie_ontology_modeled_knowledge_sdk_vendored.mv_yaml`).
* Parameters: `${source_catalog}`, `${source_schema}`, `${target_catalog}`, `${target_schema}`. A literal catalog in `source:` is rule MV004.
* `manifest.json` entries: `{name, yaml_path, domain, subdomain}`, `yaml_path` relative to the metric-views bundle root, sorted by `name`.

## Tasks
1. Plan one metric view per business process and grain; map each KPI to one view.
2. Write `ontology-metric-views/metric_views/<domain>/mv_<domain>_<process>.yml` per the skill, with `rely` cardinalities from `data_model_summary.md`.
3. Add `materialization:` blocks for views that meet the skill's thresholds.
4. Run the validator CLI and fix every finding. Write `manifest.json` with `build_manifest` + `write_manifest`.
5. Optional read-only check: `EXPLAIN` the rendered source SQL of each view (`mv_yaml.render_ddl` with the dev parameters) to catch column typos.

## Acceptance Criteria
- [ ] The validator exits 0 on `ontology-metric-views/metric_views`.
- [ ] `manifest.json` lists every YAML and passes `validate_manifest_json`.
- [ ] No literal catalogs, schemas or workspace values in any YAML.

## Owned Paths
- `ontology-metric-views/metric_views/**`

## Dependencies
- Sessions 02, 03, 04: research, context and profile docs.
