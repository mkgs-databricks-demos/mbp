# ontology-metric-views (DAB 1)

Declarative Automation Bundle template that owns a Genie Ontology project's metric view YAML files and registers them in Unity Catalog. `scaffold_project` copies it into `<project>/ontology-metric-views/`.

## What it deploys

| Resource | Key | What |
|---|---|---|
| Schema | `ontology_schema` | `${var.catalog}.${var.schema_name}`, grants `USE_SCHEMA` + `SELECT` to `${var.consumer_group}`. In `dev` (development mode) the name gets the per-user `dev_<user>_` prefix. |
| Job | `register_metric_views` | Four serverless notebook tasks (below) |

```
generate_manifest --> register_each_mv (forEach, concurrency 4) --> smoke_test
                                       \-> register_single_mv     \-> cardinality_test
```

| Task | Notebook | Does |
|---|---|---|
| `generate_manifest` | `notebooks/generate_manifest.ipynb` | Validates every `metric_views/<domain>/**/*.yml` (MV001-MV007) and sets task value `metric_view_list` = `[{name, yaml_path, domain, subdomain}]` |
| `register_each_mv` -> `register_single_mv` | `notebooks/register_single_mv.ipynb` | Substitutes `${source_catalog}`, `${source_schema}`, `${target_catalog}`, `${target_schema}` and runs `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`. The target schema comes from `${resources.schemas.ontology_schema.name}` |
| `smoke_test` | `notebooks/smoke_test.ipynb` | `SELECT MEASURE(...) ... LIMIT 1` over every measure of every view |
| `cardinality_test` | `notebooks/cardinality_test.ipynb` | Per join, compares the fact grain `COUNT(*)` with and without the join; fails on inflation |

Every notebook takes all inputs as widgets (no hardcoded names) and ends with a JSON summary (task value `summary` and the notebook exit value).

## Layout

```
ontology-metric-views/
├── databricks.yml                     # variables + targets (no hosts, no user names)
├── resources/
│   ├── ontology_schema.yml
│   └── register_metric_views.job.yml
├── notebooks/                          # .ipynb, serverless
├── metric_views/<domain>/[<subdomain>/]<mv_name>.yml
├── src/genie_ontology_modeled_knowledge_sdk_vendored/    # filled by scaffold_project (see its README)
└── tests/README.md
```

Metric view YAML rules: file name = view name; `source:` and `joins[].source` use `${source_catalog}.${source_schema}.<table>` (never a literal catalog); never put `$$` in a YAML file, comments included. Validate locally with `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate metric_views`.

## Variables

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `catalog` | yes | - | Catalog for the ontology schema and the metric views (the environment discriminator) |
| `source_catalog` | yes | - | Catalog of the source tables |
| `source_schema` | yes | - | Schema of the source tables |
| `warehouse_id` | yes | - | SQL warehouse for ad hoc checks and the Genie Agent bundle (job tasks run on serverless) |
| `schema_name` | no | `ontology` | Ontology schema name |
| `consumer_group` | no | `account users` | Group granted `USE_SCHEMA` + `SELECT` |

## Targets

* `dev` (default): `mode: development`. It sets obvious placeholders (`catalog: main`, `source_catalog: samples`, `source_schema: tpch`, `warehouse_id: "<set-in-variable-overrides>"`) so `bundle validate` passes out of the box.
* `prd`: `mode: production`, `root_path: /Workspace/.bundle/${bundle.name}/${bundle.target}`. No values are set; supply them with overrides or `--var`.

Neither target sets a workspace host: select the workspace with a CLI profile (`--profile` or `DATABRICKS_CONFIG_PROFILE`).

## Real values: variable-overrides.json

Put workspace-specific values in `.databricks/bundle/<target>/variable-overrides.json` (gitignored, never committed):

```json
{
  "catalog": "<your_catalog>",
  "source_catalog": "<source_catalog>",
  "source_schema": "<source_schema>",
  "warehouse_id": "<warehouse_id>"
}
```

The CLI reads this file for the selected target; values there override the target defaults. `--var name=value` on the command line overrides both.

## Usage

From this folder:

```bash
databricks bundle validate --strict --target dev
databricks bundle deploy --target dev
databricks bundle run register_metric_views --target dev
```

Re-running is idempotent: `CREATE OR REPLACE VIEW` re-registers every view in the manifest. Views removed from `metric_views/` are not dropped; drop them yourself.

For production: `databricks bundle deploy --target prd` (with a `prd` overrides file or `--var`s), then `bundle run register_metric_views --target prd`.
