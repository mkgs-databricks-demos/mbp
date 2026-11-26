# SDK distribution: the SDK bundle

The SDK itself is deployed as a Declarative Automation Bundle at the SDK root (`databricks.yml`, `resources/`). It owns one Unity Catalog schema that holds everything the SDK publishes:

* the `sdk_wheels` volume (versioned SDK wheels, uploaded on deploy through `workspace.artifact_path`),
* the published `ontology-*` skills,
* build-only `scratch_*` pattern-check views.

Committed files never name a real catalog or schema; this document writes it as `<sdk_catalog>.<sdk_schema>`.

## Setup questions

| Variable | Question | Default |
|---|---|---|
| `sdk_catalog` | Which existing catalog holds the SDK schema? | none (required) |
| `sdk_schema` | Which schema? **Recommended: a new schema the bundle creates.** | `ontology_sdk` |
| `sdk_schema_grants`, `sdk_volume_grants` | Who reads the SDK assets (`USE_SCHEMA`, `READ_VOLUME`)? Lists of `{principal, privileges}`; a principal is a user name, an account-level group or a service principal application id | `dev`: the deploying developer; `prod` targets: `account users` |
| `warehouse_id` | Which SQL warehouse runs SDK setup checks and later SDK jobs? | none (required) |

Put the answers in the gitignored `.databricks/bundle/<target>/variable-overrides.json` at the SDK root:

```json
{"sdk_catalog": "<catalog>", "sdk_schema": "ontology_sdk", "warehouse_id": "<warehouse id>",
 "sdk_volume_grants": [{"principal": "<account-level group or SP application id>", "privileges": ["READ_VOLUME"]}]}
```

## Modes

| Mode | Targets | Resources | Files |
|---|---|---|---|
| New schema (recommended) | `dev` (development; schema name prefixed `dev_<user>_`), `prod` | schema `sdk` + volume `sdk_wheels` in it (`${resources.schemas.sdk.*}`, so the schema is created first). grants from `sdk_schema_grants` / `sdk_volume_grants` (developer in `dev`, `account users` in `prod`) | `resources/sdk.schema.yml`, `resources/sdk_wheels.volume.yml` |
| Existing schema | `prod_existing_schema` | volume `sdk_wheels` only, in `<sdk_catalog>.<sdk_schema>` (the schema must exist; it is not managed by the bundle) | `resources/sdk.existing_schema.yml` |

All three targets pass `databricks bundle validate --strict`.

## Deploy

```bash
databricks bundle validate --strict -t dev
databricks bundle deploy -t dev                    # or -t prod / -t prod_existing_schema
databricks bundle summary -t dev                   # resolved schema and volume names
```

Deploy the SDK bundle before any project bundle that installs the wheel from the volume.

## The wheel artifact

Checked with Databricks CLI **v1.27.0** (`databricks version`).

| Key | Value | Note |
|---|---|---|
| `artifacts.sdk_wheel.type` | `whl` | pure-Python wheel |
| `artifacts.sdk_wheel.path` | `.` | the SDK root (`pyproject.toml`) |
| `artifacts.sdk_wheel.build` | `python -m pip wheel --no-deps --no-build-isolation -w dist .` | `python -m build` was not used: the `build` module is not installed on the serverless compute where deploys ran |
| version | static, `[project] version` in `pyproject.toml` | no dynamic versioning |
| `workspace.artifact_path` | `${resources.volumes.sdk_wheels.volume_path}` on every target | the resource reference is accepted by `bundle validate`, so no per-target path is composed |
| `sync.exclude` | everything except the package, its metadata and `notebooks/sdk_smoke.ipynb` | `dist/` and `build/` are left to `.gitignore`; strict validate rejects exclude patterns that match no files |
| `resources/sdk_smoke.job.yml` | serverless notebook task, job environment `sdk` with `dependencies: [../dist/*.whl]`, `environment_key: sdk` | referencing the wheel is what makes the CLI upload it |

**`bundle validate` needs the volume.** The CLI checks that the `/Volumes/...` `artifact_path` exists during validate. Placeholder catalogs therefore cannot validate the SDK bundle: validate it with real values (the gitignored `variable-overrides.json`, or the CI repository variables `GOS_SDK_CATALOG`, `GOS_WAREHOUSE_ID`), after the first deploy has created the volume.

## The volume contract

Projects install `<sdk_volume_path>/<sdk_wheel_subpath>/genie_ontology_modeled_knowledge_sdk-<sdk_version>-py3-none-any.whl`:

* `sdk_volume_path`: `/Volumes/<sdk_catalog>/<sdk_schema>/sdk_wheels` (no default; set in the project's gitignored overrides).
* `sdk_wheel_subpath`: the sub-folder the CLI uploads artifacts to: `.internal` (template default). Session 23b confirmed with CLI v1.27.0 that the upload path is `<sdk_volume_path>/.internal/<wheel>`, stable across deploys, so no `releases/<version>/` copy is made. See [wheel_publish.md](wheel_publish.md).
* `sdk_version`: rendered by the scaffold from `pyproject.toml`.

## Grants

Consumers need `USE_CATALOG` on `<sdk_catalog>`, `USE_SCHEMA` on the SDK schema and `READ_VOLUME` on `sdk_wheels`. Every target grants `USE_SCHEMA` and `READ_VOLUME` from `sdk_schema_grants` / `sdk_volume_grants`: the deploying developer in `dev`, `account users` in `prod` and `prod_existing_schema`, overridable per target. Workspace-local groups (for example `admins`) cannot hold Unity Catalog grants. `USE_CATALOG` is a catalog owner step.
