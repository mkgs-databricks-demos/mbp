# L200-E — Metric View Synthesizer

Matthew Giglia | Databricks Field Engineering
Version: 0.1-draft | Date: 2026-11-24

**Parent:** [L100 — Genie Ontology Modeled Knowledge SDK](L100-genie-ontology-modeled-knowledge-sdk.md)
**Wave:** Wave 4

## Scope

This component synthesizes all context into metric view YAML candidates:

### Synthesis Inputs

| Source | Contributes |
|---|---|
| Wave 1 (Research) | Synonyms, display names, industry-standard measures |
| Wave 2 (Context) | Business rules, filters, calculated field logic |
| Wave 3 (EDA) | Join keys, cardinality, grain, data types, materialization signals |

### YAML Generation Rules

1. **Parameterized source** — `source: ${source_catalog}.${source_schema}.table_name`
2. **Explicit fields** — no wildcards in certified views
3. **Verified joins** — `rely: at_most_one_match: true` only where Wave 3 confirmed cardinality
4. **Semantic metadata** — comments from context, synonyms from research, formats from EDA
5. **Materialization blocks** — auto-generated for MVs meeting thresholds:
   - `refresh_policy: auto`
   - `cluster_by: { auto: true }`
   - Dimensions = categorical grouping columns (not continuous/unique)

### Manifest Generation

`manifest.json` — array of objects for the forEach task:

```json
[
  {
    "name": "mv_sales_revenue",
    "yaml_path": "metric_views/sales/mv_sales_revenue.yml",
    "domain": "sales",
    "subdomain": "revenue"
  }
]
```

### Output

- `metric_views/<domain>/*.yml` — one YAML per metric view
- `manifest.json` — forEach task input

## Dependencies

- L100 system-level patterns (governance, observability, security, error handling)
- Previous waves' outputs (see L100 wave descriptions)

## Open Questions

_To be resolved during L200 detailed design._

## Testing Strategy

_To be defined per component._

## Deployment

Deployed as part of the Genie Build Waves pipeline. See L100 for the overall orchestration model.
