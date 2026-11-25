# 2026-11-24 — Wave 0-2 / Session 06: Metric View Bundle Template (DAB 1)

* Build run: job `419885870201924`, run `701596191246320`, task `w0-2_session`, continuation 0
* Mode: `edit` (`allow_execute: true`), workflow `hybrid`, branch `mg-genie-ontology-modeled-knowledge-sdk` (Git folder `mbp`, verified read-only via the Repos API and `git rev-parse`)
* Status: **pass**. No deploy (plan rule).

## Changes

| File | What |
|---|---|
| `templates/ontology-metric-views/databricks.yml` | Bundle `ontology-metric-views`; variables `catalog`, `source_catalog`, `source_schema`, `warehouse_id` (required), `schema_name` (`ontology`), `consumer_group` (`account users`); targets `dev` (development, default, placeholders `main`/`samples`/`tpch`/`"<set-in-variable-overrides>"`) and `prd` (production, `root_path: /Workspace/.bundle/${bundle.name}/${bundle.target}`). No hosts, no user names |
| `templates/ontology-metric-views/resources/ontology_schema.yml` | Schema `ontology_schema` = `${var.catalog}.${var.schema_name}`, grants `USE_SCHEMA` + `SELECT` to `${var.consumer_group}` |
| `templates/ontology-metric-views/resources/register_metric_views.job.yml` | Job `register_metric_views`: `generate_manifest` -> `register_each_mv` (forEach, concurrency 4, inner `register_single_mv`) -> `smoke_test` + `cardinality_test`. All serverless notebook tasks; target catalog/schema from `${resources.schemas.ontology_schema.catalog_name/name}`; `bundle_root: ${workspace.file_path}` |
| `templates/ontology-metric-views/notebooks/generate_manifest.ipynb` | Validates MV YAML (errors fail), `manifest.build_manifest` + `validate_manifest_json`, sets task value `metric_view_list` |
| `templates/ontology-metric-views/notebooks/register_single_mv.ipynb` | `mv_yaml.render_ddl` (catches `ValueError`), `spark.sql`, `DESCRIBE TABLE` verify |
| `templates/ontology-metric-views/notebooks/smoke_test.ipynb` | `SELECT MEASURE(...) ... LIMIT 1` over all measures of each MV (first dimension if none); fails on any error |
| `templates/ontology-metric-views/notebooks/cardinality_test.ipynb` | Per MV with joins: fact-grain `COUNT(*)` vs. cumulative `LEFT JOIN`s (parents before nested); fails and names the first inflating join |
| `templates/ontology-metric-views/{README.md, .gitignore, metric_views/.gitkeep, tests/README.md, src/genie_ontology_sdk_vendored/README.md}` | Usage, variables, overrides file, deploy + `bundle run register_metric_views`; `.databricks/` ignored; vendoring contract |
| `tests/test_template_mv_bundle.py` | 21 static tests: layout, variables/targets, schema resource, 4 tasks + forEach params, serverless, every `notebook_path` exists with `.ipynb`, no `${var.schema` outside the schema resource, no hosts/user names/emails/`/Users/` paths, notebook structure (SDK install first cell, widgets default `""`, exit JSON), and the vendored loader against a copy of `src/` |

## Decisions

* **Vendored import.** `mv_yaml.py` / `manifest.py` import each other as `genie_ontology_sdk.*`, and session 09 vendors them verbatim ("identical to `src/`"). Each notebook's `load_sdk(bundle_root)` registers `src/genie_ontology_sdk_vendored/` as the `genie_ontology_sdk` package before importing, and falls back to an installed package. No `__init__.py` is needed in the vendored folder. Covered by `test_vendored_loader_imports_sdk`.
* **`warehouse_id`** is declared (required, per plan) but no task uses it: all tasks are serverless notebooks. It is there for ad hoc checks and for parity with the Genie Agent bundle.
* **Job and file names** follow the plan (`resources/ontology_schema.yml`, `resources/register_metric_views.job.yml`, `include: resources/*.yml`) rather than the owner's `resources/<type>/` layout preference, because the manifest/plan names them.
* **No `${...}` in variable descriptions**: bundle interpolation would try to resolve `${source_catalog}`; descriptions say "the source_catalog token" instead.
* Notebooks are `.ipynb` files (nbformat 4); `bundle validate` resolves them as notebooks (paths shown without extension in the resolved config).
* Widgets default to `""` and fail fast; no catalog/schema literals in notebook code (tested).

## Checks

| Check | Result |
|---|---|
| `databricks bundle validate --strict --target dev` from `templates/ontology-metric-views/` (runDatabricksCli, `workingDirectory`) | pass — "Validation OK!"; resolved schema `main.dev_<user>_ontology`, 4 tasks, forEach inner params reference `${resources.schemas.ontology_schema.*}` |
| Gate pytest from `/tmp/gos-gate` copy (`pip install -q pyyaml jsonschema pytest && python -m pytest -q`) | pass — 255 passed, 1 skipped (the skip is not in this session's tests) |
| `tests/test_template_mv_bundle.py` alone | pass — 21 passed |
| Negative check: in a scratch copy, `.ipynb` -> `.py` on one notebook_path and `${var.schema_name}` in the job | 3 tests fail as expected |
| Dry run of `generate_manifest` + `cardinality_test` cells (fake dbutils, real Spark, read-only on `samples.tpch`) with the `mv_tpch_order_lines` fixture | pass — manifest of 1, joins pass (fact rows 29,999,795 unchanged) |
| Same with a fan-out MV (`orders` joined to `lineitem`) | fails as intended: `inflated`, join `li`, 7,500,000 -> 29,999,795 |
| `register_single_mv` render cell on the fixture | DDL renders with no `${`, `verified_cardinality:` key stripped (no registration run) |
| No deploy | confirmed (validate only) |

`smoke_test` and the `spark.sql(ddl)` registration step were not executed (they need registered views; deploy/run is session 12).

## Notes for later sessions

* **09 (scaffold):** copy `mv_yaml.py`, `manifest.py` (and `geniespace.py`) verbatim into `ontology-metric-views/src/genie_ontology_sdk_vendored/`; the notebooks need nothing else. Keep the template's `src/genie_ontology_sdk_vendored/README.md`.
* **12 (registration):** the dev overrides file needs `catalog` and `warehouse_id`; `source_catalog`/`source_schema` default to `samples`/`tpch` in `dev`. Run `bundle run register_metric_views --target dev`. The registered schema is dev-prefixed (`dev_<user>_ontology` unless `schema_name` is overridden).
* **11 (synthesis):** `cardinality_test` uses join `name`s as SQL aliases, so join names must be unique across nesting levels (the notebook reports a reused name as an error).

## Requests

None.
