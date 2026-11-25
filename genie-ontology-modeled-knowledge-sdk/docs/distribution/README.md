# SDK distribution: the SDK bundle

The SDK itself is deployed as a Declarative Automation Bundle at the SDK root (`databricks.yml`, `resources/`). It owns one Unity Catalog schema that holds everything the SDK publishes:

* the `sdk_wheels` volume (versioned SDK wheels; added by later sessions through `workspace.artifact_path`),
* the published `ontology-*` skills,
* build-only `scratch_*` pattern-check views.

Committed files never name a real catalog or schema; this document writes it as `<sdk_catalog>.<sdk_schema>`.

## Setup questions

| Variable | Question | Default |
|---|---|---|
| `sdk_catalog` | Which existing catalog holds the SDK schema? | none (required) |
| `sdk_schema` | Which schema? **Recommended: a new schema the bundle creates.** | `ontology_sdk` |
| `sdk_consumer_group` | Which group reads the SDK assets (`USE_SCHEMA`, `READ_VOLUME` in production)? | none (required) |
| `warehouse_id` | Which SQL warehouse runs SDK setup checks and later SDK jobs? | none (required) |

Put the answers in the gitignored `.databricks/bundle/<target>/variable-overrides.json` at the SDK root:

```json
{"sdk_catalog": "<catalog>", "sdk_schema": "ontology_sdk", "sdk_consumer_group": "<group>", "warehouse_id": "<warehouse id>"}
```

## Modes

| Mode | Targets | Resources | Files |
|---|---|---|---|
| New schema (recommended) | `dev` (development; schema name prefixed `dev_<user>_`), `prod` | schema `sdk` + volume `sdk_wheels` in it (`${resources.schemas.sdk.*}`, so the schema is created first). `prod` grants `USE_SCHEMA` / `READ_VOLUME` to `sdk_consumer_group`; `dev` declares no grants | `resources/sdk.schema.yml`, `resources/sdk_wheels.volume.yml` |
| Existing schema | `prod_existing_schema` | volume `sdk_wheels` only, in `<sdk_catalog>.<sdk_schema>` (the schema must exist; it is not managed by the bundle) | `resources/sdk.existing_schema.yml` |

All three targets pass `databricks bundle validate --strict`.

## Deploy

```bash
databricks bundle validate --strict -t dev
databricks bundle deploy -t dev                    # or -t prod / -t prod_existing_schema
databricks bundle summary -t dev                   # resolved schema and volume names
```

Deploy the SDK bundle before any project bundle that installs the wheel from the volume.
