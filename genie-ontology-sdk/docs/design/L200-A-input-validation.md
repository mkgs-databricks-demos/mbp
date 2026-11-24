# L200-A — Input Validation & Repo Scaffolding

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology SDK](L100-genie-ontology-sdk.md)
**Wave:** Wave 0

## Scope

This component handles the SDK's initialization phase:

1. **Input validation** — verify all provided catalogs, schemas, and tables exist in Unity Catalog; verify volume directories are readable; verify repo path is writable
2. **Feature branch creation** — create `ontology-sdk/<domain>-<timestamp>` branch in the target repo
3. **Folder scaffolding** — create the standard directory structure following discovery-and-design workflow conventions
4. **Configuration capture** — write a `sdk_config.json` with all input parameters for downstream waves

### Input Contract Validation Rules

| Input | Validation |
|---|---|
| `source_catalogs` | Each catalog exists and user has `USE CATALOG` |
| `source_schemas` | Each schema exists and user has `USE SCHEMA` |
| `source_tables` | Each table exists and user has `SELECT` |
| `repo_path` | Path exists, is a Git folder, user can write |
| `target_catalog` | Catalog exists and user has `CREATE SCHEMA` (or schema exists with `CREATE TABLE`) |
| `supplemental_volume_dirs` | Each directory exists and is readable |

### Folder Structure Generated

```
<repo>/
├── ontology-metric-views/
│   ├── metric_views/<domain>/
│   ├── sql/
│   ├── notebooks/
│   └── tests/
├── ontology-genie-agents/
│   ├── agents/
│   └── notebooks/
└── docs/
    ├── research/
    ├── context/
    ├── semantics/
    ├── data_profiles/
    └── tuning/
```

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
