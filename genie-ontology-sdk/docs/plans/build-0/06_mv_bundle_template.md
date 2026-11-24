# Session 06: Metric View Bundle Template (DAB 1)

## Scope
Create `templates/ontology-metric-views/`, the reusable Declarative Automation Bundle that owns metric view YAMLs and registers them with a forEach job. It must pass `bundle validate --strict --target dev` with no extra flags. Start from `examples/dab1_metric_views/`, but do not edit `examples/`.

## Context
* L100 "Architecture: Two DABs"; [L200-F](../../design/L200-F-registration-pipeline.md); diagram 04 (forEach flow); [research/metric-view-cicd-best-practices.md](../../research/metric-view-cicd-best-practices.md).
* Known example defects to fix (PROJECT_MEMORY finding 12):
  * undeclared `${var.dev_warehouse_id}` / `${var.*_workspace_host}`
  * `workspace.host` set from a variable (omit host; use the CLI profile)
  * missing smoke-test SQL
  * no schema resource
* Conventions:
  * reference the schema as `${resources.schemas.ontology_schema.name}` (never raw `${var.schema}` outside the schema resource)
  * `notebook_path` must match the extension on disk (use `.ipynb`, verify with a listing)
  * serverless notebook tasks; `sql_task` only with `warehouse_id`
  * the first cell of SDK notebooks installs the latest databricks-sdk and calls `dbutils.library.restartPython()`
* Library code: notebooks import `mv_yaml` / `manifest` from a vendored copy at `src/genie_ontology_sdk_vendored/`, which session 09's `scaffold.py` copies in. The template keeps only a `src/genie_ontology_sdk_vendored/README.md` explaining this. For `bundle validate`, the import is not needed.
* Variables: `catalog` (required), `source_catalog` (required), `source_schema` (required), `warehouse_id` (required), `schema_name` (default `ontology`), `consumer_group` (default `account users`). The dev target sets obvious placeholders (`catalog: main`, `source_catalog: samples`, `source_schema: tpch`, `warehouse_id: "<set-in-variable-overrides>"`) so validate passes. The README tells users to put real values in `.databricks/bundle/<target>/variable-overrides.json` (gitignored).
* Targets: `dev` (mode development, default) and `prd` (mode production, `root_path: /Workspace/.bundle/${bundle.name}/${bundle.target}`), with no hosts or user names.

## Tasks
1. `databricks.yml` + `resources/ontology_schema.yml`: schema resource `ontology_schema`, name `${var.schema_name}`, with grants USE_SCHEMA + SELECT to `${var.consumer_group}`.
2. `resources/register_metric_views.job.yml`: job `register_metric_views` with four tasks:
   * `generate_manifest`: notebook; sets task value `metric_view_list`
   * `register_each_mv`: for_each, concurrency 4, over `{{tasks.generate_manifest.values.metric_view_list}}` -> `register_single_mv` notebook with `yaml_path`, `mv_name`, the source/target params, and the target schema from the schema resource
   * `smoke_test`: notebook; `SELECT MEASURE(...)` per MV, LIMIT 1
   * `cardinality_test`: notebook; for each join, compare `COUNT(*)` of the fact grain with and without joins and fail on inflation
   * all four tasks serverless
3. Notebooks under `notebooks/` (`.ipynb`), each with widgets, no hardcoded names, and a final summary as task values / an exit JSON.
4. `metric_views/.gitkeep`, `tests/README.md`, `README.md` (usage, variables, overrides file, deploy + `bundle run register_metric_views`), and `.gitignore` (`.databricks/`).
5. `tests/test_template_mv_bundle.py` (repo-level tests folder): parse the YAML; check every `notebook_path` exists with its extension, there are no `${var.schema` references outside the schema resource, and there are no hosts or user names.

## Acceptance Criteria
- [ ] `databricks bundle validate --strict --target dev`, run from `templates/ontology-metric-views/`, exits 0. Use the runDatabricksCli tool with `workingDirectory`; the CLI is blocked in executeCode shells.
- [ ] pytest (from a `/tmp` copy) passes, including `tests/test_template_mv_bundle.py`.
- [ ] The job has the 4 tasks, and the forEach inner task gets the schema from `${resources.schemas.ontology_schema.name}`.
- [ ] No deploy in this session.

## Owned Paths / Assets
- `templates/ontology-metric-views/**`
- `tests/test_template_mv_bundle.py`

## Dependencies
- Session 02: `mv_yaml.substitute` / `render_ddl` and `manifest.build_manifest` semantics (the notebooks call them through the vendored copy).
