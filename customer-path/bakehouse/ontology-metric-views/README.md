# ontology-metric-views (DAB 1)

Declarative Automation Bundle template that owns a Genie Ontology project's metric view YAML files and registers them in Unity Catalog. `scaffold_project` copies it into `<project>/ontology-metric-views/`.

## What it deploys

| Resource | Key | What |
|---|---|---|
| Schema | `ontology_schema` | `${var.catalog}.${var.schema_name}`, grants `${var.schema_grants}` (`USE_SCHEMA` + `SELECT`). In `dev` (development mode) the name gets the per-user `dev_<user>_` prefix. |
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
| `schema_grants` | no | `dev`: the deploying developer; other targets: `account users` | List of `{principal, privileges}` granted on the ontology schema. A principal is a user name, an account-level group or a service principal application id (workspace-local groups such as `admins` cannot hold Unity Catalog grants). Override the whole list per target in `variable-overrides.json` |
| `warehouse_id` | no | `""` | Optional SQL warehouse. Nothing in the job uses it (every task runs on serverless); set it only for ad hoc SQL checks, and it is copied into `resolved_target.json` for the Genie Agent bundle |
| `schema_name` | no | `ontology` | Ontology schema name. `scaffold_project` replaces the default with `sdk_config.target_schema` |
| `sdk_volume_path` | yes | - | `/Volumes/<sdk_catalog>/<sdk_schema>/sdk_wheels` of the SDK bundle (set it in `variable-overrides.json`) |
| `sdk_version` | no | `0.1.0` | SDK version to install (rendered by the scaffold from the SDK) |
| `sdk_wheel_subpath` | no | `.internal` | Sub-folder of the volume where the SDK bundle publishes the wheel |
| `sdk_wheel` | no | composed from the three above | Full wheel path the job environment installs |

## SDK wheel

Every job task runs with `environment_key: sdk`; the job environment `sdk` installs `${var.sdk_wheel}` (the SDK wheel published by the SDK bundle, see the SDK's `docs/distribution/README.md`). For classic compute, use the commented `libraries: [{whl: ${var.sdk_wheel}}]` block in `resources/register_metric_views.job.yml` instead. The notebooks' `load_sdk()` prefers a vendored copy under `src/genie_ontology_modeled_knowledge_sdk_vendored/` (only present when the project was scaffolded with `vendor=True`), else imports the installed package.

## Targets

* `dev` (default): `mode: development`. It sets obvious placeholders (`catalog: main`, `source_catalog: samples`, `source_schema: tpch`). `schema_grants` defaults to the deploying developer (`${workspace.current_user.userName}`); add a group or a service principal in the overrides file.
* `prd`: `mode: production`, `root_path: /Workspace/.bundle/${bundle.name}/${bundle.target}`. No values are set; supply them with overrides or `--var`.

Neither target sets a workspace host: select the workspace with a CLI profile (`--profile` or `DATABRICKS_CONFIG_PROFILE`).

## Real values: variable-overrides.json

Put workspace-specific values in `.databricks/bundle/<target>/variable-overrides.json` (gitignored, never committed):

```json
{
  "catalog": "<your_catalog>",
  "source_catalog": "<source_catalog>",
  "source_schema": "<source_schema>",
  "warehouse_id": "<optional warehouse_id>",
  "schema_grants": [
    {"principal": "<you or an account-level group>", "privileges": ["USE_SCHEMA", "SELECT"]},
    {"principal": "<service principal application id>", "privileges": ["USE_SCHEMA", "SELECT"]}
  ]
}
```

`schema_grants` is optional (the target default applies when it is left out) and replaces the whole list when set; `warehouse_id` may be left out.

The CLI reads this file for the selected target; values there override the target defaults. `--var name=value` on the command line overrides both.

## Usage

From this folder:

```bash
databricks bundle validate --strict --target dev
databricks bundle deploy --target dev
databricks bundle run register_metric_views --target dev
```

Re-running is idempotent: `CREATE OR REPLACE VIEW` re-registers every view in the manifest. Views removed from `metric_views/` are not dropped; drop them yourself.

## Resolved target: resolved_target.json

The Genie Agent bundle needs the full schema name, which in `dev` carries the `dev_<user>_` prefix. Do not write it by hand: resolve it from this bundle's `bundle summary` (after deploy) with the SDK:

```bash
python -m genie_ontology_modeled_knowledge_sdk.targets resolve --bundle . --target dev --out ../docs/registration/resolved_target.json
```

It writes `{"catalog", "schema", "warehouse_id", "source": "bundle_summary", "resolved_at"}` (`warehouse_id` is `null` when unset). Pass `--var name=value` if a variable is not in the overrides file. The agents bundle renders from this file (`geniespace render ... --params resolved_target.json --check`, see its README). Each `register_single_mv` run also ends with `catalog` and `schema` in its notebook exit value, so the job run output shows the same target.

For production: `databricks bundle deploy --target prd` (with a `prd` overrides file or `--var`s), then `bundle run register_metric_views --target prd`.
